#!/usr/bin/env python3
"""
Script para atualizar metadados de arquivos G-code existentes
"""

import os
import sys
import sqlite3
import re

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

DB_NAME = 'croma_printer.db'
GCODE_FOLDER = 'gcode_files'

def parse_gcode_metadata(gcode_path):
    """Extrai metadados completos do G-code"""
    metadata = {
        'print_time': None,
        'filament_used': None,
        'filament_type': None,
        'nozzle_temp': None,
        'bed_temp': None,
        'layer_height': None,
        'infill': None
    }
    
    try:
        with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Ler primeiras 500 linhas (onde geralmente estão os comentários com metadados)
            for i, line in enumerate(f):
                if i > 500:
                    break
                
                line = line.strip()
                
                # Para na primeira linha de código (não comentário)
                if line and not line.startswith(';'):
                    continue
                
                # Remove o ponto e vírgula
                if line.startswith(';'):
                    line = line[1:].strip()
                
                # Tempo de impressão
                if 'estimated printing time' in line.lower() or 'TIME:' in line:
                    # Formatos: "; estimated printing time (normal mode) = 2h 30m 15s" ou ";TIME:7200"
                    time_match = re.search(r'=\s*(.+)', line)
                    if time_match:
                        metadata['print_time'] = time_match.group(1).strip()
                    else:
                        time_match = re.search(r'TIME:\s*(\d+)', line)
                        if time_match:
                            # Converter segundos para formato legível
                            total_seconds = int(time_match.group(1))
                            hours = total_seconds // 3600
                            minutes = (total_seconds % 3600) // 60
                            seconds = total_seconds % 60
                            metadata['print_time'] = f"{hours}h {minutes}m {seconds}s"
                
                # Filamento usado (gramas ou metros)
                if 'filament used' in line.lower() or 'material used' in line.lower() or 'Filament used' in line:
                    # Formato: "; filament used [g] = 25.4" ou "; filament used [mm] = 8450"
                    weight_match = re.search(r'\[g\]\s*=\s*([\d.]+)', line)
                    length_match = re.search(r'\[mm\]\s*=\s*([\d.]+)', line)
                    simple_match = re.search(r':\s*([\d.]+)\s*g', line)
                    
                    if weight_match:
                        metadata['filament_used'] = float(weight_match.group(1))
                    elif simple_match:
                        metadata['filament_used'] = float(simple_match.group(1))
                    elif length_match:
                        # Converte mm para metros e estima peso (1.75mm PLA ≈ 2.8mg/mm)
                        length_mm = float(length_match.group(1))
                        metadata['filament_used'] = round((length_mm * 0.0028), 2)
                
                # Tipo de filamento
                if 'filament_type' in line.lower() or 'filament type' in line:
                    # Formato: "; filament_type = PLA"
                    type_match = re.search(r'=\s*(.+)', line)
                    if type_match:
                        filament_value = type_match.group(1).strip()
                        # Remover aspas se existirem
                        metadata['filament_type'] = filament_value.strip('"\'')
                
                # Temperatura do bico
                if ('nozzle_temperature' in line.lower() or 'first_layer_temperature' in line.lower() 
                    or 'nozzle temperature' in line.lower()):
                    temp_match = re.search(r'=\s*([\d]+)', line)
                    if temp_match and not metadata['nozzle_temp']:
                        metadata['nozzle_temp'] = int(temp_match.group(1))
                
                # Temperatura da mesa
                if ('bed_temperature' in line.lower() or 'first_layer_bed_temperature' in line.lower()
                    or 'bed temperature' in line.lower()):
                    temp_match = re.search(r'=\s*([\d]+)', line)
                    if temp_match and not metadata['bed_temp']:
                        metadata['bed_temp'] = int(temp_match.group(1))
                
                # Altura da camada
                if 'layer_height' in line.lower() or 'layer height' in line:
                    height_match = re.search(r'=\s*([\d.]+)', line)
                    if height_match:
                        metadata['layer_height'] = float(height_match.group(1))
                
                # Preenchimento (infill)
                if 'fill_density' in line.lower() or 'infill' in line.lower() or 'sparse infill density' in line.lower():
                    infill_match = re.search(r'=\s*([\d.]+)', line)
                    if infill_match:
                        # Pode vir como decimal (0.20) ou percentual (20)
                        value = float(infill_match.group(1))
                        metadata['infill'] = int(value * 100) if value < 1 else int(value)
    
    except Exception as e:
        print(f"Erro ao parsear metadados do G-code: {e}")
    
    return metadata

def update_all_files():
    """Atualiza metadados de todos os arquivos G-code existentes"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Buscar todos os arquivos
    cursor.execute('SELECT id, filename FROM gcode_files')
    files = cursor.fetchall()
    
    print(f"Encontrados {len(files)} arquivos para processar...")
    
    updated_count = 0
    error_count = 0
    
    for file_id, filename in files:
        filepath = os.path.join(GCODE_FOLDER, filename)
        
        if not os.path.exists(filepath):
            print(f"❌ Arquivo não encontrado: {filename}")
            error_count += 1
            continue
        
        print(f"📝 Processando: {filename}")
        
        # Extrair metadados
        metadata = parse_gcode_metadata(filepath)
        
        # Atualizar banco de dados
        cursor.execute('''
            UPDATE gcode_files 
            SET print_time = ?, filament_used = ?, filament_type = ?, 
                nozzle_temp = ?, bed_temp = ?, layer_height = ?, infill = ?
            WHERE id = ?
        ''', (metadata['print_time'], metadata['filament_used'], metadata['filament_type'],
              metadata['nozzle_temp'], metadata['bed_temp'], metadata['layer_height'], 
              metadata['infill'], file_id))
        
        # Mostrar informações extraídas
        info_parts = []
        if metadata['print_time']:
            info_parts.append(f"⏱️ {metadata['print_time']}")
        if metadata['filament_used']:
            info_parts.append(f"🧵 {metadata['filament_used']}g")
        if metadata['filament_type']:
            info_parts.append(f"({metadata['filament_type']})")
        
        if info_parts:
            print(f"   {' '.join(info_parts)}")
        else:
            print(f"   ℹ️ Nenhum metadado encontrado")
        
        updated_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Concluído!")
    print(f"   Atualizados: {updated_count}")
    print(f"   Erros: {error_count}")

if __name__ == '__main__':
    print("=" * 60)
    print("Atualizador de Metadados G-Code - Croma")
    print("=" * 60)
    print()
    
    update_all_files()

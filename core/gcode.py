"""G-code file utilities: validation, slicing, thumbnail extraction, metadata parsing."""

import os
import re
import base64
import subprocess
import shutil
import shlex
import sys
import time
from typing import Optional

from core.config import (
    ALLOWED_EXTENSIONS, ALLOWED_3D_EXTENSIONS, ORCA_SLICER_PATH,
    ORCA_DATADIR, SLICER_TIMEOUT_SEC, app,
)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_3d_file(filename):
    """Permite .stl e .obj para o fatiador integrado."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_3D_EXTENSIONS


def _log_slicer(msg: str, *args) -> None:
    """Log do fatiador (para debug); pode trocar por logging depois."""
    print(f"[slicer] {msg}", *args)

def run_orca_slice(stl_path: str, output_dir: str, layer_height: Optional[float] = None,
                   infill: Optional[int] = None) -> str:
    """
    Chama OrcaSlicer via CLI para fatiar o modelo.
    Retorna o caminho do arquivo .gcode gerado.
    Levanta RuntimeError em caso de falha.
    """
    _log_slicer("run_orca_slice: stl_path=%r output_dir=%r", stl_path, output_dir)
    def _orca_valid(p):
        if not p:
            return False
        if os.path.isabs(p):
            return os.path.isfile(p)
        return bool(shutil.which(p))

    def _resolve_orca_path(p):
        """Se for um .app no macOS, resolve para o binário em Contents/MacOS."""
        if not p or sys.platform != 'darwin':
            return p
        p = p.strip()
        if p.endswith('.app') and os.path.isdir(p):
            app_name = os.path.basename(p)[:-4]
            binary = os.path.join(p, 'Contents', 'MacOS', app_name)
            if os.path.isfile(binary):
                return binary
        return p

    orca_cfg = _resolve_orca_path(ORCA_SLICER_PATH)
    orca_bin = orca_cfg if _orca_valid(orca_cfg) else None
    if not orca_bin and sys.platform == 'win32':
        for base in [os.environ.get('ProgramFiles', 'C:\\Program Files'), os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')]:
            for name in ['OrcaSlicer\\OrcaSlicer.exe', 'OrcaSlicer\\orca-slicer.exe']:
                candidate = os.path.join(base, name)
                if os.path.isfile(candidate):
                    orca_bin = candidate
                    break
            if orca_bin:
                break
    if not orca_bin and sys.platform == 'darwin':
        default_macos = '/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer'
        if os.path.isfile(default_macos):
            orca_bin = default_macos
    if not orca_bin:
        for candidate in ['orca-slicer', 'OrcaSlicer', '/usr/bin/orca-slicer']:
            if shutil.which(candidate):
                orca_bin = candidate
                break
        if not orca_bin:
            _log_slicer("OrcaSlicer não encontrado no PATH")
            raise RuntimeError(
                'OrcaSlicer não encontrado. Configure ORCA_SLICER_PATH ou instale o OrcaSlicer.'
            )
    _log_slicer("Orca bin: %s", orca_bin)

    stl_path_abs = os.path.abspath(stl_path)
    output_dir_abs = os.path.abspath(output_dir)
    _log_slicer("stl_path_abs=%s output_dir_abs=%s", stl_path_abs, output_dir_abs)
    if not os.path.isfile(stl_path_abs):
        _log_slicer("Arquivo STL não existe: %s", stl_path_abs)
        raise RuntimeError(f'Arquivo não encontrado: {stl_path_abs}')
    _log_slicer("Tamanho do STL: %s bytes", os.path.getsize(stl_path_abs))

    cmd = [
        orca_bin,
        '--slice', '0',
        '--outputdir', output_dir_abs,
        '--allow-newer-file',
        '--no-check', '1',
        stl_path_abs,
    ]
    if ORCA_DATADIR and os.path.isdir(ORCA_DATADIR):
        settings_files = []
        for name in ['printer.json', 'process.json', 'print.json']:
            p = os.path.join(ORCA_DATADIR, name)
            if os.path.isfile(p):
                settings_files.append(p)
        if settings_files:
            cmd.extend(['--load-settings', ';'.join(settings_files)])
        filaments_dir = os.path.join(ORCA_DATADIR, 'filament')
        if os.path.isdir(filaments_dir):
            for f in os.listdir(filaments_dir):
                if f.endswith('.json'):
                    cmd.extend(['--load-filaments', os.path.join(filaments_dir, f)])
                    break
    _log_slicer("Comando Orca: %s", cmd)

    env = os.environ.copy()
    if ORCA_DATADIR:
        env['ORCA_SLICER_DATA_DIR'] = ORCA_DATADIR

    log_path = os.path.join(output_dir_abs, '_orca_log.txt')
    cwd = os.path.dirname(os.path.abspath(__file__)) or '.'

    if sys.platform == 'win32':
        _log_slicer("subprocess.run Orca (Windows) cwd=%s timeout=%s", cwd, SLICER_TIMEOUT_SEC)
        create_no_window = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        try:
            with open(log_path, 'w', encoding='utf-8', errors='replace') as log_file:
                result = subprocess.run(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    timeout=SLICER_TIMEOUT_SEC,
                    cwd=cwd,
                    env=env,
                    creationflags=create_no_window
                )
        except subprocess.TimeoutExpired:
            _log_slicer("Orca expirou (timeout %s s)", SLICER_TIMEOUT_SEC)
            raise RuntimeError(f'Fatiamento expirou após {SLICER_TIMEOUT_SEC} segundos.')
    else:
        cmd_shell = ' '.join(shlex.quote(a) for a in cmd) + ' > ' + shlex.quote(log_path) + ' 2>&1'
        _log_slicer("subprocess.run (shell) cwd=%s timeout=%s", cwd, SLICER_TIMEOUT_SEC)
        try:
            result = subprocess.run(
                ['sh', '-c', cmd_shell],
                stdin=subprocess.DEVNULL,
                timeout=SLICER_TIMEOUT_SEC,
                cwd=cwd,
                env=env
            )
        except subprocess.TimeoutExpired:
            _log_slicer("Orca expirou (timeout %s s)", SLICER_TIMEOUT_SEC)
            raise RuntimeError(f'Fatiamento expirou após {SLICER_TIMEOUT_SEC} segundos.')

    _log_slicer("Orca returncode=%s", result.returncode)
    if result.returncode != 0:
        orca_err = ''
        if os.path.isfile(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                    orca_err = f.read().strip()
                    _log_slicer("Orca stderr/stdout (últimas 1500 chars): %s", orca_err[-1500:] if len(orca_err) > 1500 else orca_err)
            except OSError as e:
                _log_slicer("Não foi possível ler log: %s", e)
        _log_slicer("Orca falhou com código %s", result.returncode)
        err_snippet = (orca_err[-800:] if len(orca_err) > 800 else orca_err) if orca_err else ''
        hint = ''
        if sys.platform == 'darwin' and result.returncode == 253 and 'No such file: 1' in orca_err:
            hint = ' No macOS o OrcaSlicer em linha de comando pode apresentar este erro; no Windows o fatiador integrado funciona normalmente. Enquanto isso, fatie o modelo no Orca pelo app e envie o arquivo .gcode em Arquivos.'
        raise RuntimeError(
            f'OrcaSlicer saiu com código {result.returncode}. '
            f'Verifique se o modelo está válido e se o Orca está instalado corretamente. '
            f'(arquivo: {stl_path_abs})'
            + (f' Saída: {err_snippet}' if err_snippet else '')
            + hint
        )

    base = os.path.splitext(os.path.basename(stl_path))[0]
    gcode_name = base + '.gcode'
    gcode_path = os.path.join(output_dir_abs, gcode_name)
    if not os.path.isfile(gcode_path):
        listing = os.listdir(output_dir_abs)
        _log_slicer("G-code %s não encontrado; conteúdo da pasta: %s", gcode_path, listing)
        for f in listing:
            if f.endswith('.gcode'):
                gcode_path = os.path.join(output_dir_abs, f)
                break
        else:
            _log_slicer("Nenhum .gcode na pasta de saída")
            raise RuntimeError('OrcaSlicer não gerou arquivo .gcode na pasta de saída.')
    _log_slicer("G-code gerado: %s (%s bytes)", gcode_path, os.path.getsize(gcode_path))
    return gcode_path


def get_gcode_info(filepath):
    try:
        file_size = os.path.getsize(filepath)
        return {'size': file_size}
    except:
        return {'size': 0}


def extract_thumbnail(gcode_path, file_id):
    try:
        with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines(500000)
        
        in_thumbnail = False
        thumbnail_data = []
        thumbnail_width = 0
        thumbnail_height = 0
        max_thumbnail_size = 0
        best_thumbnail_data = []
        
        for line in lines:
            line = line.strip()
            
            if 'thumbnail begin' in line or 'thumbnail_PNG begin' in line:
                match = re.search(r'(\d+)x(\d+)', line)
                if match:
                    width = int(match.group(1))
                    height = int(match.group(2))
                    current_size = width * height
                    
                    if current_size > max_thumbnail_size:
                        max_thumbnail_size = current_size
                        thumbnail_width = width
                        thumbnail_height = height
                        thumbnail_data = []
                        in_thumbnail = True
                    else:
                        in_thumbnail = False
            
            elif 'thumbnail end' in line or 'thumbnail_PNG end' in line:
                if in_thumbnail and thumbnail_data:
                    best_thumbnail_data = thumbnail_data[:]
                in_thumbnail = False
            
            elif in_thumbnail and line.startswith(';'):
                data = line[1:].strip()
                if data:
                    thumbnail_data.append(data)
        
        if best_thumbnail_data:
            try:
                base64_string = ''.join(best_thumbnail_data)
                image_data = base64.b64decode(base64_string)
                thumbnail_filename = f"thumb_{file_id}.png"
                thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], thumbnail_filename)
                
                with open(thumbnail_path, 'wb') as img_file:
                    img_file.write(image_data)
                
                return f"thumbnails/{thumbnail_filename}"
            except Exception as e:
                print(f"Erro ao decodificar thumbnail: {e}")
                return None
        
        return None
    except Exception as e:
        print(f"Erro ao extrair thumbnail: {e}")
        return None


def parse_gcode_objects_for_bed(gcode_path):
    """
    Percorre o G-code e extrai objetos (blocos entre marcadores de objeto).
    Usa apenas marcadores "; printing object" / "; stop printing object" (Orca/Prusa).
    Ignora "; LAYER" para não criar objetos espúrios.
    Retorna lista com bounding box em mm (min_x, min_y, max_x, max_y) por objeto.
    """
    objects = []
    current = None
    obj_id = 0
    try:
        with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                raw = line.strip()
                raw_lower = raw.lower()
                if not raw_lower.startswith(';'):
                    pass
                elif 'stop printing object' in raw_lower:
                    if current is not None and current.get('min_x') is not None:
                        objects.append(current)
                    current = None
                    continue
                elif 'printing object' in raw_lower and 'stop' not in raw_lower:
                    if current is not None and current.get('min_x') is not None:
                        objects.append(current)
                    obj_id += 1
                    name = None
                    m = re.search(r'object[:\s]+(.+?)(?:\s*$|\s*;)', raw_lower, re.I)
                    if m:
                        name = m.group(1).strip().strip(';').strip() or None
                    current = {
                        'id': obj_id - 1,
                        'name': name,
                        'min_x': None,
                        'min_y': None,
                        'max_x': None,
                        'max_y': None,
                    }
                    continue

                if current is None:
                    continue
                cmd = line.split(';')[0].strip().upper()
                if not cmd or (not cmd.startswith('G0') and not cmd.startswith('G1')):
                    continue
                x_m = re.search(r'\bX([-\d.]+)', line, re.I)
                y_m = re.search(r'\bY([-\d.]+)', line, re.I)
                x = float(x_m.group(1)) if x_m else None
                y = float(y_m.group(1)) if y_m else None
                if x is not None:
                    current['min_x'] = x if current['min_x'] is None else min(current['min_x'], x)
                    current['max_x'] = x if current['max_x'] is None else max(current['max_x'], x)
                if y is not None:
                    current['min_y'] = y if current['min_y'] is None else min(current['min_y'], y)
                    current['max_y'] = y if current['max_y'] is None else max(current['max_y'], y)
        if current is not None and current.get('min_x') is not None:
            objects.append(current)
    except Exception as e:
        print(f"⚠️ Erro ao parsear objetos do G-code: {e}")
    return objects


def parse_gcode_metadata(gcode_path):
    """Extrai metadados completos do G-code (OrcaSlicer, PrusaSlicer, Cura, etc.)"""
    metadata = {
        'print_time': None,
        'filament_used': None,
        'filament_type': None,
        'nozzle_temp': None,
        'bed_temp': None,
        'layer_height': None,
        'infill': None,
        'slicer': None,
        'total_layers': None,
        'filament_density': None,
        'filament_diameter': None,
        'max_z_height': None
    }
    
    try:
        with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
            found_m104 = False
            found_m140 = False
            
            for i, line in enumerate(f):
                if i > 500:
                    break
                
                line = line.strip()
                
                if 'generated by' in line.lower():
                    if 'orcaslicer' in line.lower():
                        slicer_match = re.search(r'OrcaSlicer\s+([\d.]+)', line, re.IGNORECASE)
                        if slicer_match:
                            metadata['slicer'] = f"OrcaSlicer {slicer_match.group(1)}"
                    elif 'prusaslicer' in line.lower():
                        slicer_match = re.search(r'PrusaSlicer\s+([\d.]+)', line, re.IGNORECASE)
                        if slicer_match:
                            metadata['slicer'] = f"PrusaSlicer {slicer_match.group(1)}"
                    elif 'cura' in line.lower():
                        metadata['slicer'] = "Cura"
                
                comment_line = line[1:].strip() if line.startswith(';') else line
                
                if 'total layer number' in comment_line.lower():
                    layers_match = re.search(r':\s*(\d+)', comment_line)
                    if layers_match:
                        metadata['total_layers'] = int(layers_match.group(1))
                
                if 'filament_density' in comment_line.lower() and not metadata['filament_density']:
                    density_match = re.search(r':\s*([\d.]+)', comment_line)
                    if density_match:
                        metadata['filament_density'] = float(density_match.group(1))
                
                if 'filament_diameter' in comment_line.lower() and not metadata['filament_diameter']:
                    diameter_match = re.search(r':\s*([\d.]+)', comment_line)
                    if diameter_match:
                        metadata['filament_diameter'] = float(diameter_match.group(1))
                
                if 'max_z_height' in comment_line.lower():
                    z_match = re.search(r':\s*([\d.]+)', comment_line)
                    if z_match:
                        metadata['max_z_height'] = float(z_match.group(1))
                
                if not metadata['print_time']:
                    filename = os.path.basename(gcode_path)
                    time_match = re.search(r'(\d+)h(\d+)m(\d+)s', filename)
                    if time_match:
                        h, m, s = time_match.groups()
                        metadata['print_time'] = f"{h}h {m}m {s}s"
                    else:
                        time_match = re.search(r'(\d+)m(\d+)s', filename)
                        if time_match:
                            m, s = time_match.groups()
                            metadata['print_time'] = f"{m}m {s}s"
                
                if 'estimated printing time' in comment_line.lower() or 'TIME:' in comment_line:
                    time_match = re.search(r'=\s*(.+)', comment_line)
                    if time_match:
                        metadata['print_time'] = time_match.group(1).strip()
                    else:
                        time_match = re.search(r'TIME:\s*(\d+)', comment_line)
                        if time_match:
                            total_seconds = int(time_match.group(1))
                            hours = total_seconds // 3600
                            minutes = (total_seconds % 3600) // 60
                            seconds = total_seconds % 60
                            if hours > 0:
                                metadata['print_time'] = f"{hours}h {minutes}m {seconds}s"
                            else:
                                metadata['print_time'] = f"{minutes}m {seconds}s"
                
                if 'filament used' in comment_line.lower() or 'material used' in comment_line.lower():
                    weight_match = re.search(r'\[g\]\s*=\s*([\d.]+)', comment_line)
                    length_match = re.search(r'\[mm\]\s*=\s*([\d.]+)', comment_line)
                    simple_match = re.search(r':\s*([\d.]+)\s*g', comment_line)
                    
                    if weight_match:
                        metadata['filament_used'] = float(weight_match.group(1))
                    elif simple_match:
                        metadata['filament_used'] = float(simple_match.group(1))
                    elif length_match:
                        length_mm = float(length_match.group(1))
                        if metadata['filament_density'] and metadata['filament_diameter']:
                            radius = metadata['filament_diameter'] / 2
                            volume_mm3 = 3.14159 * (radius ** 2) * length_mm
                            metadata['filament_used'] = round((volume_mm3 / 1000) * metadata['filament_density'], 2)
                        else:
                            metadata['filament_used'] = round((length_mm * 0.0028), 2)
                
                if not metadata['filament_type']:
                    filename = os.path.basename(gcode_path)
                    for material in ['PETG', 'PLA', 'ABS', 'TPU', 'NYLON', 'ASA', 'PC']:
                        if material in filename.upper():
                            metadata['filament_type'] = material
                            break
                
                if 'filament_type' in comment_line.lower() and not metadata['filament_type']:
                    type_match = re.search(r'=\s*(.+)', comment_line)
                    if type_match:
                        filament_value = type_match.group(1).strip().split(',')[0]
                        metadata['filament_type'] = filament_value.strip('"\'')
                
                if not found_m104 and line.startswith('M104'):
                    temp_match = re.search(r'S(\d+)', line)
                    if temp_match:
                        metadata['nozzle_temp'] = int(temp_match.group(1))
                        found_m104 = True
                
                if not found_m104 and ('nozzle_temperature' in comment_line.lower() or 
                    'first_layer_temperature' in comment_line.lower()):
                    temp_match = re.search(r'=\s*([\d]+)', comment_line)
                    if temp_match:
                        metadata['nozzle_temp'] = int(temp_match.group(1))
                
                if not found_m140 and line.startswith('M140'):
                    temp_match = re.search(r'S(\d+)', line)
                    if temp_match:
                        metadata['bed_temp'] = int(temp_match.group(1))
                        found_m140 = True
                
                if not found_m140 and ('bed_temperature' in comment_line.lower() or 
                    'first_layer_bed_temperature' in comment_line.lower()):
                    temp_match = re.search(r'=\s*([\d]+)', comment_line)
                    if temp_match:
                        metadata['bed_temp'] = int(temp_match.group(1))
                
                if 'layer_height' in comment_line.lower() and not metadata['layer_height']:
                    height_match = re.search(r'=\s*([\d.]+)', comment_line)
                    if height_match:
                        metadata['layer_height'] = float(height_match.group(1))
                
                if ('fill_density' in comment_line.lower() or 'infill' in comment_line.lower() or 
                    'sparse infill density' in comment_line.lower()) and not metadata['infill']:
                    infill_match = re.search(r'=\s*([\d.]+)', comment_line)
                    if infill_match:
                        value = float(infill_match.group(1))
                        metadata['infill'] = int(value * 100) if value < 1 else int(value)
    
    except Exception as e:
        print(f"Erro ao parsear metadados do G-code: {e}")
    
    return metadata

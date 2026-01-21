import sqlite3
import os
import base64
import re

def extract_thumbnail(gcode_path, file_id):
    try:
        with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines(500000)
        
        in_thumbnail = False
        thumbnail_data = []
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
            base64_string = ''.join(best_thumbnail_data)
            image_data = base64.b64decode(base64_string)
            thumbnail_filename = f'thumb_{file_id}.png'
            thumbnail_path = os.path.join('static/thumbnails', thumbnail_filename)
            
            with open(thumbnail_path, 'wb') as img_file:
                img_file.write(image_data)
            
            return f'thumbnails/{thumbnail_filename}'
    except Exception as e:
        print(f'Erro ao extrair thumbnail: {e}')
    return None

# Processar arquivo existente
conn = sqlite3.connect('croma.db')
cursor = conn.cursor()
cursor.execute('SELECT id, filename FROM gcode_files')
files = cursor.fetchall()

for file_id, filename in files:
    gcode_path = os.path.join('gcode_files', filename)
    if os.path.exists(gcode_path):
        print(f'Processando: {filename}')
        thumb_path = extract_thumbnail(gcode_path, file_id)
        if thumb_path:
            cursor.execute('UPDATE gcode_files SET thumbnail_path = ? WHERE id = ?', (thumb_path, file_id))
            print(f'✓ Thumbnail extraído: {thumb_path}')
        else:
            print('✗ Nenhum thumbnail encontrado')

conn.commit()
conn.close()
print('\nConcluído!')

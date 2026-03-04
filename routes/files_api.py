"""File management API routes."""

from flask import Blueprint, request, jsonify, session, send_from_directory
import sqlite3
import os
import time
import shutil
import threading
from datetime import datetime
from werkzeug.utils import secure_filename

from core.config import (
    DB_NAME, GCODE_FOLDER, SLICER_TEMP_FOLDER,
    app as flask_app,
)
from core.printer import connect_printer, send_gcode as printer_send_gcode
from core.gcode import (
    allowed_file, allowed_3d_file, get_gcode_info, extract_thumbnail,
    parse_gcode_metadata, run_orca_slice, _log_slicer,
)
from core.print_engine import run_print_job
import core.state as st

files_bp = Blueprint('files_api', __name__)


@files_bp.route('/api/files/list', methods=['GET'])
def list_files():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, original_name, file_size, uploaded_at, last_printed, print_count, filename, thumbnail_path,
               print_time, filament_used, filament_type, nozzle_temp, bed_temp, layer_height, infill,
               slicer, total_layers, filament_density, filament_diameter, max_z_height
        FROM gcode_files 
        WHERE user_id = ?
        ORDER BY uploaded_at DESC
    ''', (session['user_id'],))

    files = []
    for row in cursor.fetchall():
        files.append({
            'id': row[0],
            'name': row[1],
            'size': row[2],
            'uploaded': row[3],
            'last_printed': row[4],
            'print_count': row[5],
            'filename': row[6],
            'thumbnail': row[7],
            'print_time': row[8],
            'filament_used': row[9],
            'filament_type': row[10],
            'nozzle_temp': row[11],
            'bed_temp': row[12],
            'layer_height': row[13],
            'infill': row[14],
            'slicer': row[15],
            'total_layers': row[16],
            'filament_density': row[17],
            'filament_diameter': row[18],
            'max_z_height': row[19]
        })

    conn.close()
    return jsonify({'success': True, 'files': files})


@files_bp.route('/api/files/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido. Use .gcode, .gco ou .g'}), 400

    original_name = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{original_name}"
    filepath = os.path.join(flask_app.config['GCODE_FOLDER'], filename)

    file.save(filepath)
    file_info = get_gcode_info(filepath)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO gcode_files (user_id, filename, original_name, file_size)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], filename, original_name, file_info['size']))
    conn.commit()
    file_id = cursor.lastrowid

    thumbnail_path = extract_thumbnail(filepath, file_id)
    if thumbnail_path:
        cursor.execute('UPDATE gcode_files SET thumbnail_path = ? WHERE id = ?',
                       (thumbnail_path, file_id))
        conn.commit()

    metadata = parse_gcode_metadata(filepath)
    if metadata:
        cursor.execute('''
            UPDATE gcode_files 
            SET print_time = ?, filament_used = ?, filament_type = ?, 
                nozzle_temp = ?, bed_temp = ?, layer_height = ?, infill = ?,
                slicer = ?, total_layers = ?, filament_density = ?, 
                filament_diameter = ?, max_z_height = ?
            WHERE id = ?
        ''', (metadata['print_time'], metadata['filament_used'], metadata['filament_type'],
              metadata['nozzle_temp'], metadata['bed_temp'], metadata['layer_height'],
              metadata['infill'], metadata['slicer'], metadata['total_layers'],
              metadata['filament_density'], metadata['filament_diameter'],
              metadata['max_z_height'], file_id))
        conn.commit()

    conn.close()

    return jsonify({
        'success': True,
        'message': 'Arquivo enviado com sucesso',
        'file_id': file_id,
        'filename': original_name
    })


@files_bp.route('/api/slicer/slice', methods=['POST'])
def slicer_slice():
    """Recebe .stl ou .obj, chama OrcaSlicer, salva G-code em gcode_files e retorna file_id."""
    _log_slicer("POST /api/slicer/slice recebido")
    if 'user_id' not in session:
        _log_slicer("401: não autenticado")
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    if 'file' not in request.files:
        _log_slicer("400: file não está em request.files (keys: %s)", list(request.files.keys()))
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']
    _log_slicer("Arquivo: filename=%r content_type=%r content_length=%s", file.filename, file.content_type, getattr(file, 'content_length', None))
    if file.filename == '':
        _log_slicer("400: filename vazio")
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400

    if not allowed_3d_file(file.filename):
        _log_slicer("400: tipo não permitido %r", file.filename)
        return jsonify({
            'success': False,
            'message': 'Tipo não permitido. Envie um arquivo .stl ou .obj'
        }), 400

    layer_height = request.form.get('layer_height', type=float)
    infill = request.form.get('infill', type=int)
    _log_slicer("Opções: layer_height=%s infill=%s", layer_height, infill)

    temp_base = os.path.join(flask_app.config['SLICER_TEMP_FOLDER'], f"slice_{session['user_id']}_{int(time.time() * 1000)}")
    input_dir = temp_base + '_in'
    output_dir = temp_base + '_out'
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    _log_slicer("Temp: input_dir=%s output_dir=%s", input_dir, output_dir)

    original_name = secure_filename(file.filename) or 'model'
    stl_temp_name = 'model.stl' if original_name.lower().endswith('.stl') else 'model.obj'
    stl_path = os.path.join(input_dir, stl_temp_name)
    try:
        file.save(stl_path)
        _log_slicer("Arquivo salvo em %s", stl_path)
    except Exception as e:
        _log_slicer("Erro ao salvar: %s", e)
        return jsonify({'success': False, 'message': f'Erro ao salvar arquivo: {str(e)}'}), 500

    try:
        size = os.path.getsize(stl_path)
    except OSError as e:
        size = 0
        _log_slicer("getsize falhou: %s", e)
    _log_slicer("Tamanho do arquivo salvo: %s bytes", size)
    if size == 0:
        _log_slicer("400: arquivo vazio após save")
        return jsonify({
            'success': False,
            'message': 'Arquivo chegou vazio. Verifique se o arquivo foi selecionado corretamente e tente de novo. Se usar proxy (Vite), confira se o backend está na porta correta.'
        }), 400

    try:
        gcode_path = run_orca_slice(stl_path, output_dir, layer_height=layer_height, infill=infill)
        _log_slicer("run_orca_slice retornou: %s", gcode_path)
    except RuntimeError as e:
        _log_slicer("run_orca_slice falhou: %s", e)
        return jsonify({'success': False, 'message': str(e)}), 400

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    gcode_original_name = os.path.splitext(original_name)[0] + '.gcode'
    gcode_filename = f"{timestamp}_{gcode_original_name}"
    gcode_dest = os.path.join(flask_app.config['GCODE_FOLDER'], gcode_filename)
    try:
        shutil.copy2(gcode_path, gcode_dest)
        _log_slicer("G-code copiado para %s", gcode_dest)
    except Exception as e:
        _log_slicer("Erro ao copiar G-code: %s", e)
        return jsonify({'success': False, 'message': f'Erro ao copiar G-code: {str(e)}'}), 500

    file_info = get_gcode_info(gcode_dest)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO gcode_files (user_id, filename, original_name, file_size)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], gcode_filename, gcode_original_name, file_info['size']))
    conn.commit()
    file_id = cursor.lastrowid

    thumbnail_path = extract_thumbnail(gcode_dest, file_id)
    if thumbnail_path:
        cursor.execute('UPDATE gcode_files SET thumbnail_path = ? WHERE id = ?', (thumbnail_path, file_id))
        conn.commit()

    metadata = parse_gcode_metadata(gcode_dest)
    if metadata:
        cursor.execute('''
            UPDATE gcode_files 
            SET print_time = ?, filament_used = ?, filament_type = ?, 
                nozzle_temp = ?, bed_temp = ?, layer_height = ?, infill = ?,
                slicer = ?, total_layers = ?, filament_density = ?, 
                filament_diameter = ?, max_z_height = ?
            WHERE id = ?
        ''', (
            metadata['print_time'], metadata['filament_used'], metadata['filament_type'],
            metadata['nozzle_temp'], metadata['bed_temp'], metadata['layer_height'],
            metadata['infill'], metadata['slicer'], metadata['total_layers'],
            metadata['filament_density'], metadata['filament_diameter'],
            metadata['max_z_height'], file_id
        ))
        conn.commit()
    conn.close()

    try:
        if os.path.isfile(stl_path):
            os.remove(stl_path)
        for f in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, f))
        os.rmdir(output_dir)
        os.rmdir(input_dir)
        _log_slicer("Temp limpo")
    except Exception as e:
        _log_slicer("Aviso ao limpar temp: %s", e)

    _log_slicer("Sucesso: file_id=%s filename=%s", file_id, gcode_original_name)
    return jsonify({
        'success': True,
        'message': 'G-code gerado com sucesso',
        'file_id': file_id,
        'filename': gcode_original_name
    })


@files_bp.route('/api/files/delete/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT filename FROM gcode_files WHERE id = ? AND user_id = ?',
                   (file_id, session['user_id']))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return jsonify({'success': False, 'message': 'Arquivo não encontrado'}), 404

    filename = result[0]
    filepath = os.path.join(flask_app.config['GCODE_FOLDER'], filename)

    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Erro ao deletar arquivo: {str(e)}'}), 500

    cursor.execute('DELETE FROM gcode_files WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Arquivo deletado com sucesso'})


@files_bp.route('/api/files/print/<int:file_id>', methods=['POST'])
def print_file(file_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT filename, original_name FROM gcode_files WHERE id = ? AND user_id = ?',
                   (file_id, session['user_id']))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return jsonify({'success': False, 'message': 'Arquivo não encontrado'}), 404

    filename = result[0]
    original_name = result[1]
    filepath = os.path.join(flask_app.config['GCODE_FOLDER'], filename)

    if not st.printer_serial or not st.printer_serial.is_open:
        if not connect_printer():
            conn.close()
            return jsonify({'success': False, 'message': 'Impressora não conectada'}), 500

    cursor.execute('''
        UPDATE print_jobs 
        SET status = 'cancelled', completed_at = CURRENT_TIMESTAMP
        WHERE status = 'printing'
    ''')
    conn.commit()

    if not os.path.exists(filepath):
        conn.close()
        return jsonify({'success': False, 'message': 'Arquivo G-code não encontrado'}), 404

    cursor.execute('''
        UPDATE gcode_files 
        SET last_printed = CURRENT_TIMESTAMP, print_count = print_count + 1
        WHERE id = ?
    ''', (file_id,))

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO print_jobs (user_id, filename, status, progress, started_at)
        VALUES (?, ?, 'printing', 0, ?)
    ''', (session['user_id'], original_name, current_time))

    job_id = cursor.lastrowid
    conn.commit()
    conn.close()

    thread = threading.Thread(
        target=run_print_job,
        args=(filepath, original_name, job_id),
        daemon=True,
    )
    thread.start()

    return jsonify({
        'success': True,
        'message': f'Iniciando impressão de {original_name}'
    })


@files_bp.route('/api/files/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT filename, original_name FROM gcode_files WHERE id = ? AND user_id = ?',
                   (file_id, session['user_id']))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return jsonify({'success': False, 'message': 'Arquivo não encontrado'}), 404

    filename = result[0]
    original_name = result[1]

    return send_from_directory(flask_app.config['GCODE_FOLDER'], filename, as_attachment=True, download_name=original_name)


@files_bp.route('/api/files/preview/<int:file_id>', methods=['GET'])
def preview_gcode(file_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT filename FROM gcode_files WHERE id = ? AND user_id = ?',
                   (file_id, session['user_id']))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return jsonify({'success': False, 'message': 'Arquivo não encontrado'}), 404

    filename = result[0]
    filepath = os.path.join(flask_app.config['GCODE_FOLDER'], filename)

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            gcode_content = f.read(10 * 1024 * 1024)
        return jsonify({'success': True, 'gcode': gcode_content})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao ler arquivo: {str(e)}'}), 500

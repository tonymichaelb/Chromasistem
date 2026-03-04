"""HTML page routes."""

from flask import (Blueprint, render_template, session, redirect,
                   send_from_directory, abort)
import sqlite3
import os

from core.config import DB_NAME, REACT_DIST, USE_REACT_APP

pages_bp = Blueprint('pages', __name__)


def _serve_react_index():
    """Serve index.html do build React quando USE_REACT_APP."""
    if USE_REACT_APP:
        return send_from_directory(REACT_DIST, 'index.html')
    return None


@pages_bp.route('/')
def index():
    r = _serve_react_index()
    if r is not None:
        return r
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')


@pages_bp.route('/login')
def login():
    r = _serve_react_index()
    if r is not None:
        return r
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    conn.close()

    return render_template('login.html', allow_registration=(user_count == 0))


@pages_bp.route('/register')
def register():
    r = _serve_react_index()
    if r is not None:
        return r
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    conn.close()

    if user_count > 0:
        return redirect('/login')

    return render_template('register.html')


@pages_bp.route('/dashboard')
def dashboard():
    r = _serve_react_index()
    if r is not None:
        return r
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, original_name, file_size, uploaded_at, print_count, thumbnail_path,
               print_time, filament_used, filament_type, nozzle_temp, bed_temp, layer_height, infill,
               slicer, total_layers, filament_density, filament_diameter, max_z_height
        FROM gcode_files 
        WHERE user_id = ?
        ORDER BY uploaded_at DESC
        LIMIT 5
    ''', (session['user_id'],))

    recent_files = []
    for row in cursor.fetchall():
        recent_files.append({
            'id': row[0],
            'name': row[1],
            'size': row[2],
            'uploaded': row[3],
            'print_count': row[4],
            'thumbnail': row[5],
            'print_time': row[6],
            'filament_used': row[7],
            'filament_type': row[8],
            'nozzle_temp': row[9],
            'bed_temp': row[10],
            'layer_height': row[11],
            'infill': row[12],
            'slicer': row[13],
            'total_layers': row[14],
            'filament_density': row[15],
            'filament_diameter': row[16],
            'max_z_height': row[17]
        })

    conn.close()
    return render_template('dashboard.html', username=session.get('username'), recent_files=recent_files)


@pages_bp.route('/files')
def files():
    r = _serve_react_index()
    if r is not None:
        return r
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('files.html', username=session.get('username'))


@pages_bp.route('/viewer')
@pages_bp.route('/viewer/<path:filename>')
def viewer(filename=None):
    r = _serve_react_index()
    if r is not None:
        return r
    if 'user_id' not in session:
        return redirect('/login')

    file_id = None
    if filename:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id FROM gcode_files 
            WHERE original_name = ? AND user_id = ?
        ''', (filename, session['user_id']))
        result = cursor.fetchone()
        conn.close()

        if result:
            file_id = result[0]
            print(f"✓ Arquivo '{filename}' encontrado com ID: {file_id}")
        else:
            print(f"✗ Arquivo '{filename}' NÃO encontrado para user_id={session['user_id']}")
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute('SELECT id, original_name FROM gcode_files WHERE user_id = ?', (session['user_id'],))
            all_files = cursor.fetchall()
            conn.close()
            print(f"  Arquivos disponíveis: {all_files}")

    return render_template('gcode_viewer.html', username=session.get('username'), file_id=file_id)


@pages_bp.route('/terminal')
def terminal():
    r = _serve_react_index()
    if r is not None:
        return r
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('terminal.html', username=session.get('username'))


@pages_bp.route('/wifi')
def wifi_page():
    r = _serve_react_index()
    if r is not None:
        return r
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('wifi.html')


@pages_bp.route('/colorir')
def colorir():
    """Página de seleção de pincéis (extrusores)"""
    r = _serve_react_index()
    if r is not None:
        return r
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('colorir.html', username=session.get('username'))


@pages_bp.route('/mistura')
def mistura():
    """Página de mistura de filamentos"""
    r = _serve_react_index()
    if r is not None:
        return r
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('mistura.html', username=session.get('username'))


@pages_bp.route('/fatiador')
def fatiador():
    """Página do fatiador (slicer) - React SPA"""
    r = _serve_react_index()
    if r is not None:
        return r
    if 'user_id' not in session:
        return redirect('/login')
    return redirect('/files')


@pages_bp.route('/assets/<path:path>')
def serve_react_assets(path):
    if USE_REACT_APP:
        return send_from_directory(os.path.join(REACT_DIST, 'assets'), path)
    abort(404)


@pages_bp.route('/vite.svg')
def serve_vite_svg():
    if USE_REACT_APP and os.path.isfile(os.path.join(REACT_DIST, 'vite.svg')):
        return send_from_directory(REACT_DIST, 'vite.svg')
    abort(404)


@pages_bp.route('/images/<path:path>')
def serve_react_images(path):
    """Serve imagens do build React (ex: logo) ou static/images"""
    if USE_REACT_APP:
        img_dir = os.path.join(REACT_DIST, 'images')
        if os.path.isfile(os.path.join(img_dir, path)):
            return send_from_directory(img_dir, path)
    static_img = os.path.join('static', 'images', path)
    if os.path.isfile(static_img):
        return send_from_directory('static', os.path.join('images', path))
    abort(404)

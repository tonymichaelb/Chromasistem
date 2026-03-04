"""Authentication API routes."""

from flask import Blueprint, request, jsonify, session
import sqlite3

from core.config import DB_NAME, get_app_version
from core.database import hash_password

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'success': False, 'message': 'Usuário e senha são obrigatórios'}), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if user and user[2] == hash_password(password):
        session['user_id'] = user[0]
        session['username'] = user[1]
        return jsonify({'success': True, 'message': 'Login realizado com sucesso'})

    return jsonify({'success': False, 'message': 'Usuário ou senha inválidos'}), 401


@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'success': False, 'message': 'Usuário e senha são obrigatórios'}), 400

    if len(password) < 6:
        return jsonify({'success': False, 'message': 'A senha deve ter pelo menos 6 caracteres'}), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]

    if user_count > 0:
        conn.close()
        return jsonify({'success': False, 'message': 'Registro não permitido. Use uma conta existente.'}), 403

    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                       (username, hash_password(password)))
        conn.commit()
        user_id = cursor.lastrowid
        session['user_id'] = user_id
        session['username'] = username
        conn.close()
        return jsonify({'success': True, 'message': 'Conta criada com sucesso'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Nome de usuário já existe'}), 409


@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logout realizado com sucesso'})


@auth_bp.route('/api/me', methods=['GET'])
def api_me():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    return jsonify({'success': True, 'username': session.get('username', '')})


@auth_bp.route('/api/version', methods=['GET'])
def api_version():
    return jsonify({'version': get_app_version()})

"""Database initialization and helpers."""

import sqlite3
import hashlib
from core.config import DB_NAME


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS print_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            status TEXT,
            progress REAL,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gcode_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_size INTEGER,
            thumbnail_path TEXT,
            print_time TEXT,
            filament_used REAL,
            filament_type TEXT,
            nozzle_temp INTEGER,
            bed_temp INTEGER,
            layer_height REAL,
            infill INTEGER,
            slicer TEXT,
            total_layers INTEGER,
            filament_density REAL,
            filament_diameter REAL,
            max_z_height REAL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_printed TIMESTAMP,
            print_count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS brush_mixtures (
            brush_id INTEGER PRIMARY KEY,
            a_percent INTEGER DEFAULT 33,
            b_percent INTEGER DEFAULT 33,
            c_percent INTEGER DEFAULT 34,
            custom_color TEXT,
            tinta_color TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS print_pause_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            print_job_id INTEGER NOT NULL,
            gcode_filename TEXT NOT NULL,
            file_offset INTEGER NOT NULL,
            pos_x REAL, pos_y REAL, pos_z REAL, pos_e REAL,
            target_nozzle REAL, target_bed REAL,
            pause_option TEXT DEFAULT 'keep_temp',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (print_job_id) REFERENCES print_jobs (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS print_failure_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            print_job_id INTEGER NOT NULL,
            occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            failure_code TEXT,
            failure_message TEXT,
            action TEXT NOT NULL,
            object_index_or_name TEXT,
            FOREIGN KEY (print_job_id) REFERENCES print_jobs (id)
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                       ('admin', hash_password('croma123')))
        conn.commit()
        print("✓ Usuário padrão criado: admin / croma123 (troque a senha após o primeiro login)")
    conn.close()

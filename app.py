from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_cors import CORS
import sqlite3
import hashlib
import os
from datetime import datetime
import serial
import time
from werkzeug.utils import secure_filename
import re
import base64
import subprocess

# Importar GPIO (com fallback para desenvolvimento em outros sistemas)
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False
    print("⚠️ RPi.GPIO não disponível - sensor de filamento desabilitado")

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Configuração do banco de dados
DB_NAME = 'croma.db'

# Configuração de upload de arquivos G-code
GCODE_FOLDER = 'gcode_files'
THUMBNAIL_FOLDER = 'static/thumbnails'
ALLOWED_EXTENSIONS = {'gcode', 'gco', 'g'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Criar pastas se não existirem
if not os.path.exists(GCODE_FOLDER):
    os.makedirs(GCODE_FOLDER)
if not os.path.exists(THUMBNAIL_FOLDER):
    os.makedirs(THUMBNAIL_FOLDER)

app.config['GCODE_FOLDER'] = GCODE_FOLDER
app.config['THUMBNAIL_FOLDER'] = THUMBNAIL_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Configuração da conexão serial com a impressora
SERIAL_PORT = '/dev/ttyUSB0'  # Porta serial padrão no Raspberry Pi (ajustar se necessário)
SERIAL_BAUDRATE = 115200
SERIAL_TIMEOUT = 2

# Configuração do sensor de filamento
FILAMENT_SENSOR_PIN = 17  # GPIO17 (Pino físico 11)

# Variável global para conexão serial
printer_serial = None

# Variável global para estado do filamento
filament_status = {
    'has_filament': True,
    'sensor_enabled': GPIO_AVAILABLE,
    'last_check': None
}

# Configurar GPIO para sensor de filamento
def setup_filament_sensor():
    """Inicializa o sensor de filamento"""
    if not GPIO_AVAILABLE:
        print("⚠️ GPIO não disponível - sensor de filamento não configurado")
        return False
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(FILAMENT_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Configurar callback para detecção de mudança
        GPIO.add_event_detect(FILAMENT_SENSOR_PIN, GPIO.BOTH, 
                            callback=filament_sensor_callback, 
                            bouncetime=300)
        
        print(f"✓ Sensor de filamento configurado no GPIO{FILAMENT_SENSOR_PIN}")
        return True
    except Exception as e:
        print(f"✗ Erro ao configurar sensor de filamento: {e}")
        return False

def filament_sensor_callback(channel):
    """Callback executado quando o sensor detecta mudança"""
    global filament_status
    
    # Ler estado do GPIO
    # Normalmente ABERTO: GPIO HIGH (1) = com filamento
    # FECHADO: GPIO LOW (0) = sem filamento
    gpio_state = GPIO.input(FILAMENT_SENSOR_PIN)
    has_filament = bool(gpio_state)
    
    filament_status['has_filament'] = has_filament
    filament_status['last_check'] = datetime.now().isoformat()
    
    if not has_filament:
        print("⚠️ ALERTA: Filamento acabou! Pausando impressão...")
        # Pausar impressão automaticamente
        send_gcode('M25')  # Pausar SD print
        send_gcode('M117 Sem filamento!')  # Mensagem no display
    else:
        print("✓ Filamento detectado")

def check_filament_sensor():
    """Verifica estado atual do sensor de filamento"""
    global filament_status
    
    if not GPIO_AVAILABLE:
        return filament_status
    
    try:
        gpio_state = GPIO.input(FILAMENT_SENSOR_PIN)
        filament_status['has_filament'] = bool(gpio_state)
        filament_status['last_check'] = datetime.now().isoformat()
    except Exception as e:
        print(f"Erro ao ler sensor de filamento: {e}")
    
    return filament_status

# Inicializar banco de dados
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
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_printed TIMESTAMP,
            print_count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# Hash de senha
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Conectar à impressora via serial
def connect_printer():
    global printer_serial
    try:
        if printer_serial and printer_serial.is_open:
            return True
        
        printer_serial = serial.Serial(
            port=SERIAL_PORT,
            baudrate=SERIAL_BAUDRATE,
            timeout=SERIAL_TIMEOUT
        )
        time.sleep(2)  # Aguardar inicialização
        print(f"✓ Conectado à impressora em {SERIAL_PORT} @ {SERIAL_BAUDRATE} baud")
        return True
    except Exception as e:
        print(f"✗ Erro ao conectar impressora: {e}")
        printer_serial = None
        return False

# Desconectar impressora
def disconnect_printer():
    global printer_serial
    try:
        if printer_serial and printer_serial.is_open:
            printer_serial.close()
            print("✓ Impressora desconectada")
    except Exception as e:
        print(f"Erro ao desconectar: {e}")
    finally:
        printer_serial = None

# Enviar comando G-code para impressora
def send_gcode(command):
    global printer_serial
    try:
        if not printer_serial or not printer_serial.is_open:
            if not connect_printer():
                return None
        
        # Adicionar newline se não existir
        if not command.endswith('\n'):
            command += '\n'
        
        printer_serial.write(command.encode())
        
        # Ler resposta
        response = printer_serial.readline().decode('utf-8').strip()
        return response
    except Exception as e:
        print(f"Erro ao enviar comando '{command.strip()}': {e}")
        return None

# Ler status da impressora
def get_printer_status_serial():
    try:
        # Enviar M105 para ler temperatura
        temp_response = send_gcode('M105')
        
        # Enviar M27 para ler progresso de impressão
        progress_response = send_gcode('M27')
        
        status = {
            'connected': printer_serial and printer_serial.is_open,
            'printing': False,
            'progress': 0,
            'bed_temp': 0,
            'nozzle_temp': 0,
            'target_bed_temp': 0,
            'target_nozzle_temp': 0
        }
        
        # Parse da temperatura (ex: "ok T:210.0 /210.0 B:60.0 /60.0")
        if temp_response and 'T:' in temp_response:
            try:
                # Extrai temperatura do bico
                t_match = re.search(r'T:(\d+\.?\d*)\s*/(\d+\.?\d*)', temp_response)
                if t_match:
                    status['nozzle_temp'] = float(t_match.group(1))
                    status['target_nozzle_temp'] = float(t_match.group(2))
                
                # Extrai temperatura da mesa
                b_match = re.search(r'B:(\d+\.?\d*)\s*/(\d+\.?\d*)', temp_response)
                if b_match:
                    status['bed_temp'] = float(b_match.group(1))
                    status['target_bed_temp'] = float(b_match.group(2))
            except Exception as e:
                print(f"Erro ao parsear temperatura: {e}")
        
        # Parse do progresso (ex: "SD printing byte 1234/5678")
        if progress_response and 'SD printing' in progress_response:
            try:
                match = re.search(r'(\d+)/(\d+)', progress_response)
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    status['progress'] = (current / total) * 100 if total > 0 else 0
                    status['printing'] = True
            except Exception as e:
                print(f"Erro ao parsear progresso: {e}")
        
        return status
    except Exception as e:
        print(f"Erro ao obter status: {e}")
        return {
            'connected': False,
            'printing': False,
            'progress': 0,
            'bed_temp': 0,
            'nozzle_temp': 0,
            'target_bed_temp': 0,
            'target_nozzle_temp': 0
        }

# Verificar extensão de arquivo permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Obter informações do arquivo G-code
def get_gcode_info(filepath):
    try:
        file_size = os.path.getsize(filepath)
        # Aqui poderia analisar o G-code para estimar tempo, etc
        return {'size': file_size}
    except:
        return {'size': 0}

# Extrair thumbnail do G-code (PrusaSlicer, OrcaSlicer, BambuStudio)
def extract_thumbnail(gcode_path, file_id):
    try:
        with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines(500000)  # Ler primeiras linhas onde geralmente está o thumbnail
        
        # Procurar thumbnail no formato OrcaSlicer/BambuStudio
        in_thumbnail = False
        thumbnail_data = []
        thumbnail_width = 0
        thumbnail_height = 0
        max_thumbnail_size = 0
        best_thumbnail_data = []
        
        for line in lines:
            line = line.strip()
            
            # Início do thumbnail
            if 'thumbnail begin' in line or 'thumbnail_PNG begin' in line:
                match = re.search(r'(\d+)x(\d+)', line)
                if match:
                    width = int(match.group(1))
                    height = int(match.group(2))
                    current_size = width * height
                    
                    if current_size > max_thumbnail_size:
                        # Este é maior, começar a capturar
                        max_thumbnail_size = current_size
                        thumbnail_width = width
                        thumbnail_height = height
                        thumbnail_data = []
                        in_thumbnail = True
                    else:
                        # Ignorar thumbnails menores
                        in_thumbnail = False
            
            # Fim do thumbnail
            elif 'thumbnail end' in line or 'thumbnail_PNG end' in line:
                if in_thumbnail and thumbnail_data:
                    best_thumbnail_data = thumbnail_data[:]
                in_thumbnail = False
            
            # Dados do thumbnail (linhas com base64)
            elif in_thumbnail and line.startswith(';'):
                # Remover o ';' e espaços
                data = line[1:].strip()
                if data:  # Adicionar apenas se não for vazio
                    thumbnail_data.append(data)
        
        # Se encontrou thumbnail, processar
        if best_thumbnail_data:
            try:
                # Juntar todas as linhas base64
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

# Rotas de autenticação
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    # Verificar se existem usuários cadastrados
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    conn.close()
    
    return render_template('login.html', allow_registration=(user_count == 0))

@app.route('/register')
def register():
    # Verificar se já existem usuários
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    conn.close()
    
    # Se já existir usuário, redirecionar para login
    if user_count > 0:
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Buscar últimos 5 arquivos G-code
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, original_name, file_size, uploaded_at, print_count, thumbnail_path,
               print_time, filament_used, filament_type, nozzle_temp, bed_temp, layer_height, infill
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
            'infill': row[12]
        })
    
    conn.close()
    return render_template('dashboard.html', username=session.get('username'), recent_files=recent_files)

@app.route('/files')
def files():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('files.html', username=session.get('username'))

# API de autenticação
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
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

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Usuário e senha são obrigatórios'}), 400
    
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'A senha deve ter pelo menos 6 caracteres'}), 400
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Verificar se já existem usuários (apenas o primeiro pode se registrar)
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

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logout realizado com sucesso'})

# API de controle da impressora
@app.route('/api/printer/status', methods=['GET'])
def printer_status():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    # Tentar obter status real da impressora
    status_data = get_printer_status_serial()
    
    # Buscar informações da impressão atual no banco
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT filename, progress 
        FROM print_jobs 
        WHERE status = 'printing' 
        ORDER BY started_at DESC 
        LIMIT 1
    ''')
    current_job = cursor.fetchone()
    conn.close()
    
    # Verificar status do sensor de filamento
    filament_info = check_filament_sensor()
    
    status = {
        'connected': status_data['connected'],
        'temperature': {
            'bed': status_data['bed_temp'],
            'nozzle': status_data['nozzle_temp'],
            'target_bed': status_data['target_bed_temp'],
            'target_nozzle': status_data['target_nozzle_temp']
        },
        'state': 'printing' if status_data['printing'] else 'idle',
        'progress': status_data['progress'],
        'filename': current_job[0] if current_job else '',
        'time_elapsed': '00:00:00',  # Calcular baseado no tempo de início
        'time_remaining': '00:00:00',  # Estimar baseado no progresso
        'filament': filament_info  # Adicionar info do sensor de filamento
    }
    return jsonify({'success': True, 'status': status})

@app.route('/api/printer/pause', methods=['POST'])
def printer_pause():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    # Pausar impressão via serial (M25)
    response = send_gcode('M25')
    if response:
        return jsonify({'success': True, 'message': 'Impressão pausada'})
    else:
        return jsonify({'success': False, 'message': 'Erro ao pausar impressão'}), 500

@app.route('/api/printer/resume', methods=['POST'])
def printer_resume():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    # Retomar impressão via serial (M24)
    response = send_gcode('M24')
    if response:
        return jsonify({'success': True, 'message': 'Impressão retomada'})
    else:
        return jsonify({'success': False, 'message': 'Erro ao retomar impressão'}), 500

@app.route('/api/printer/stop', methods=['POST'])
def printer_stop():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    # Parar impressão via serial
    send_gcode('M108')  # Break e cancelar aquecimento
    send_gcode('M104 S0')  # Desligar aquecedor do bico
    send_gcode('M140 S0')  # Desligar aquecedor da mesa
    send_gcode('M107')  # Desligar ventilador
    send_gcode('G28 X Y')  # Home X e Y
    
    return jsonify({'success': True, 'message': 'Impressão parada'})

@app.route('/api/printer/start', methods=['POST'])
def printer_start():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    data = request.get_json()
    filename = data.get('filename')
    
    # Comando para iniciar impressão
    # Em produção: iniciar impressão do arquivo G-code
    return jsonify({'success': True, 'message': f'Impressão iniciada: {filename}'})

# API de Gerenciamento de Arquivos G-code
@app.route('/api/files/list', methods=['GET'])
def list_files():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, original_name, file_size, uploaded_at, last_printed, print_count, filename, thumbnail_path,
               print_time, filament_used, filament_type, nozzle_temp, bed_temp, layer_height, infill
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
            'infill': row[14]
        })
    
    conn.close()
    return jsonify({'success': True, 'files': files})

@app.route('/api/files/upload', methods=['POST'])
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
    filepath = os.path.join(app.config['GCODE_FOLDER'], filename)
    
    file.save(filepath)
    file_info = get_gcode_info(filepath)
    
    # Salvar no banco de dados
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO gcode_files (user_id, filename, original_name, file_size)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], filename, original_name, file_info['size']))
    conn.commit()
    file_id = cursor.lastrowid
    
    # Extrair thumbnail
    thumbnail_path = extract_thumbnail(filepath, file_id)
    if thumbnail_path:
        cursor.execute('UPDATE gcode_files SET thumbnail_path = ? WHERE id = ?', 
                      (thumbnail_path, file_id))
        conn.commit()
    
    # Extrair metadados do G-code
    metadata = parse_gcode_metadata(filepath)
    if metadata:
        cursor.execute('''
            UPDATE gcode_files 
            SET print_time = ?, filament_used = ?, filament_type = ?, 
                nozzle_temp = ?, bed_temp = ?, layer_height = ?, infill = ?
            WHERE id = ?
        ''', (metadata['print_time'], metadata['filament_used'], metadata['filament_type'],
              metadata['nozzle_temp'], metadata['bed_temp'], metadata['layer_height'], 
              metadata['infill'], file_id))
        conn.commit()
    
    conn.close()
    
    return jsonify({
        'success': True, 
        'message': 'Arquivo enviado com sucesso',
        'file_id': file_id,
        'filename': original_name
    })

@app.route('/api/files/delete/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Verificar se o arquivo pertence ao usuário
    cursor.execute('SELECT filename FROM gcode_files WHERE id = ? AND user_id = ?', 
                  (file_id, session['user_id']))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return jsonify({'success': False, 'message': 'Arquivo não encontrado'}), 404
    
    filename = result[0]
    filepath = os.path.join(app.config['GCODE_FOLDER'], filename)
    
    # Deletar arquivo físico
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Erro ao deletar arquivo: {str(e)}'}), 500
    
    # Deletar do banco de dados
    cursor.execute('DELETE FROM gcode_files WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Arquivo deletado com sucesso'})

@app.route('/api/files/print/<int:file_id>', methods=['POST'])
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
    
    # Atualizar contadores
    cursor.execute('''
        UPDATE gcode_files 
        SET last_printed = CURRENT_TIMESTAMP, print_count = print_count + 1
        WHERE id = ?
    ''', (file_id,))
    conn.commit()
    conn.close()
    
    # Em produção: enviar arquivo para impressora
    filepath = os.path.join(app.config['GCODE_FOLDER'], filename)
    
    return jsonify({
        'success': True, 
        'message': f'Iniciando impressão de {original_name}',
        'filepath': filepath
    })

@app.route('/api/files/download/<int:file_id>', methods=['GET'])
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
    
    return send_from_directory(app.config['GCODE_FOLDER'], filename, as_attachment=True, download_name=original_name)

# ==================== ROTAS DE CONFIGURAÇÃO WI-FI ====================

@app.route('/wifi')
def wifi_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('wifi.html')

@app.route('/api/wifi/scan', methods=['GET'])
def wifi_scan():
    """Escaneia redes Wi-Fi disponíveis"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    try:
        result = subprocess.run(['sudo', 'python3', 'wifi_manager.py', 'scan'], 
                              capture_output=True, text=True, timeout=15)
        
        networks = []
        for line in result.stdout.strip().split('\n'):
            if 'SSID:' in line:
                parts = line.split(',')
                ssid = parts[0].replace('SSID:', '').strip()
                signal = parts[1].replace('Sinal:', '').replace('%', '').strip() if len(parts) > 1 else '0'
                security = parts[2].replace('Segurança:', '').strip() if len(parts) > 2 else 'Aberta'
                
                networks.append({
                    'ssid': ssid,
                    'signal': int(signal) if signal.isdigit() else 0,
                    'security': security
                })
        
        return jsonify({'success': True, 'networks': networks})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/wifi/connect', methods=['POST'])
def wifi_connect():
    """Conecta a uma rede Wi-Fi"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    data = request.get_json()
    ssid = data.get('ssid')
    password = data.get('password', '')
    
    if not ssid:
        return jsonify({'success': False, 'message': 'SSID não fornecido'}), 400
    
    try:
        result = subprocess.run(['sudo', 'python3', 'wifi_manager.py', 'connect', ssid, password],
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': f'Conectado à rede {ssid}'})
        else:
            return jsonify({'success': False, 'message': 'Erro ao conectar'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/wifi/status', methods=['GET'])
def wifi_status():
    """Retorna status da conexão Wi-Fi"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    try:
        # Obter SSID atual
        result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True, timeout=5)
        current_ssid = result.stdout.strip() if result.returncode == 0 else None
        
        # Obter IP
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
        ip_address = result.stdout.strip().split()[0] if result.returncode == 0 else None
        
        # Verificar se é hotspot
        is_hotspot = current_ssid == 'Croma-3D-Printer' if current_ssid else False
        
        return jsonify({
            'success': True,
            'status': {
                'connected': bool(current_ssid),
                'ssid': current_ssid,
                'ip': ip_address,
                'is_hotspot': is_hotspot
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/wifi/saved', methods=['GET'])
def wifi_saved():
    """Lista redes Wi-Fi salvas"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    try:
        result = subprocess.run(['sudo', 'nmcli', '-t', '-f', 'NAME,TYPE', 'connection', 'show'],
                              capture_output=True, text=True, timeout=10)
        
        networks = []
        for line in result.stdout.strip().split('\n'):
            if '802-11-wireless' in line:
                name = line.split(':')[0]
                networks.append(name)
        
        return jsonify({'success': True, 'networks': networks})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/wifi/forget', methods=['POST'])
def wifi_forget():
    """Remove uma rede Wi-Fi salva"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    data = request.get_json()
    ssid = data.get('ssid')
    
    if not ssid:
        return jsonify({'success': False, 'message': 'SSID não fornecido'}), 400
    
    try:
        result = subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid],
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': f'Rede {ssid} removida'})
        else:
            return jsonify({'success': False, 'message': 'Erro ao remover rede'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== ROTAS DO SENSOR DE FILAMENTO ====================

@app.route('/api/filament/status', methods=['GET'])
def filament_status_api():
    """Retorna status do sensor de filamento"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    status = check_filament_sensor()
    return jsonify({
        'success': True,
        'filament': status
    })

if __name__ == '__main__':
    init_db()
    
    # Configurar sensor de filamento
    setup_filament_sensor()
    
    # Iniciar servidor
    try:
        app.run(host='0.0.0.0', port=80, debug=True)
    finally:
        # Limpar GPIO ao encerrar
        if GPIO_AVAILABLE:
            GPIO.cleanup()

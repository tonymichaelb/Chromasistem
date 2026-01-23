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

# Importar threading para lock
import threading

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Lock para sincronizar acesso à porta serial
serial_lock = threading.Lock()

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
SERIAL_PORT = '/dev/ttyACM0'  # Porta serial para placas Arduino/Marlin
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
        filament_status['sensor_enabled'] = False
        return False
    
    try:
        # Limpar configurações anteriores do GPIO
        try:
            GPIO.cleanup()
        except:
            pass
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(FILAMENT_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Configurar callback para detecção de mudança
        GPIO.add_event_detect(FILAMENT_SENSOR_PIN, GPIO.BOTH, 
                            callback=filament_sensor_callback, 
                            bouncetime=300)
        
        filament_status['sensor_enabled'] = True
        print(f"✓ Sensor de filamento configurado no GPIO{FILAMENT_SENSOR_PIN}")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao configurar sensor de filamento: {e}")
        print("   O servidor continuará funcionando sem sensor de filamento")
        filament_status['sensor_enabled'] = False
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
            print(f"✓ Já conectado à impressora em {SERIAL_PORT}")
            return True
        
        # Verificar se a porta existe
        import os
        if not os.path.exists(SERIAL_PORT):
            print(f"✗ ERRO: Porta {SERIAL_PORT} não existe!")
            print("   Portas disponíveis:")
            try:
                import glob
                ports = glob.glob('/dev/tty[AU]*')
                for port in ports:
                    print(f"     - {port}")
            except:
                pass
            return False
        
        print(f"🔌 Tentando conectar à impressora...")
        print(f"   Porta: {SERIAL_PORT}")
        print(f"   Baudrate: {SERIAL_BAUDRATE}")
        print(f"   Timeout: {SERIAL_TIMEOUT}s")
        
        printer_serial = serial.Serial(
            port=SERIAL_PORT,
            baudrate=SERIAL_BAUDRATE,
            timeout=SERIAL_TIMEOUT,
            write_timeout=SERIAL_TIMEOUT,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )
        
        print(f"   Aguardando inicialização da impressora...")
        time.sleep(2)  # Aguardar inicialização
        
        # Tentar enviar comando M115 para verificar conexão
        try:
            printer_serial.write(b'M115\n')
            time.sleep(0.5)
            response = printer_serial.readline().decode('utf-8', errors='ignore').strip()
            if response:
                print(f"   Resposta da impressora: {response[:50]}...")
        except Exception as e:
            print(f"   Aviso ao verificar resposta: {e}")
        
        print(f"✓ Conectado à impressora em {SERIAL_PORT} @ {SERIAL_BAUDRATE} baud")
        return True
    except serial.SerialException as e:
        print(f"✗ ERRO Serial: {e}")
        if 'Permission denied' in str(e):
            print("   SOLUÇÃO: Execute 'sudo usermod -a -G dialout $USER' e faça logout/login")
            print("   OU execute o servidor com sudo")
        elif 'Device or resource busy' in str(e):
            print("   SOLUÇÃO: Outra aplicação está usando a porta. Feche-a primeiro.")
        printer_serial = None
        return False
    except Exception as e:
        print(f"✗ Erro inesperado ao conectar impressora: {type(e).__name__}: {e}")
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
def send_gcode(command, wait_for_ok=True, timeout=None):
    global printer_serial
    
    with serial_lock:  # Garantir acesso exclusivo à porta serial
        try:
            if not printer_serial or not printer_serial.is_open:
                if not connect_printer():
                    return None
            
            # Adicionar newline se não existir
            if not command.endswith('\n'):
                command += '\n'
            
            # Determinar timeout baseado no comando
            if timeout is None:
                cmd = command.strip().upper()
                if cmd.startswith('G28'):  # Home - pode levar até 60s
                    timeout = 60
                elif cmd.startswith('G29'):  # Auto bed leveling - pode levar até 120s
                    timeout = 120
                elif cmd.startswith('M109') or cmd.startswith('M190'):  # Aquecimento - até 300s
                    timeout = 300
                elif cmd.startswith('T'):  # Trocar extrusora - pode levar até 10s
                    timeout = 10
                else:
                    timeout = 5  # Timeout padrão aumentado
            
            # Limpar buffer de entrada antes de enviar
            printer_serial.reset_input_buffer()
            
            # Enviar comando
            printer_serial.write(command.encode())
            printer_serial.flush()
            
            if not wait_for_ok:
                return 'ok'
            
            # Ler resposta (pode ter múltiplas linhas)
            responses = []
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if printer_serial.in_waiting > 0:
                    line = printer_serial.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        responses.append(line)
                        # Se recebeu 'ok', terminou
                        if 'ok' in line.lower():
                            break
                else:
                    time.sleep(0.01)  # Pequena pausa para não saturar CPU
            
            return '\n'.join(responses) if responses else None
        except Exception as e:
            print(f"Erro ao enviar comando '{command.strip()}': {e}")
            return None

# Ler status da impressora
def get_printer_status_serial():
    try:
        status = {
            'connected': printer_serial and printer_serial.is_open,
            'printing': False,
            'progress': 0,
            'bed_temp': 0,
            'nozzle_temp': 0,
            'target_bed_temp': 0,
            'target_nozzle_temp': 0
        }
        
        if not status['connected']:
            return status
        
        # Enviar M105 para ler temperatura (tentar 2 vezes)
        temp_response = None
        for attempt in range(2):
            temp_response = send_gcode('M105')
            if temp_response and 'T:' in temp_response:
                break
            time.sleep(0.1)
        
        # Parse da temperatura (ex: "ok T:210.0 /210.0 B:60.0 /60.0" ou "T:25.0 /0.0 B:24.5 /0.0")
        if temp_response:
            try:
                # Procurar em todas as linhas da resposta
                for line in temp_response.split('\n'):
                    if 'T:' in line:
                        # Extrai temperatura do bico
                        t_match = re.search(r'T:(\d+\.?\d*)\s*/(\d+\.?\d*)', line)
                        if t_match:
                            status['nozzle_temp'] = float(t_match.group(1))
                            status['target_nozzle_temp'] = float(t_match.group(2))
                        
                        # Extrai temperatura da mesa
                        b_match = re.search(r'B:(\d+\.?\d*)\s*/(\d+\.?\d*)', line)
                        if b_match:
                            status['bed_temp'] = float(b_match.group(1))
                            status['target_bed_temp'] = float(b_match.group(2))
                        break
            except Exception as e:
                print(f"Erro ao parsear temperatura: {e}")
                print(f"Resposta: {temp_response}")
        
        # Enviar M27 para ler progresso de impressão
        progress_response = send_gcode('M27')
        
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

@app.route('/terminal')
def terminal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('terminal.html', username=session.get('username'))

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
    
    # Se houver impressão ativa, NÃO consultar serial para evitar conflitos
    if current_job:
        is_printing = True
        current_progress = current_job[1] if current_job else 0
        current_filename = current_job[0] if current_job else ''
        
        status = {
            'connected': printer_serial and printer_serial.is_open,
            'temperature': {
                'bed': 0,  # Não consultar durante impressão
                'nozzle': 0,
                'target_bed': 0,
                'target_nozzle': 0
            },
            'state': 'printing',
            'progress': current_progress,
            'filename': current_filename,
            'time_elapsed': '00:00:00',
            'time_remaining': '00:00:00',
            'filament': check_filament_sensor()
        }
        return jsonify({'success': True, 'status': status})
    
    # Se NÃO houver impressão, consultar status normal
    status_data = get_printer_status_serial()
    filament_info = check_filament_sensor()
    
    status = {
        'connected': status_data['connected'],
        'temperature': {
            'bed': status_data['bed_temp'],
            'nozzle': status_data['nozzle_temp'],
            'target_bed': status_data['target_bed_temp'],
            'target_nozzle': status_data['target_nozzle_temp']
        },
        'state': 'idle',
        'progress': 0,
        'filename': '',
        'time_elapsed': '00:00:00',
        'time_remaining': '00:00:00',
        'filament': filament_info
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

@app.route('/api/printer/connect', methods=['POST'])
def printer_connect():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    if connect_printer():
        return jsonify({'success': True, 'message': 'Impressora conectada com sucesso'})
    else:
        return jsonify({'success': False, 'message': 'Falha ao conectar à impressora'}), 500

@app.route('/api/printer/disconnect', methods=['POST'])
def printer_disconnect():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    disconnect_printer()
    return jsonify({'success': True, 'message': 'Impressora desconectada'})

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

@app.route('/api/printer/gcode', methods=['POST'])
def send_gcode_api():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    data = request.get_json()
    command = data.get('command', '').strip()
    
    if not command:
        return jsonify({'success': False, 'message': 'Comando vazio'}), 400
    
    # Enviar comando para impressora
    response = send_gcode(command)
    
    if response is not None:
        return jsonify({'success': True, 'response': response})
    else:
        return jsonify({'success': False, 'message': 'Sem resposta da impressora'}), 500

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
    filepath = os.path.join(app.config['GCODE_FOLDER'], filename)
    
    # Verificar se impressora está conectada
    if not printer_serial or not printer_serial.is_open:
        if not connect_printer():
            conn.close()
            return jsonify({'success': False, 'message': 'Impressora não conectada'}), 500
    
    # Verificar se arquivo existe
    if not os.path.exists(filepath):
        conn.close()
        return jsonify({'success': False, 'message': 'Arquivo G-code não encontrado'}), 404
    
    # Atualizar contadores
    cursor.execute('''
        UPDATE gcode_files 
        SET last_printed = CURRENT_TIMESTAMP, print_count = print_count + 1
        WHERE id = ?
    ''', (file_id,))
    
    # Criar registro de impressão
    cursor.execute('''
        INSERT INTO print_jobs (user_id, filename, status, progress, started_at)
        VALUES (?, ?, 'printing', 0, CURRENT_TIMESTAMP)
    ''', (session['user_id'], original_name))
    
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Iniciar impressão em thread separada para não bloquear
    import threading
    
    def print_gcode_file():
        try:
            print(f"\n▶️ Iniciando impressão: {original_name}")
            
            # Aguardar um pouco para garantir estabilidade da conexão
            time.sleep(1)
            
            # Comandos de preparação (sem M110 que pode causar reset)
            send_gcode('G21')  # Unidades em mm
            time.sleep(0.2)
            send_gcode('G90')  # Modo absoluto
            time.sleep(0.2)
            send_gcode('M82')  # Extrusor absoluto
            time.sleep(1.0)
            
            print("  Comandos de inicialização enviados")
            
            # Contar total de linhas primeiro
            with open(filepath, 'r') as f:
                total_lines = sum(1 for line in f if line.split(';')[0].strip())
            
            print(f"  Total de comandos: {total_lines}")
            
            # Processar arquivo
            with open(filepath, 'r') as f:
                line_count = 0
                lines_sent = 0
                
                for line in f:
                    # Remover comentários e espaços
                    line = line.split(';')[0].strip()
                    
                    # Pular linhas vazias
                    if not line:
                        line_count += 1
                        continue
                    
                    # Log para comandos importantes
                    cmd_upper = line.upper()
                    if cmd_upper.startswith('G28'):
                        print("  🏠 Executando homing (G28)... pode levar até 60 segundos")
                    elif cmd_upper.startswith('G29'):
                        print("  📐 Executando nivelamento de mesa (G29)... pode levar até 2 minutos")
                    elif cmd_upper.startswith('M109'):
                        print("  🔥 Aquecendo bico e aguardando temperatura...")
                    elif cmd_upper.startswith('M190'):
                        print("  🔥 Aquecendo mesa e aguardando temperatura...")
                    elif cmd_upper.startswith('T'):
                        print(f"  🔧 Selecionando extrusora: {line}")
                    
                    # Enviar comando
                    response = send_gcode(line)
                    
                    # Aguardar mais após comandos importantes
                    if cmd_upper.startswith(('M109', 'M190')):
                        time.sleep(2.0)  # Aquecimento completo - aguardar estabilização
                    elif cmd_upper.startswith(('G28', 'G29', 'T')):
                        time.sleep(0.5)  # Dar tempo para impressora processar
                    
                    if response is None:
                        print(f"✗ Erro ao enviar linha {line_count}: {line}")
                        # Marcar como erro
                        conn_local = sqlite3.connect(DB_NAME)
                        cursor_local = conn_local.cursor()
                        cursor_local.execute('''
                            UPDATE print_jobs 
                            SET status = 'error', completed_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (job_id,))
                        conn_local.commit()
                        conn_local.close()
                        break
                    
                    line_count += 1
                    lines_sent += 1
                    
                    # Atualizar progresso a cada 50 linhas
                    if lines_sent % 50 == 0:
                        progress = (lines_sent / total_lines) * 100
                        conn_local = sqlite3.connect(DB_NAME)
                        cursor_local = conn_local.cursor()
                        cursor_local.execute('''
                            UPDATE print_jobs 
                            SET progress = ?
                            WHERE id = ?
                        ''', (progress, job_id))
                        conn_local.commit()
                        conn_local.close()
                        print(f"  Progresso: {progress:.1f}% ({lines_sent}/{total_lines})")
                    
                    # Pequena pausa para não saturar
                    time.sleep(0.05)
            
            # Marcar como concluído
            conn_local = sqlite3.connect(DB_NAME)
            cursor_local = conn_local.cursor()
            cursor_local.execute('''
                UPDATE print_jobs 
                SET status = 'completed', progress = 100, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (job_id,))
            conn_local.commit()
            conn_local.close()
            
            print(f"✓ Impressão concluída: {lines_sent} linhas enviadas")
            
        except Exception as e:
            print(f"✗ Erro durante impressão: {e}")
            # Marcar como erro
            try:
                conn_local = sqlite3.connect(DB_NAME)
                cursor_local = conn_local.cursor()
                cursor_local.execute('''
                    UPDATE print_jobs 
                    SET status = 'error', completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (job_id,))
                conn_local.commit()
                conn_local.close()
            except:
                pass
    
    # Iniciar thread
    thread = threading.Thread(target=print_gcode_file, daemon=True)
    thread.start()
    
    return jsonify({
        'success': True, 
        'message': f'Iniciando impressão de {original_name}'
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
    print("\n" + "="*50)
    print("🖨️  Chromasistem - Sistema de Monitoramento 3D")
    print("="*50)
    setup_filament_sensor()
    print("="*50 + "\n")
    
    # Iniciar servidor
    try:
        app.run(host='0.0.0.0', port=80, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n⏹️  Servidor interrompido pelo usuário")
    finally:
        # Limpar GPIO ao encerrar
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
                print("✓ GPIO limpo")
            except:
                pass

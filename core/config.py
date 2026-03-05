"""Configuration constants and Flask app creation."""

from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import sys
import subprocess
import shutil
import sys
import threading
from typing import Optional
from collections import deque

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False
    print("⚠️ RPi.GPIO não disponível - sensor de filamento desabilitado")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(os.path.realpath(__file__))))
app = Flask(
    __name__,
    template_folder=os.path.join(_PROJECT_ROOT, 'templates'),
    static_folder=os.path.join(_PROJECT_ROOT, 'static'),
)


def _get_secret_key():
    key = os.environ.get('CHROMA_SECRET_KEY')
    if key:
        return key
    secret_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.chroma_secret')
    if os.path.isfile(secret_file):
        with open(secret_file, 'rb') as f:
            return f.read()
    key = os.urandom(24)
    try:
        with open(secret_file, 'wb') as f:
            f.write(key)
    except OSError:
        pass
    return key


app.secret_key = _get_secret_key()
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

CORS(app, supports_credentials=True)

# ---------------------------------------------------------------------------
# App version
# ---------------------------------------------------------------------------
_APP_VERSION_CACHE = None


def get_app_version() -> str:
    """Retorna a versão do app (env var ou git), com cache."""
    global _APP_VERSION_CACHE
    if _APP_VERSION_CACHE is not None:
        return _APP_VERSION_CACHE

    env_version = os.environ.get('CHROMA_VERSION') or os.environ.get('APP_VERSION')
    if env_version:
        _APP_VERSION_CACHE = env_version.strip()
        return _APP_VERSION_CACHE

    def _find_git_workdir(start_dir: str) -> Optional[str]:
        current = start_dir
        for _ in range(6):
            if os.path.exists(os.path.join(current, '.git')):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        return None

    def _find_git_executable() -> str:
        """Encontra o executável do git mesmo quando o PATH do systemd é restrito."""
        env_git = os.environ.get('GIT_BIN')
        candidates = [env_git] if env_git else []

        which_git = shutil.which('git')
        if which_git:
            candidates.append(which_git)

        candidates.extend([
            '/usr/bin/git',
            '/bin/git',
            '/usr/local/bin/git',
        ])

        for candidate in candidates:
            if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate

        return 'git'

    try:
        start_dir = os.path.dirname(os.path.abspath(__file__))
        git_dir = _find_git_workdir(start_dir) or start_dir

        git_bin = _find_git_executable()

        result = subprocess.run(
            [git_bin, '-C', git_dir, 'describe', '--tags', '--always', '--dirty'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            git_version = (result.stdout or '').strip()
            if git_version:
                _APP_VERSION_CACHE = git_version
                return _APP_VERSION_CACHE

        result = subprocess.run(
            [git_bin, '-C', git_dir, 'rev-parse', '--short', 'HEAD'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            git_hash = (result.stdout or '').strip()
            if git_hash:
                _APP_VERSION_CACHE = git_hash
                return _APP_VERSION_CACHE
    except Exception:
        pass

    try:
        version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'VERSION')
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                v = f.read().strip()
            if v:
                _APP_VERSION_CACHE = v
                return _APP_VERSION_CACHE
    except Exception:
        pass

    _APP_VERSION_CACHE = 'unknown'
    return _APP_VERSION_CACHE


@app.context_processor
def inject_app_version():
    return {'app_version': get_app_version()}


# ---------------------------------------------------------------------------
# Locks & command history
# ---------------------------------------------------------------------------
serial_lock = threading.Lock()
history_lock = threading.Lock()
commands_history = deque(maxlen=100)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DB_NAME = 'croma.db'

# ---------------------------------------------------------------------------
# Upload / G-code
# ---------------------------------------------------------------------------
GCODE_FOLDER = os.path.join(_PROJECT_ROOT, 'gcode_files')
THUMBNAIL_FOLDER = os.path.join(_PROJECT_ROOT, 'static', 'thumbnails')
ALLOWED_EXTENSIONS = {'gcode', 'gco', 'g'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# ---------------------------------------------------------------------------
# Slicer (Orca)
# ---------------------------------------------------------------------------
SLICER_TEMP_FOLDER = os.environ.get('SLICER_TEMP_FOLDER', os.path.join(_PROJECT_ROOT, 'slicer_temp'))
ALLOWED_3D_EXTENSIONS = {'stl', 'obj'}
_DEFAULT_ORCA_MACOS = '/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer'
ORCA_SLICER_PATH = os.environ.get('ORCA_SLICER_PATH', _DEFAULT_ORCA_MACOS if sys.platform == 'darwin' else 'orca-slicer')
ORCA_DATADIR = os.environ.get('ORCA_DATADIR', '')
SLICER_TIMEOUT_SEC = int(os.environ.get('SLICER_TIMEOUT_SEC', '600'))

# ---------------------------------------------------------------------------
# Folder creation
# ---------------------------------------------------------------------------
if not os.path.exists(GCODE_FOLDER):
    os.makedirs(GCODE_FOLDER)
if not os.path.exists(THUMBNAIL_FOLDER):
    os.makedirs(THUMBNAIL_FOLDER)
if not os.path.exists(SLICER_TEMP_FOLDER):
    os.makedirs(SLICER_TEMP_FOLDER)

app.config['GCODE_FOLDER'] = GCODE_FOLDER
app.config['THUMBNAIL_FOLDER'] = THUMBNAIL_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['SLICER_TEMP_FOLDER'] = SLICER_TEMP_FOLDER

# ---------------------------------------------------------------------------
# React frontend
# ---------------------------------------------------------------------------
REACT_DIST = os.path.join(_PROJECT_ROOT, 'front-react', 'dist')
USE_REACT_APP = os.path.isfile(os.path.join(REACT_DIST, 'index.html'))

# ---------------------------------------------------------------------------
# Bed dimensions (mm)
# ---------------------------------------------------------------------------
BED_WIDTH_MM = float(os.environ.get('BED_WIDTH_MM', '220'))
BED_DEPTH_MM = float(os.environ.get('BED_DEPTH_MM', '220'))

# ---------------------------------------------------------------------------
# Pause / park
# ---------------------------------------------------------------------------
PAUSE_RETRACT_MM = float(os.environ.get('PAUSE_RETRACT_MM', '5'))
PAUSE_Z_LIFT_MM = float(os.environ.get('PAUSE_Z_LIFT_MM', '10'))
PAUSE_PARK_X = float(os.environ.get('PAUSE_PARK_X', '0'))
PAUSE_PARK_Y = float(os.environ.get('PAUSE_PARK_Y', '0'))
TEMP_REHEAT_MARGIN = 5

# ---------------------------------------------------------------------------
# Serial
# ---------------------------------------------------------------------------
SERIAL_PORT = '/dev/ttyACM0'
SERIAL_BAUDRATE = 115200
SERIAL_TIMEOUT = 2

# ---------------------------------------------------------------------------
# Filament sensor
# ---------------------------------------------------------------------------
FILAMENT_SENSOR_PIN = int(os.environ.get('FILAMENT_SENSOR_PIN') or '17')

_filament_mode_raw = (os.environ.get('FILAMENT_SENSOR_MODE') or 'gpio').strip().lower()
if _filament_mode_raw in ('old', 'raspberry', 'rpi', 'legacy'):
    _filament_mode_raw = 'gpio'
FILAMENT_SENSOR_MODE = _filament_mode_raw
FILAMENT_CHECK_INTERVAL_SEC = float(os.environ.get('FILAMENT_CHECK_INTERVAL_SEC') or '2.0')
FILAMENT_CHECK_INTERVAL_PRINT_SEC = float(os.environ.get('FILAMENT_CHECK_INTERVAL_PRINT_SEC') or '15.0')
MARLIN_FILAMENT_INVERT = (os.environ.get('MARLIN_FILAMENT_INVERT') or '0').strip() in ('1', 'true', 'True', 'yes', 'YES')
FILAMENT_M119_DURING_PRINT = (os.environ.get('FILAMENT_M119_DURING_PRINT') or '0').strip() in ('1', 'true', 'True', 'yes', 'YES')

# ---------------------------------------------------------------------------
# Temperature polling during print
# ---------------------------------------------------------------------------
TEMP_CHECK_INTERVAL_PRINT_SEC = float(os.environ.get('TEMP_CHECK_INTERVAL_PRINT_SEC') or '5.0')

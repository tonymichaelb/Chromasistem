"""Chromasistem — entry point."""
from core.config import app, USE_REACT_APP, GPIO_AVAILABLE
from core.database import init_db
from core.filament import setup_filament_sensor
from routes import register_blueprints

register_blueprints(app)

if __name__ == '__main__':
    init_db()

    print("\n" + "=" * 50)
    print("🖨️  Chromasistem - Sistema de Monitoramento 3D")
    print("=" * 50)
    if USE_REACT_APP:
        print("   Frontend: React (front-react/dist)")
    else:
        print("   Frontend: Templates HTML (build React não encontrado em front-react/dist)")
    print("=" * 50)
    setup_filament_sensor()
    print("=" * 50 + "\n")

    try:
        app.run(host='0.0.0.0', port=80, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n⏹️  Servidor interrompido pelo usuário")
    finally:
        if GPIO_AVAILABLE:
            try:
                from core.config import GPIO
                GPIO.cleanup()
                print("✓ GPIO limpo")
            except:
                pass

"""Chromasistem — entry point."""
from core.config import app, USE_REACT_APP, GPIO_AVAILABLE, REACT_DIST
from core.database import init_db
from core.filament import setup_filament_sensor
from routes import register_blueprints
import os

register_blueprints(app)

if __name__ == '__main__':
    init_db()

    print("\n" + "=" * 50)
    print("🖨️  Chromasistem - Sistema de Monitoramento 3D")
    print("=" * 50)
    if USE_REACT_APP:
        idx = os.path.join(REACT_DIST, "index.html")
        print("   Frontend: React (front-react/dist)")
        print(f"   REACT_DIST: {os.path.abspath(REACT_DIST)}")
        print(f"   index.html existe: {os.path.isfile(idx)}")
    else:
        print("   Frontend: Templates HTML (build React não encontrado em front-react/dist)")
        print(f"   REACT_DIST verificado: {os.path.abspath(REACT_DIST)}")
        print(f"   index.html existe: {os.path.isfile(os.path.join(REACT_DIST, 'index.html'))}")
    print("=" * 50)
    setup_filament_sensor()
    print("=" * 50 + "\n")

    port = int(os.environ.get('PORT', '80'))
    print(f"   Escutando em 0.0.0.0:{port} (use PORT=5000 para testar sem root)")
    print("   No próprio Raspberry, teste: curl -I http://127.0.0.1")
    print("=" * 50 + "\n")

    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except OSError as e:
        if e.errno == 98 or 'Address already in use' in str(e):
            print("\n⚠️  Porta {} em uso ou sem permissão. Tente: PORT=5000 ./scripts/run-prod.sh".format(port))
        elif e.errno == 13 or 'Permission denied' in str(e):
            print("\n⚠️  Porta {} requer root. Execute: sudo ./scripts/run-prod.sh".format(port))
        else:
            print("\n⚠️  Erro ao iniciar servidor:", e)
        raise
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

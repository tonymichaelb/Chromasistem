"""Route blueprints registration."""
from routes.auth import auth_bp
from routes.pages import pages_bp
from routes.printer_api import printer_bp
from routes.files_api import files_bp
from routes.wifi_api import wifi_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(printer_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(wifi_bp)

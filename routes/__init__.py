"""Blueprints HTTP de New Records agrupados por dominio."""

from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.carrito import carrito_bp
from routes.catalogo import catalogo_bp
from routes.pagos import pagos_bp
from routes.pedidos import pedidos_bp

BLUEPRINTS = (
    catalogo_bp,
    auth_bp,
    carrito_bp,
    pedidos_bp,
    pagos_bp,
    admin_bp,
)


def registrar_blueprints(app):
    """Registra todos los módulos HTTP sobre una instancia Flask."""
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)

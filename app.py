"""Fábrica y punto de entrada de la aplicación New Records."""

import click
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from auth import obtener_usuario_actual
from cart import obtener_carrito_sesion
from config import Config
from extensions import csrf, migrate
from mailer import mail
from models import Categoria, db
from routes import registrar_blueprints
from validators import es_url_segura


def _registrar_contexto_plantillas(app: Flask) -> None:
    """Expone navegación y sesión a todas las plantillas Jinja."""

    @app.context_processor
    def inyectar_contexto_usuario():
        usuario = obtener_usuario_actual()
        carrito = obtener_carrito_sesion()
        total_items = sum(
            cantidad
            for cantidad in carrito.values()
            if isinstance(cantidad, int)
            and not isinstance(cantidad, bool)
            and cantidad > 0
        )
        categorias_globales = (
            Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
        )

        iniciales = ""
        if usuario and usuario.nombre:
            partes = usuario.nombre.strip().split()
            if len(partes) >= 2:
                iniciales = f"{partes[0][0]}{partes[1][0]}".upper()
            elif len(partes) == 1 and len(partes[0]) >= 2:
                iniciales = partes[0][:2].upper()
            elif partes:
                iniciales = partes[0][0].upper()

        return {
            "usuario_actual": usuario,
            "usuario_iniciales": iniciales or "NR",
            "esta_autenticado": usuario is not None,
            "es_admin": usuario is not None and usuario.rol == "administrador",
            "es_cliente": usuario is not None and usuario.rol == "cliente",
            "categorias_globales": categorias_globales,
            "total_items_carrito": total_items,
        }


def _registrar_seguridad_y_errores(app: Flask) -> None:
    """Configura cabeceras, navegación HTMX y manejadores de error."""

    @app.after_request
    def agregar_cabeceras_seguridad(response):
        if (
            request.headers.get("HX-Request") == "true"
            and response.status_code in {301, 302, 303, 307, 308}
            and response.headers.get("Location")
        ):
            destino = response.headers.pop("Location")
            response.status_code = 204
            response.headers["HX-Location"] = destino

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    @app.errorhandler(403)
    def acceso_denegado(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(CSRFError)
    def csrf_invalido(_error):
        flash("La solicitud expiró o no es válida. Inténtalo nuevamente.", "error")
        destino = (
            request.referrer
            if es_url_segura(request.referrer)
            else url_for("catalogo.inicio")
        )
        return redirect(destino)

    @app.errorhandler(404)
    def pagina_no_encontrada(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def error_interno(_error):
        db.session.rollback()
        return render_template("errors/500.html"), 500


def _registrar_comandos(app: Flask) -> None:
    """Registra utilidades CLI de diagnóstico y respaldos."""

    @app.cli.command("check-db")
    def check_db():
        """Comprueba la conexión sin modificar PostgreSQL."""
        try:
            resultado = db.session.execute(
                text(
                    "SELECT current_user, current_database(), "
                    "pg_encoding_to_char(encoding), pg_get_userbyid(datdba) "
                    "FROM pg_database WHERE datname = current_database()"
                )
            ).one()
            click.echo("Conexión con PostgreSQL correcta.")
            click.echo(f"Usuario: {resultado[0]}")
            click.echo(f"Base de datos: {resultado[1]}")
            click.echo(f"Codificación: {resultado[2]}")
            click.echo(f"Propietario: {resultado[3]}")
        except SQLAlchemyError as error:
            db.session.rollback()
            raise click.ClickException(
                "No fue posible conectar con PostgreSQL. Revisa el archivo .env."
            ) from error

    @app.cli.command("crear-backup")
    @click.option(
        "--formato",
        type=click.Choice(["plain", "custom"], case_sensitive=False),
        default="plain",
        help="Formato de salida: 'plain' (.sql) o 'custom' (.dump).",
    )
    def crear_backup(formato):
        """Genera un respaldo PostgreSQL en la carpeta backups/."""
        from backup_manager import ejecutar_backup_pg_dump

        click.echo(f"Iniciando respaldo en formato {formato.upper()}...")
        exito, resultado, tamano = ejecutar_backup_pg_dump(formato=formato)
        if exito:
            click.echo("¡Respaldo creado exitosamente!")
            click.echo(f"Archivo: {resultado}")
            click.echo(f"Tamaño: {round(tamano / 1024, 2)} KB")
            return
        click.echo(f"Aviso: {resultado}")
        click.echo("Consulta docs/SEGURIDAD_Y_RESPALDOS.md para el respaldo manual.")

    @app.cli.command("verificar-restauracion")
    def verificar_restauracion():
        """Restaura un dump temporal y valida su contenido."""
        from backup_manager import verificar_restauracion_completa

        click.echo("Creando y restaurando una copia temporal de verificación...")
        exito, mensaje, resumen = verificar_restauracion_completa()
        if not exito:
            raise click.ClickException(mensaje)
        click.echo(mensaje)
        click.echo(
            f"Tablas: {resumen['tablas']} | "
            f"Categorías: {resumen['categorias']} | Discos: {resumen['discos']}"
        )


def create_app(config_object=Config, config_overrides: dict | None = None) -> Flask:
    """Construye una instancia Flask configurada, testeable y desacoplada."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    if config_overrides:
        app.config.update(config_overrides)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "Configura SECRET_KEY en el archivo .env antes de iniciar Flask."
        )

    db.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db, directory="alembic")

    registrar_blueprints(app)
    _registrar_contexto_plantillas(app)
    _registrar_seguridad_y_errores(app)
    _registrar_comandos(app)
    return app


# Compatibilidad con `flask --app app`, Gunicorn y las pruebas existentes.
app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])

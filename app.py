"""Punto de entrada de la aplicación New Records."""

import click
from flask import Flask, render_template
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from config import Config
from models import db


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


@app.route("/")
def inicio():
    """Muestra la portada de New Records."""
    return render_template("index.html")


@app.route("/categorias")
def categorias():
    """Muestra temporalmente las categorías del prototipo."""
    return render_template("categorias.html")


@app.route("/productos")
def productos():
    """Muestra temporalmente el catálogo estático del prototipo."""
    return render_template("productos.html")


@app.route("/contacto")
def contacto():
    """Muestra el formulario de contacto del prototipo."""
    return render_template("contacto.html")


@app.errorhandler(403)
def acceso_denegado(_error):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def pagina_no_encontrada(_error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def error_interno(_error):
    db.session.rollback()
    return render_template("errors/500.html"), 500


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


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])

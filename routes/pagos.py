"""Rutas de métodos de pago simulados y verificación por PIN."""

from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from auth import obtener_usuario_actual, rol_requerido
from mailer import enviar_pin
from models import VerificacionTarjeta, db
from payments import (
    MARCAS_VALIDAS,
    crear_verificacion,
    desactivar_metodo_pago,
    establecer_predeterminado,
    numero_tarjeta_valido,
    obtener_metodos_pago_activos,
    vencimiento_tarjeta_valido,
    verificar_pin,
)
from validators import validar_titular_tarjeta

pagos_bp = Blueprint("pagos", __name__)


@pagos_bp.route("/pago/metodos")
@rol_requerido("cliente")
def pago_metodos():
    """Muestra los métodos de pago verificados del cliente."""
    metodos = obtener_metodos_pago_activos(session["usuario_id"])
    return render_template("pago/metodos.html", metodos=metodos)


@pagos_bp.route("/pago/agregar", methods=["GET", "POST"])
@rol_requerido("cliente")
def pago_agregar():
    """Formulario de registro de nueva tarjeta; genera y envía el PIN de verificación."""
    if request.method == "POST":
        titular = request.form.get("titular", "").strip()
        marca = request.form.get("marca", "").upper().strip()
        numero_completo = (
            request.form.get("numero", "").replace(" ", "").replace("-", "")
        )
        mes = request.form.get("mes_vencimiento", "").strip()
        anio = request.form.get("anio_vencimiento", "").strip()

        errores = []
        error_titular = validar_titular_tarjeta(titular)
        if error_titular:
            errores.append(error_titular)
        if marca not in MARCAS_VALIDAS:
            errores.append("Selecciona una marca de tarjeta válida.")
        if not numero_tarjeta_valido(numero_completo):
            errores.append("El número de tarjeta no es válido.")
        try:
            mes_int = int(mes)
            anio_int = int(anio)
            if not (1 <= mes_int <= 12):
                raise ValueError
            if not vencimiento_tarjeta_valido(mes_int, anio_int):
                raise ValueError
        except (ValueError, TypeError):
            errores.append("Ingresa una fecha de vencimiento vigente y válida.")

        if errores:
            for e in errores:
                flash(e, "error")
            return render_template(
                "pago/agregar.html",
                marcas=MARCAS_VALIDAS,
                titular=titular,
                marca=marca,
                mes=mes,
                anio=anio,
                anio_actual=date.today().year,
                mes_actual=date.today().month,
            )

        ultimos4 = numero_completo[-4:]
        datos = {
            "marca": marca,
            "ultimos4": ultimos4,
            "titular": titular,
            "mes_vencimiento": mes_int,
            "anio_vencimiento": anio_int,
        }

        try:
            verificacion, pin = crear_verificacion(session["usuario_id"], datos)
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
            return render_template(
                "pago/agregar.html",
                marcas=MARCAS_VALIDAS,
                titular=titular,
                marca=marca,
                mes=mes,
                anio=anio,
                anio_actual=date.today().year,
                mes_actual=date.today().month,
            )
        except Exception:
            db.session.rollback()
            flash("Error al procesar la tarjeta. Inténtalo de nuevo.", "error")
            return render_template(
                "pago/agregar.html",
                marcas=MARCAS_VALIDAS,
                anio_actual=date.today().year,
                mes_actual=date.today().month,
            )

        usuario = obtener_usuario_actual()
        enviado = enviar_pin(
            usuario.email,
            usuario.nombre,
            pin,
            url_for(
                "pagos.pago_verificar",
                token=verificacion.token_verificacion,
                _external=True,
            ),
        )

        if enviado:
            flash(
                f"Se envió un código de 6 dígitos a {usuario.email}. Ingresa el código para confirmar tu tarjeta.",
                "info",
            )
        else:
            flash(
                f"Tu PIN de verificación es: {pin}",
                "warning",
            )

        return redirect(
            url_for("pagos.pago_verificar", token=verificacion.token_verificacion)
        )

    return render_template(
        "pago/agregar.html",
        marcas=MARCAS_VALIDAS,
        anio_actual=date.today().year,
        mes_actual=date.today().month,
    )


@pagos_bp.route("/pago/verificar/<token>", methods=["GET", "POST"])
@rol_requerido("cliente")
def pago_verificar(token):
    """Formulario de ingreso del PIN para confirmar el registro de la tarjeta."""
    verificacion = VerificacionTarjeta.query.filter_by(
        token_verificacion=token, usuario_id=session["usuario_id"]
    ).first_or_404()

    if verificacion.verificada:
        flash("Esta verificación ya fue completada.", "info")
        return redirect(url_for("pagos.pago_metodos"))

    if request.method == "POST":
        pin_ingresado = request.form.get("pin", "").strip()
        exito, resultado = verificar_pin(token, pin_ingresado)

        if exito:
            flash(
                "¡Tarjeta verificada y agregada correctamente a tus métodos de pago!",
                "success",
            )
            return redirect(url_for("pagos.pago_metodos"))
        else:
            flash(resultado, "error")

    intentos_restantes = max(0, 3 - verificacion.intentos)
    return render_template(
        "pago/verificar_pin.html",
        token=token,
        verificacion=verificacion,
        intentos_restantes=intentos_restantes,
    )


@pagos_bp.route("/pago/predeterminado/<int:metodo_id>", methods=["POST"])
@rol_requerido("cliente")
def pago_predeterminado(metodo_id):
    """Establece un método de pago como predeterminado del cliente."""
    if establecer_predeterminado(metodo_id, session["usuario_id"]):
        flash("Método de pago predeterminado actualizado.", "success")
    else:
        flash("No se encontró el método de pago indicado.", "error")
    return redirect(url_for("pagos.pago_metodos"))


@pagos_bp.route("/pago/eliminar/<int:metodo_id>", methods=["POST"])
@rol_requerido("cliente")
def pago_eliminar(metodo_id):
    """Desactiva (eliminación lógica) un método de pago del cliente."""
    if desactivar_metodo_pago(metodo_id, session["usuario_id"]):
        flash("Método de pago eliminado correctamente.", "info")
    else:
        flash("No se encontró el método de pago indicado.", "error")
    return redirect(url_for("pagos.pago_metodos"))

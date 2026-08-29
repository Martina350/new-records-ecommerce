"""Módulo de lógica de negocio para métodos de pago y verificación por PIN en New Records."""

import random
import secrets
import string
from datetime import timedelta

from werkzeug.security import check_password_hash, generate_password_hash

from models import MetodoPago, VerificacionTarjeta, ahora_utc, db

# Constantes de negocio
DURACION_PIN_MINUTOS = 5
MAX_INTENTOS_PIN = 3
MARCAS_VALIDAS = ("VISA", "MASTERCARD", "AMEX")


def generar_token_tarjeta():
    """Genera un token único UUID para identificar la tarjeta sin almacenar su número."""
    return secrets.token_hex(24)


def generar_pin_temporal():
    """Genera un PIN numérico de 6 dígitos como cadena de texto."""
    return "".join(random.choices(string.digits, k=6))


def crear_verificacion(usuario_id, datos_tarjeta):
    """Persiste una VerificacionTarjeta pendiente con el PIN hasheado.

    No se guarda el número completo de tarjeta; solo los últimos 4 dígitos,
    la marca, el titular y las fechas de vencimiento.

    Retorna (verificacion, pin_plano) donde pin_plano se usa únicamente para
    enviar por correo y nunca se persiste.
    """
    pin = generar_pin_temporal()
    pin_hash = generate_password_hash(pin)
    token_verificacion = secrets.token_urlsafe(32)
    token_tarjeta = generar_token_tarjeta()

    ahora = ahora_utc()
    expiracion = ahora + timedelta(minutes=DURACION_PIN_MINUTOS)

    verificacion = VerificacionTarjeta(
        usuario_id=usuario_id,
        token_verificacion=token_verificacion,
        pin_hash=pin_hash,
        token_tarjeta=token_tarjeta,
        marca=datos_tarjeta["marca"].upper(),
        ultimos4=datos_tarjeta["ultimos4"],
        titular=datos_tarjeta["titular"].strip(),
        mes_vencimiento=int(datos_tarjeta["mes_vencimiento"]),
        anio_vencimiento=int(datos_tarjeta["anio_vencimiento"]),
        fecha_creacion=ahora,
        fecha_expiracion=expiracion,
        intentos=0,
        verificada=False,
    )

    db.session.add(verificacion)
    db.session.commit()
    return verificacion, pin


def verificar_pin(token_verificacion, pin_ingresado):
    """Valida el PIN ingresado contra la verificación pendiente.

    Flujo:
    1. Busca la verificación por token.
    2. Valida que no esté ya utilizada, expirada ni bloqueada por intentos.
    3. Si el PIN es incorrecto, incrementa el contador de intentos.
    4. Si el PIN es correcto, crea el MetodoPago definitivo y marca la verificación como completada.

    Retorna (True, metodo_pago) en éxito, o (False, mensaje_error) en fallo.
    """
    verificacion = VerificacionTarjeta.query.filter_by(
        token_verificacion=token_verificacion
    ).first()

    if verificacion is None:
        return False, "El enlace de verificación no es válido."

    if verificacion.verificada:
        return False, "Esta verificación ya fue completada anteriormente."

    if ahora_utc() > verificacion.fecha_expiracion:
        return False, "El código de verificación ha expirado. Inicia el proceso nuevamente."

    if verificacion.intentos >= MAX_INTENTOS_PIN:
        return False, "Se alcanzó el número máximo de intentos. Inicia el proceso nuevamente."

    if not check_password_hash(verificacion.pin_hash, pin_ingresado):
        verificacion.intentos += 1
        db.session.commit()
        restantes = MAX_INTENTOS_PIN - verificacion.intentos
        if restantes <= 0:
            return False, "Código incorrecto. No quedan intentos disponibles. Inicia el proceso nuevamente."
        return False, f"Código incorrecto. Te quedan {restantes} intento(s)."

    # PIN correcto: crear el MetodoPago definitivo
    # Si ya existe un método predeterminado, el nuevo no será predeterminado
    tiene_predeterminado = MetodoPago.query.filter_by(
        usuario_id=verificacion.usuario_id,
        activo=True,
        predeterminado=True,
    ).first() is not None

    metodo = MetodoPago(
        usuario_id=verificacion.usuario_id,
        token=verificacion.token_tarjeta,
        marca=verificacion.marca,
        ultimos4=verificacion.ultimos4,
        titular=verificacion.titular,
        mes_vencimiento=verificacion.mes_vencimiento,
        anio_vencimiento=verificacion.anio_vencimiento,
        predeterminado=not tiene_predeterminado,
        activo=True,
        fecha_verificacion=ahora_utc(),
    )
    db.session.add(metodo)

    verificacion.verificada = True
    db.session.commit()
    return True, metodo


def obtener_metodos_pago_activos(usuario_id):
    """Retorna los métodos de pago verificados y activos del usuario."""
    return (
        MetodoPago.query.filter_by(usuario_id=usuario_id, activo=True)
        .order_by(MetodoPago.predeterminado.desc(), MetodoPago.fecha_verificacion.desc())
        .all()
    )


def desactivar_metodo_pago(metodo_id, usuario_id):
    """Desactiva un método de pago verificando que pertenezca al usuario.

    Si el método era el predeterminado, promueve automáticamente el siguiente activo.
    Retorna True si se desactivó, False si no se encontró o no pertenece al usuario.
    """
    metodo = MetodoPago.query.filter_by(id=metodo_id, usuario_id=usuario_id, activo=True).first()
    if not metodo:
        return False

    era_predeterminado = metodo.predeterminado
    metodo.activo = False
    metodo.predeterminado = False
    db.session.flush()

    # Si era el predeterminado, promover automáticamente el siguiente activo
    if era_predeterminado:
        siguiente = MetodoPago.query.filter_by(
            usuario_id=usuario_id, activo=True
        ).order_by(MetodoPago.fecha_verificacion.desc()).first()
        if siguiente:
            siguiente.predeterminado = True

    db.session.commit()
    return True


def establecer_predeterminado(metodo_id, usuario_id):
    """Desmarca todos los métodos del usuario y marca el seleccionado como predeterminado.

    Retorna True si se realizó el cambio, False si el método no pertenece al usuario.
    """
    metodo = MetodoPago.query.filter_by(id=metodo_id, usuario_id=usuario_id, activo=True).first()
    if not metodo:
        return False

    MetodoPago.query.filter_by(usuario_id=usuario_id, activo=True).update(
        {"predeterminado": False}
    )
    metodo.predeterminado = True
    db.session.commit()
    return True

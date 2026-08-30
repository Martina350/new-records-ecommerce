"""Servicios y lógica transaccional para pedidos y pagos en New Records."""

import secrets
from datetime import datetime, timezone

from sqlalchemy import text

from cart import obtener_carrito_sesion, vaciar_carrito
from models import (
    DetallePedido,
    Disco,
    MetodoPago,
    Pedido,
    TransaccionPago,
    ahora_utc,
    db,
)
from payments import vencimiento_tarjeta_valido


def generar_numero_pedido():
    """Genera un identificador único para el pedido con formato NR-YYYYMMDD-XXXX."""
    fecha_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    sufijo = secrets.token_hex(2).upper()
    return f"NR-{fecha_str}-{sufijo}"


def generar_referencia_pago():
    """Genera un código único para la transacción de pago simulada."""
    return f"TXN-{secrets.token_hex(16).upper()}"


def procesar_checkout(cliente_id, metodo_pago_id):
    """Convierte el carrito en un pedido persistente con detalles históricos y cobro simulado.

    Flujo transaccional:
    1. Valida que el carrito tenga productos.
    2. Valida que el método de pago exista, esté activo y pertenezca al cliente.
    3. Revalida que cada disco exista, esté activo y tenga stock suficiente.
    4. Crea el Pedido en estado 'PENDIENTE'.
    5. Crea los DetallePedido con copias históricas de datos y precio final polimórfico.
    6. Crea la TransaccionPago en estado 'PENDIENTE'.
    7. Realiza commit en PostgreSQL y vacía el carrito en la sesión.

    Retorna (True, pedido) en éxito o (False, mensaje_error) en fallo.
    """
    carrito = obtener_carrito_sesion()
    if not carrito:
        return False, "Tu carrito de compras está vacío."

    # Validar método de pago
    metodo_pago = MetodoPago.query.filter_by(
        id=metodo_pago_id, usuario_id=cliente_id, activo=True
    ).first()

    if not metodo_pago:
        return False, "El método de pago seleccionado no es válido o no está disponible."
    if not vencimiento_tarjeta_valido(
        metodo_pago.mes_vencimiento, metodo_pago.anio_vencimiento
    ):
        return False, "El método de pago seleccionado está vencido."

    # Preparar elementos y validar existencias
    detalles_a_crear = []
    total_pedido = 0

    pedido = None
    try:
        from pdf_generator import generar_pdf_pedido

        for clave_id, cantidad in list(carrito.items()):
            try:
                disco_id = int(clave_id)
            except (ValueError, TypeError):
                continue

            disco = db.session.get(Disco, disco_id)
            if not disco or not disco.activo:
                db.session.rollback()
                return False, f"El disco '{disco.album if disco else 'desconocido'}' ya no está disponible."

            if disco.stock < cantidad:
                db.session.rollback()
                return False, f"Stock insuficiente para '{disco.album}' (disponible: {disco.stock} unidades)."

            precio_unitario = disco.precio_final()
            subtotal = precio_unitario * cantidad
            total_pedido += subtotal

            detalles_a_crear.append(
                {
                    "disco_id": disco.id,
                    "album": disco.album,
                    "artista": disco.artista,
                    "formato": disco.formato,
                    "precio_unitario": precio_unitario,
                    "cantidad": cantidad,
                }
            )

        if not detalles_a_crear:
            db.session.rollback()
            return False, "No hay productos válidos en el carrito."

        # Generar número único de pedido
        numero_pedido = generar_numero_pedido()
        while Pedido.query.filter_by(numero=numero_pedido).first() is not None:
            numero_pedido = generar_numero_pedido()

        # Crear entidad Pedido
        pedido = Pedido(
            numero=numero_pedido,
            cliente_id=cliente_id,
            metodo_pago_id=metodo_pago.id,
            estado="PENDIENTE",
            total=total_pedido,
            fecha_creacion=ahora_utc(),
        )
        db.session.add(pedido)
        db.session.flush()  # Obtener pedido.id

        # Crear líneas históricas DetallePedido
        for d in detalles_a_crear:
            detalle = DetallePedido(
                pedido_id=pedido.id,
                disco_id=d["disco_id"],
                album=d["album"],
                artista=d["artista"],
                formato=d["formato"],
                precio_unitario=d["precio_unitario"],
                cantidad=d["cantidad"],
            )
            db.session.add(detalle)

        # Crear registro de cobro simulado
        transaccion = TransaccionPago(
            pedido_id=pedido.id,
            metodo_pago_id=metodo_pago.id,
            monto=total_pedido,
            estado="PENDIENTE",
            referencia=generar_referencia_pago(),
            fecha_procesamiento=ahora_utc(),
        )
        db.session.add(transaccion)

        db.session.flush()
        generar_pdf_pedido(pedido, tipo="COMPROBANTE_PENDIENTE")
        db.session.commit()

        # Vaciar carrito de la sesión tras éxito en base de datos
        vaciar_carrito()
        return True, pedido

    except Exception:
        db.session.rollback()
        if pedido is not None:
            from pdf_generator import eliminar_pdf_pedido

            eliminar_pdf_pedido(pedido, "COMPROBANTE_PENDIENTE")
        return False, "Ocurrió un error inesperado al procesar el pedido. Inténtalo nuevamente."


def obtener_pedidos_cliente(cliente_id):
    """Retorna los pedidos de un cliente ordenados por fecha descendente."""
    return (
        Pedido.query.filter_by(cliente_id=cliente_id)
        .order_by(Pedido.fecha_creacion.desc())
        .all()
    )


def obtener_pedido_por_numero(numero, usuario):
    """Recupera un pedido por su número público verificando permisos de acceso."""
    pedido = Pedido.query.filter_by(numero=numero).first()
    if not pedido:
        return None

    # El propietario o un administrador tienen acceso permitido
    if pedido.cliente_id == usuario.id or usuario.es_administrador():
        return pedido

    return None


def obtener_estadisticas_dashboard():
    """Calcula métricas clave para el panel de control administrativo."""
    from models import Categoria

    total_discos = Disco.query.count()
    discos_activos = Disco.query.filter_by(activo=True).count()
    total_categorias = Categoria.query.filter_by(activo=True).count()
    pedidos_pendientes = Pedido.query.filter_by(estado="PENDIENTE").count()
    pedidos_aprobados = Pedido.query.filter_by(estado="APROBADO").count()
    pedidos_rechazados = Pedido.query.filter_by(estado="RECHAZADO").count()
    total_facturado = (
        db.session.query(db.func.sum(Pedido.total))
        .filter(Pedido.estado == "APROBADO")
        .scalar()
        or 0
    )

    return {
        "total_discos": total_discos,
        "discos_activos": discos_activos,
        "total_categorias": total_categorias,
        "pedidos_pendientes": pedidos_pendientes,
        "pedidos_aprobados": pedidos_aprobados,
        "pedidos_rechazados": pedidos_rechazados,
        "total_facturado": float(total_facturado),
    }


def obtener_pedidos_admin(estado=None):
    """Consulta la bandeja de pedidos con filtro opcional por estado."""
    query = Pedido.query
    if estado and estado.upper() in ("PENDIENTE", "APROBADO", "RECHAZADO"):
        query = query.filter_by(estado=estado.upper())
    return query.order_by(Pedido.fecha_creacion.desc()).all()


def aprobar_pedido(numero, admin_id):
    """Aprueba en PostgreSQL, genera la factura y confirma todo en una transacción.

    Flujo:
    1. Verifica que el pedido esté en estado 'PENDIENTE'.
    2. Revalida que cada disco en el pedido tenga existencias suficientes.
    3. Descuenta las unidades del inventario físico.
    4. Cambia el estado del pedido a 'APROBADO' y registra al revisor.
    5. Cambia el estado de TransaccionPago a 'APROBADA'.
    6. Emite la 'FACTURA_FINAL' y notifica al cliente por correo.
    """
    from mailer import notificar_cambio_estado
    from pdf_generator import eliminar_pdf_pedido, generar_pdf_pedido

    pedido = None
    try:
        resultado = db.session.execute(
            text(
                "CALL aprobar_pedido_new_records("
                ":numero, :admin_id, false, '')"
            ),
            {"numero": numero, "admin_id": admin_id},
        ).one()
        exito, mensaje = bool(resultado[0]), resultado[1]
        if not exito:
            # El procedimiento no modifica datos cuando retorna un error de negocio.
            # Confirmar libera sus bloqueos sin alterar el pedido.
            db.session.commit()
            return False, mensaje

        db.session.expire_all()
        pedido = Pedido.query.filter_by(numero=numero).first()
        generar_pdf_pedido(pedido, tipo="FACTURA_FINAL")
        db.session.commit()

        # Notificar por correo
        notificar_cambio_estado(pedido)
        return True, (
            f"Pedido {pedido.numero} aprobado exitosamente. "
            "Stock actualizado y Factura Oficial emitida."
        )

    except Exception:
        db.session.rollback()
        if pedido is not None:
            eliminar_pdf_pedido(pedido, "FACTURA_FINAL")
        return False, "Ocurrió un error inesperado al procesar la aprobación del pedido."


def rechazar_pedido(numero, admin_id, motivo):
    """Ejecuta el rechazo de un pedido registrando el motivo obligatorio sin alterar inventario."""
    from mailer import notificar_cambio_estado

    if not motivo or not motivo.strip():
        return False, "Debes ingresar un motivo explícito para rechazar el pedido."

    try:
        pedido = (
            Pedido.query.filter_by(numero=numero)
            .with_for_update()
            .first()
        )
        if not pedido:
            db.session.rollback()
            return False, "Pedido no encontrado."

        if pedido.estado != "PENDIENTE":
            db.session.rollback()
            return False, (
                "El pedido ya no se encuentra pendiente "
                f"(Estado actual: {pedido.estado})."
            )

        pedido.estado = "RECHAZADO"
        pedido.motivo_rechazo = motivo.strip()
        pedido.administrador_revisor_id = admin_id
        pedido.fecha_revision = ahora_utc()

        if pedido.transaccion_pago:
            pedido.transaccion_pago.estado = "RECHAZADA"
            pedido.transaccion_pago.fecha_procesamiento = ahora_utc()

        db.session.commit()

        # Notificar por correo
        notificar_cambio_estado(pedido)
        return True, f"Pedido {pedido.numero} rechazado correctamente."

    except Exception:
        db.session.rollback()
        return False, "Ocurrió un error inesperado al rechazar el pedido."


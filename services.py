"""Servicios y lógica transaccional para pedidos y pagos en New Records."""

import secrets
from datetime import datetime, timezone

from cart import obtener_carrito_sesion, vaciar_carrito
from models import DetallePedido, Disco, MetodoPago, Pedido, TransaccionPago, ahora_utc, db


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

    # Preparar elementos y validar existencias
    detalles_a_crear = []
    total_pedido = 0

    try:
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

        db.session.commit()

        # Vaciar carrito de la sesión tras éxito en base de datos
        vaciar_carrito()
        return True, pedido

    except Exception:
        db.session.rollback()
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

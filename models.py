"""Modelos relacionales y POO del dominio New Records."""

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


def ahora_utc():
    """Retorna una fecha UTC consciente de zona horaria."""
    return datetime.now(timezone.utc)


class Usuario(db.Model):
    __tablename__ = "usuarios"
    __table_args__ = (
        db.CheckConstraint(
            "char_length(btrim(nombre)) BETWEEN 2 AND 100",
            name="ck_usuarios_nombre_valido",
        ),
        db.CheckConstraint(
            "email = lower(btrim(email))",
            name="ck_usuarios_email_normalizado",
        ),
        db.CheckConstraint(
            "email ~ '^[^[:space:]@]+@[^[:space:]@]+\\.[^[:space:]@]+$'",
            name="ck_usuarios_email_formato",
        ),
        db.CheckConstraint(
            "rol IN ('cliente', 'administrador')",
            name="ck_usuarios_rol",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(
        db.String(20), nullable=False, default="cliente", server_default="cliente"
    )
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    ciudad = db.Column(db.String(100))
    activo = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    fecha_registro = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=ahora_utc,
        server_default=db.func.now(),
    )

    metodos_pago = db.relationship(
        "MetodoPago", back_populates="usuario", cascade="all, delete-orphan"
    )
    verificaciones_tarjeta = db.relationship(
        "VerificacionTarjeta",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
    pedidos = db.relationship(
        "Pedido", foreign_keys="Pedido.cliente_id", back_populates="cliente"
    )
    pedidos_revisados = db.relationship(
        "Pedido",
        foreign_keys="Pedido.administrador_revisor_id",
        back_populates="administrador_revisor",
    )

    def set_password(self, password_plano):
        """Almacena solamente el hash de la contraseña."""
        self.password_hash = generate_password_hash(password_plano)

    def check_password(self, password_plano):
        """Compara una contraseña recibida con el hash almacenado."""
        return check_password_hash(self.password_hash, password_plano)

    def es_administrador(self):
        return self.rol == "administrador"

    def __repr__(self):
        return f"<Usuario {self.email} ({self.rol})>"


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False, unique=True)
    slug = db.Column(db.String(90), nullable=False, unique=True, index=True)
    descripcion = db.Column(db.Text)
    imagen = db.Column(db.String(255))
    activo = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    fecha_creacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=ahora_utc,
        server_default=db.func.now(),
    )
    fecha_actualizacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=ahora_utc,
        onupdate=ahora_utc,
        server_default=db.func.now(),
    )

    discos = db.relationship("Disco", back_populates="categoria")

    def __repr__(self):
        return f"<Categoria {self.nombre}>"


class Disco(db.Model):
    """Clase padre persistente para los formatos físicos de New Records."""

    __tablename__ = "discos"
    __table_args__ = (
        db.CheckConstraint("precio_base >= 0", name="ck_discos_precio"),
        db.CheckConstraint("stock >= 0", name="ck_discos_stock"),
        db.CheckConstraint("peso_kg > 0", name="ck_discos_peso"),
        db.CheckConstraint(
            "costo_envio_por_kg >= 0", name="ck_discos_costo_envio"
        ),
        db.CheckConstraint(
            "costo_embalaje >= 0", name="ck_discos_costo_embalaje"
        ),
        db.CheckConstraint("formato IN ('CD', 'VINILO')", name="ck_discos_formato"),
    )

    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(
        db.Integer,
        db.ForeignKey("categorias.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    codigo = db.Column(db.String(30), nullable=False, unique=True, index=True)
    album = db.Column(db.String(150), nullable=False)
    artista = db.Column(db.String(120), nullable=False, index=True)
    descripcion = db.Column(db.Text, nullable=False)
    precio_base = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    formato = db.Column(db.String(10), nullable=False, index=True)
    peso_kg = db.Column(db.Numeric(6, 3), nullable=False)
    costo_envio_por_kg = db.Column(
        db.Numeric(10, 2), nullable=False, default=0, server_default="0"
    )
    costo_embalaje = db.Column(
        db.Numeric(10, 2), nullable=False, default=0, server_default="0"
    )
    imagen = db.Column(db.String(255))
    activo = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    fecha_creacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=ahora_utc,
        server_default=db.func.now(),
    )
    fecha_actualizacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=ahora_utc,
        onupdate=ahora_utc,
        server_default=db.func.now(),
    )

    categoria = db.relationship("Categoria", back_populates="discos")
    detalles_pedido = db.relationship("DetallePedido", back_populates="disco")

    __mapper_args__ = {
        "polymorphic_on": formato,
        "polymorphic_abstract": True,
    }

    def precio_final(self):
        """Contrato polimórfico implementado por cada formato."""
        raise NotImplementedError("El formato debe calcular su precio final.")

    def ficha(self):
        return (
            f"[{self.codigo}] {self.artista} - {self.album} "
            f"| {self.formato} | Stock: {self.stock}"
        )

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.codigo} - {self.album}>"


class CD(Disco):
    __mapper_args__ = {"polymorphic_identity": "CD"}

    def precio_final(self):
        envio = self.peso_kg * self.costo_envio_por_kg
        return self.precio_base + envio


class Vinilo(Disco):
    __mapper_args__ = {"polymorphic_identity": "VINILO"}

    def precio_final(self):
        envio = self.peso_kg * self.costo_envio_por_kg
        return self.precio_base + envio + self.costo_embalaje


class MetodoPago(db.Model):
    __tablename__ = "metodos_pago"
    __table_args__ = (
        db.CheckConstraint(
            "ultimos4 ~ '^[0-9]{4}$'", name="ck_metodos_pago_ultimos4"
        ),
        db.CheckConstraint(
            "mes_vencimiento BETWEEN 1 AND 12",
            name="ck_metodos_pago_mes_vencimiento",
        ),
        db.CheckConstraint(
            "anio_vencimiento BETWEEN 2020 AND 2100",
            name="ck_metodos_pago_anio_vencimiento",
        ),
        db.CheckConstraint(
            "marca IN ('VISA', 'MASTERCARD', 'AMEX')",
            name="ck_metodos_pago_marca",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token = db.Column(db.String(120), nullable=False, unique=True)
    marca = db.Column(db.String(30), nullable=False)
    ultimos4 = db.Column(db.String(4), nullable=False)
    titular = db.Column(db.String(120), nullable=False)
    mes_vencimiento = db.Column(db.Integer, nullable=False)
    anio_vencimiento = db.Column(db.Integer, nullable=False)
    predeterminado = db.Column(
        db.Boolean, nullable=False, default=False, server_default="false"
    )
    activo = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    fecha_verificacion = db.Column(db.DateTime(timezone=True), nullable=False)

    usuario = db.relationship("Usuario", back_populates="metodos_pago")
    pedidos = db.relationship("Pedido", back_populates="metodo_pago")
    transacciones = db.relationship("TransaccionPago", back_populates="metodo_pago")


class VerificacionTarjeta(db.Model):
    __tablename__ = "verificaciones_tarjeta"
    __table_args__ = (
        db.CheckConstraint(
            "intentos BETWEEN 0 AND 3", name="ck_verificaciones_intentos"
        ),
        db.CheckConstraint(
            "ultimos4 ~ '^[0-9]{4}$'", name="ck_verificaciones_ultimos4"
        ),
        db.CheckConstraint(
            "mes_vencimiento BETWEEN 1 AND 12",
            name="ck_verificaciones_mes_vencimiento",
        ),
        db.CheckConstraint(
            "anio_vencimiento BETWEEN 2020 AND 2100",
            name="ck_verificaciones_anio_vencimiento",
        ),
        db.CheckConstraint(
            "marca IN ('VISA', 'MASTERCARD', 'AMEX')",
            name="ck_verificaciones_marca",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_verificacion = db.Column(db.String(64), nullable=False, unique=True)
    pin_hash = db.Column(db.String(255), nullable=False)
    token_tarjeta = db.Column(db.String(120), nullable=False)
    marca = db.Column(db.String(30), nullable=False)
    ultimos4 = db.Column(db.String(4), nullable=False)
    titular = db.Column(db.String(120), nullable=False)
    mes_vencimiento = db.Column(db.Integer, nullable=False)
    anio_vencimiento = db.Column(db.Integer, nullable=False)
    fecha_creacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=ahora_utc,
        server_default=db.func.now(),
    )
    fecha_expiracion = db.Column(db.DateTime(timezone=True), nullable=False)
    intentos = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    verificada = db.Column(
        db.Boolean, nullable=False, default=False, server_default="false"
    )

    usuario = db.relationship("Usuario", back_populates="verificaciones_tarjeta")


class Pedido(db.Model):
    __tablename__ = "pedidos"
    __table_args__ = (
        db.CheckConstraint(
            "estado IN ('PENDIENTE', 'APROBADO', 'RECHAZADO')",
            name="ck_pedidos_estado",
        ),
        db.CheckConstraint("total >= 0", name="ck_pedidos_total"),
        db.CheckConstraint(
            "estado <> 'RECHAZADO' OR motivo_rechazo IS NOT NULL",
            name="ck_pedidos_rechazo_con_motivo",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(24), nullable=False, unique=True, index=True)
    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    metodo_pago_id = db.Column(
        db.Integer,
        db.ForeignKey("metodos_pago.id", ondelete="RESTRICT"),
        nullable=False,
    )
    estado = db.Column(
        db.String(20), nullable=False, default="PENDIENTE", server_default="PENDIENTE"
    )
    total = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_creacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=ahora_utc,
        server_default=db.func.now(),
    )
    fecha_revision = db.Column(db.DateTime(timezone=True))
    administrador_revisor_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="SET NULL"),
        index=True,
    )
    motivo_rechazo = db.Column(db.String(255))

    cliente = db.relationship(
        "Usuario", foreign_keys=[cliente_id], back_populates="pedidos"
    )
    administrador_revisor = db.relationship(
        "Usuario",
        foreign_keys=[administrador_revisor_id],
        back_populates="pedidos_revisados",
    )
    metodo_pago = db.relationship("MetodoPago", back_populates="pedidos")
    detalles = db.relationship(
        "DetallePedido", back_populates="pedido", cascade="all, delete-orphan"
    )
    transaccion_pago = db.relationship(
        "TransaccionPago", back_populates="pedido", uselist=False
    )
    facturas = db.relationship(
        "Factura", back_populates="pedido", cascade="all, delete-orphan"
    )

    def esta_pendiente(self):
        return self.estado == "PENDIENTE"


class DetallePedido(db.Model):
    __tablename__ = "detalles_pedido"
    __table_args__ = (
        db.CheckConstraint("cantidad > 0", name="ck_detalles_cantidad"),
        db.CheckConstraint(
            "precio_unitario >= 0", name="ck_detalles_precio_unitario"
        ),
        db.UniqueConstraint(
            "pedido_id", "disco_id", name="uq_detalles_pedido_disco"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey("pedidos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    disco_id = db.Column(
        db.Integer,
        db.ForeignKey("discos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    album = db.Column(db.String(150), nullable=False)
    artista = db.Column(db.String(120), nullable=False)
    formato = db.Column(db.String(10), nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)

    pedido = db.relationship("Pedido", back_populates="detalles")
    disco = db.relationship("Disco", back_populates="detalles_pedido")

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad


class TransaccionPago(db.Model):
    __tablename__ = "transacciones_pago"
    __table_args__ = (
        db.CheckConstraint("monto >= 0", name="ck_transacciones_monto"),
        db.CheckConstraint(
            "estado IN ('PENDIENTE', 'APROBADA', 'RECHAZADA')",
            name="ck_transacciones_estado",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey("pedidos.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    metodo_pago_id = db.Column(
        db.Integer,
        db.ForeignKey("metodos_pago.id", ondelete="RESTRICT"),
        nullable=False,
    )
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(
        db.String(20), nullable=False, default="PENDIENTE", server_default="PENDIENTE"
    )
    referencia = db.Column(db.String(80), nullable=False, unique=True)
    fecha_procesamiento = db.Column(db.DateTime(timezone=True))

    pedido = db.relationship("Pedido", back_populates="transaccion_pago")
    metodo_pago = db.relationship("MetodoPago", back_populates="transacciones")


class Factura(db.Model):
    __tablename__ = "facturas"
    __table_args__ = (
        db.CheckConstraint(
            "tipo IN ('COMPROBANTE_PENDIENTE', 'FACTURA_FINAL')",
            name="ck_facturas_tipo",
        ),
        db.UniqueConstraint("pedido_id", "tipo", name="uq_facturas_pedido_tipo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey("pedidos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    numero = db.Column(db.String(30), nullable=False, unique=True, index=True)
    tipo = db.Column(db.String(30), nullable=False)
    fecha_emision = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=ahora_utc,
        server_default=db.func.now(),
    )
    ruta_pdf = db.Column(db.String(255), nullable=False)

    pedido = db.relationship("Pedido", back_populates="facturas")

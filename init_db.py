"""Crea las tablas y carga los datos iniciales de New Records.

El script es idempotente: puede ejecutarse nuevamente sin duplicar registros
y nunca elimina tablas ni datos existentes.
"""

import os
from decimal import Decimal

from sqlalchemy import text

from app import app
from models import CD, Categoria, Disco, Usuario, Vinilo, db


CATEGORIAS = [
    {
        "nombre": "Rock",
        "slug": "rock",
        "descripcion": "Del rock clásico al grunge y el sonido alternativo.",
        "imagen": "img/categorias/rock.jpg",
    },
    {
        "nombre": "Pop",
        "slug": "pop",
        "descripcion": "Grandes voces, melodías globales y producción contemporánea.",
        "imagen": "img/categorias/pop.jpg",
    },
    {
        "nombre": "Reggaeton",
        "slug": "reggaeton",
        "descripcion": "Ritmos urbanos, trap latino y sonidos del Caribe.",
        "imagen": "img/categorias/reggaeton.jpg",
    },
]


DISCOS = [
    {
        "codigo": "NR-REG-001",
        "album": "Debí Tirar Más Fotos",
        "artista": "Bad Bunny",
        "categoria": "reggaeton",
        "formato": "VINILO",
        "precio_base": "35.00",
        "stock": 12,
        "peso_kg": "0.450",
        "costo_envio_por_kg": "2.50",
        "costo_embalaje": "1.50",
        "imagen": "img/productos/dtmf.png",
        "descripcion": "Combina estilos urbanos con elementos tradicionales de Puerto Rico, incluyendo toques de salsa y ritmos nostálgicos.",
    },
    {
        "codigo": "NR-ROC-001",
        "album": "The Dark Side of the Moon",
        "artista": "Pink Floyd",
        "categoria": "rock",
        "formato": "VINILO",
        "precio_base": "42.00",
        "stock": 8,
        "peso_kg": "0.460",
        "costo_envio_por_kg": "2.50",
        "costo_embalaje": "1.50",
        "imagen": "img/productos/tdsotm.jpg",
        "descripcion": "Uno de los álbumes más vendidos de la historia, considerado una obra maestra del rock progresivo.",
    },
    {
        "codigo": "NR-POP-001",
        "album": "Future Nostalgia",
        "artista": "Dua Lipa",
        "categoria": "pop",
        "formato": "CD",
        "precio_base": "29.99",
        "stock": 18,
        "peso_kg": "0.120",
        "costo_envio_por_kg": "2.50",
        "costo_embalaje": "0.50",
        "imagen": "img/productos/fn.jpg",
        "descripcion": "Exitoso álbum que combina el pop ochentero con elementos de la música electrónica.",
    },
    {
        "codigo": "NR-POP-002",
        "album": "After Hours",
        "artista": "The Weeknd",
        "categoria": "pop",
        "formato": "VINILO",
        "precio_base": "38.50",
        "stock": 10,
        "peso_kg": "0.440",
        "costo_envio_por_kg": "2.50",
        "costo_embalaje": "1.50",
        "imagen": "img/productos/ah.png",
        "descripcion": "Álbum de R&B y pop oscuro que fusiona synth-pop, new wave y trap con una estética nocturna y melancólica.",
    },
    {
        "codigo": "NR-ROC-002",
        "album": "Demon Days",
        "artista": "Gorillaz",
        "categoria": "rock",
        "formato": "VINILO",
        "precio_base": "45.00",
        "stock": 9,
        "peso_kg": "0.470",
        "costo_envio_por_kg": "2.50",
        "costo_embalaje": "1.50",
        "imagen": "img/productos/dd.jpg",
        "descripcion": "Fusiona trip-hop, hip-hop, electrónica, pop y rock, con una atmósfera melancólica y futurista.",
    },
    {
        "codigo": "NR-REG-002",
        "album": "Atrevido",
        "artista": "Trueno",
        "categoria": "reggaeton",
        "formato": "CD",
        "precio_base": "33.00",
        "stock": 14,
        "peso_kg": "0.110",
        "costo_envio_por_kg": "2.50",
        "costo_embalaje": "0.50",
        "imagen": "img/productos/tra.jpg",
        "descripcion": "Álbum debut del rapero argentino Trueno, que marca su transición del freestyle a la música profesional.",
    },
    {
        "codigo": "NR-POP-003",
        "album": "Hit Me Hard and Soft",
        "artista": "Billie Eilish",
        "categoria": "pop",
        "formato": "CD",
        "precio_base": "39.99",
        "stock": 16,
        "peso_kg": "0.115",
        "costo_envio_por_kg": "2.50",
        "costo_embalaje": "0.50",
        "imagen": "img/productos/hmhas.jpg",
        "descripcion": "Trabajo diverso y cohesivo que fusiona géneros con un sonido inmersivo y emocional.",
    },
    {
        "codigo": "NR-ROC-003",
        "album": "Nevermind",
        "artista": "Nirvana",
        "categoria": "rock",
        "formato": "VINILO",
        "precio_base": "34.50",
        "stock": 11,
        "peso_kg": "0.450",
        "costo_envio_por_kg": "2.50",
        "costo_embalaje": "1.50",
        "imagen": "img/productos/nn.jpg",
        "descripcion": "Grunge por excelencia y uno de los álbumes más influyentes de la historia del rock.",
    },
    {
        "codigo": "NR-ROC-004",
        "album": "Abbey Road",
        "artista": "The Beatles",
        "categoria": "rock",
        "formato": "VINILO",
        "precio_base": "39.99",
        "stock": 7,
        "peso_kg": "0.460",
        "costo_envio_por_kg": "2.50",
        "costo_embalaje": "1.50",
        "imagen": "img/productos/ar.jpg",
        "descripcion": "Ícono del rock en una edición remasterizada con su reconocida portada del paso de cebra.",
    },
    {
        "codigo": "NR-POP-004",
        "album": "Dangerous Woman",
        "artista": "Ariana Grande",
        "categoria": "pop",
        "formato": "CD",
        "precio_base": "36.00",
        "stock": 13,
        "peso_kg": "0.120",
        "costo_envio_por_kg": "2.50",
        "costo_embalaje": "0.50",
        "imagen": "img/productos/dw.jpg",
        "descripcion": "Una transición madura hacia sonidos pop, R&B y dance-pop con toques de soul.",
    },
    {
        "codigo": "NR-REG-003",
        "album": "House of Pleasure",
        "artista": "Plan B",
        "categoria": "reggaeton",
        "formato": "CD",
        "precio_base": "32.00",
        "stock": 10,
        "peso_kg": "0.110",
        "costo_envio_por_kg": "2.50",
        "costo_embalaje": "0.50",
        "imagen": "img/productos/hop.jpg",
        "descripcion": "Reggaetón clásico con toques electrónicos y éxitos representativos del dúo puertorriqueño.",
    },
    {
        "codigo": "NR-REG-004",
        "album": "FERXXOCALIPSIS",
        "artista": "Feid",
        "categoria": "reggaeton",
        "formato": "CD",
        "precio_base": "37.50",
        "stock": 15,
        "peso_kg": "0.115",
        "costo_envio_por_kg": "2.50",
        "costo_embalaje": "0.50",
        "imagen": "img/productos/fxxrp.jpg",
        "descripcion": "Ritmos oscuros y profundos con un estilo de perreo clásico de Medellín.",
    },
]


DEFAULTS_FECHA = (
    ("usuarios", "fecha_registro"),
    ("categorias", "fecha_creacion"),
    ("categorias", "fecha_actualizacion"),
    ("discos", "fecha_creacion"),
    ("discos", "fecha_actualizacion"),
    ("verificaciones_tarjeta", "fecha_creacion"),
    ("pedidos", "fecha_creacion"),
    ("facturas", "fecha_emision"),
)


RESTRICCIONES_USUARIO = {
    "ck_usuarios_nombre_valido": (
        "CHECK (char_length(btrim(nombre)) BETWEEN 2 AND 100)"
    ),
    "ck_usuarios_email_normalizado": "CHECK (email = lower(btrim(email)))",
    "ck_usuarios_email_formato": (
        "CHECK (email ~ '^[^@ ]+@[^@ ]+\\.[^@ ]+$')"
    ),
}


def actualizar_reglas_schema():
    """Aplica de forma idempotente reglas añadidas después de la creación inicial."""
    for tabla, columna in DEFAULTS_FECHA:
        db.session.execute(
            text(
                f"ALTER TABLE {tabla} "
                f"ALTER COLUMN {columna} SET DEFAULT CURRENT_TIMESTAMP"
            )
        )

    for nombre, expresion in RESTRICCIONES_USUARIO.items():
        existe = db.session.execute(
            text(
                "SELECT EXISTS ("
                "SELECT 1 FROM pg_constraint WHERE conname = :nombre"
                ")"
            ),
            {"nombre": nombre},
        ).scalar_one()
        if not existe:
            db.session.execute(
                text(
                    f"ALTER TABLE usuarios ADD CONSTRAINT {nombre} {expresion}"
                )
            )


def obtener_password(nombre_variable):
    password = os.getenv(nombre_variable, "")
    if not password or password.startswith("change_"):
        raise RuntimeError(
            f"Configura {nombre_variable} en el archivo .env antes de inicializar."
        )
    return password


def cargar_categoria(datos):
    categoria = Categoria.query.filter_by(slug=datos["slug"]).first()
    if categoria is None:
        categoria = Categoria(slug=datos["slug"])
        db.session.add(categoria)

    categoria.nombre = datos["nombre"]
    categoria.descripcion = datos["descripcion"]
    categoria.imagen = datos["imagen"]
    return categoria


def cargar_usuario(nombre, email, rol, password):
    email_normalizado = email.strip().lower()
    usuario = Usuario.query.filter_by(email=email_normalizado).first()
    if usuario is None:
        usuario = Usuario(email=email_normalizado)
        usuario.set_password(password)
        db.session.add(usuario)

    usuario.nombre = nombre
    usuario.rol = rol
    usuario.activo = True
    return usuario


def cargar_disco(datos, categorias_por_slug):
    clase_disco = CD if datos["formato"] == "CD" else Vinilo
    disco = Disco.query.filter_by(codigo=datos["codigo"]).first()

    if disco is not None and not isinstance(disco, clase_disco):
        raise RuntimeError(
            f"El disco {datos['codigo']} existe con un formato incompatible."
        )

    if disco is None:
        disco = clase_disco(codigo=datos["codigo"], stock=datos["stock"], activo=True)
        db.session.add(disco)

    disco.categoria = categorias_por_slug[datos["categoria"]]
    disco.album = datos["album"]
    disco.artista = datos["artista"]
    disco.descripcion = datos["descripcion"]
    disco.precio_base = Decimal(datos["precio_base"])
    disco.peso_kg = Decimal(datos["peso_kg"])
    disco.costo_envio_por_kg = Decimal(datos["costo_envio_por_kg"])
    disco.costo_embalaje = Decimal(datos["costo_embalaje"])
    disco.imagen = datos["imagen"]
    return disco


def inicializar_base():
    with app.app_context():
        try:
            db.create_all()
            actualizar_reglas_schema()

            categorias = {
                datos["slug"]: cargar_categoria(datos) for datos in CATEGORIAS
            }

            cargar_usuario(
                os.getenv("ADMIN_NAME", "Administrador New Records"),
                os.getenv("ADMIN_EMAIL", "admin@newrecords.local"),
                "administrador",
                obtener_password("ADMIN_PASSWORD"),
            )
            cargar_usuario(
                os.getenv("CLIENTE_DEMO_NAME", "Cliente Demo"),
                os.getenv("CLIENTE_DEMO_EMAIL", "cliente@newrecords.local"),
                "cliente",
                obtener_password("CLIENTE_DEMO_PASSWORD"),
            )

            for datos in DISCOS:
                cargar_disco(datos, categorias)

            db.session.commit()

            print("Base de datos inicializada correctamente.")
            print(f"Categorías disponibles: {Categoria.query.count()}")
            print(f"Discos disponibles: {Disco.query.count()}")
            print(f"Usuarios de demostración: {Usuario.query.count()}")
        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    inicializar_base()

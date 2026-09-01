"""Pruebas de navegación parcial y prevención del pantallazo blanco."""

import re
from pathlib import Path

from app import app
from models import Disco, Usuario

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent


def cargar_estilos_modulares():
    """Concatena los módulos CSS en el mismo orden declarado por styles.css."""
    directorio = RAIZ_PROYECTO / "static" / "css"
    entrada = (directorio / "styles.css").read_text(encoding="utf-8")
    modulos = re.findall(r'@import url\("([^"]+)"\)', entrada)
    return "\n".join(
        (directorio / modulo).read_text(encoding="utf-8") for modulo in modulos
    )


def test_base_activa_navegacion_parcial_con_indicador(client):
    respuesta = client.get("/productos")
    contenido = respuesta.get_data(as_text=True)

    assert respuesta.status_code == 200
    assert 'hx-boost="true"' in contenido
    assert 'hx-push-url="true"' in contenido
    assert 'hx-indicator="#indicadorNavegacion"' in contenido
    assert 'id="indicadorNavegacion"' in contenido
    assert "htmx.org@2.0.10/dist/htmx.min.js" in contenido
    assert 'src="/static/js/script.js" defer' in contenido


def test_redireccion_htmx_se_convierte_en_navegacion_parcial(client):
    with app.app_context():
        usuario = Usuario.query.filter_by(rol="cliente", activo=True).first()
        usuario_id = usuario.id

    with client.session_transaction() as sesion:
        sesion["usuario_id"] = usuario_id

    respuesta_htmx = client.get("/", headers={"HX-Request": "true"})
    assert respuesta_htmx.status_code == 204
    assert respuesta_htmx.headers["HX-Location"] == "/productos"
    assert "Location" not in respuesta_htmx.headers

    respuesta_clasica = client.get("/")
    assert respuesta_clasica.status_code == 302
    assert respuesta_clasica.headers["Location"].endswith("/productos")


def test_accion_post_htmx_no_fuerza_recarga_completa(client):
    with app.app_context():
        usuario = Usuario.query.filter_by(rol="cliente", activo=True).first()
        disco = Disco.query.filter(Disco.activo.is_(True), Disco.stock > 0).first()
        usuario_id = usuario.id
        disco_id = disco.id

    with client.session_transaction() as sesion:
        sesion["usuario_id"] = usuario_id

    respuesta = client.post(
        f"/carrito/agregar/{disco_id}",
        headers={"HX-Request": "true"},
    )

    assert respuesta.status_code == 204
    assert respuesta.headers["HX-Location"] == "/carrito"
    assert "Location" not in respuesta.headers


def test_recursos_contienen_respaldo_oscuro_y_reinicializacion():
    estilos = cargar_estilos_modulares()
    javascript = (RAIZ_PROYECTO / "static" / "js" / "script.js").read_text(
        encoding="utf-8"
    )
    catalogo = (RAIZ_PROYECTO / "templates" / "productos.html").read_text(
        encoding="utf-8"
    )

    assert ".capa-transicion-pagina.htmx-request" in estilos
    assert "@view-transition" in estilos
    assert "htmx:afterSettle" in javascript
    assert "htmx:beforeSwap" in javascript
    assert "window.location.reload()" not in javascript
    assert ".requestSubmit()" in catalogo
    assert "formFiltroProductos').submit()" not in catalogo


def test_submenu_admin_permanece_visible_al_expandirse():
    estilos = cargar_estilos_modulares()

    regla_expandida = re.search(
        r"\.sidebar:hover \.submodulo-sidebar\.abierto > \.sublista-sidebar,\s*"
        r"\.sidebar:focus-within \.submodulo-sidebar\.abierto > \.sublista-sidebar\s*"
        r"\{(?P<declaraciones>[^}]*)\}",
        estilos,
    )

    assert regla_expandida is not None
    declaraciones = regla_expandida.group("declaraciones")
    assert "display: flex" in declaraciones
    assert "opacity: 1" in declaraciones
    assert "pointer-events: auto" in declaraciones


def test_badge_formato_solo_es_absoluto_sobre_portadas():
    estilos = cargar_estilos_modulares()

    badge_general = re.search(
        r"\.badge-formato-tarjeta\s*\{(?P<declaraciones>[^}]*)\}", estilos
    )
    badge_portada = re.search(
        r"\.tarjeta-producto-imagen > \.badge-formato-tarjeta\s*"
        r"\{(?P<declaraciones>[^}]*)\}",
        estilos,
    )

    assert badge_general is not None
    assert "position: static" in badge_general.group("declaraciones")
    assert badge_portada is not None
    assert "position: absolute" in badge_portada.group("declaraciones")

"""Pruebas de navegación parcial y prevención del pantallazo blanco."""

from pathlib import Path

from app import app
from models import Disco, Usuario


RAIZ_PROYECTO = Path(__file__).resolve().parent.parent


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
    estilos = (RAIZ_PROYECTO / "static" / "css" / "styles.css").read_text(
        encoding="utf-8"
    )
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

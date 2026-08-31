"""Pruebas estructurales de la arquitectura modular de New Records."""

from pathlib import Path

from app import create_app
from config import Config
from report_repository import cargar_consultas
from validators import es_url_segura

RAIZ = Path(__file__).resolve().parent.parent


def test_fabrica_registra_blueprints_por_dominio():
    aplicacion = create_app(
        Config,
        {
            "TESTING": True,
            "SECRET_KEY": "clave-exclusiva-para-pruebas",
            "WTF_CSRF_ENABLED": False,
        },
    )

    assert set(aplicacion.blueprints) == {
        "auth",
        "catalogo",
        "carrito",
        "pagos",
        "pedidos",
        "admin",
    }
    endpoints = {regla.endpoint for regla in aplicacion.url_map.iter_rules()}
    assert "catalogo.productos" in endpoints
    assert "pedidos.confirmar_checkout" in endpoints
    assert "admin.admin_pedido_aprobar" in endpoints


def test_validador_de_redireccion_rechaza_otro_dominio():
    aplicacion = create_app(
        Config,
        {"TESTING": True, "SECRET_KEY": "clave-exclusiva-para-pruebas"},
    )
    with aplicacion.test_request_context("/", base_url="https://newrecords.test"):
        assert es_url_segura("/productos")
        assert es_url_segura("https://newrecords.test/pedidos")
        assert not es_url_segura("https://sitio-malicioso.example")


def test_reportes_tienen_una_fuente_sql_canonica():
    consultas = cargar_consultas()
    assert set(consultas) == {
        "resumen_metricas",
        "ventas_diario",
        "ventas_semanal",
        "ventas_mensual",
        "ventas_anual",
        "ranking_discos",
        "ranking_categorias",
    }
    assert "JOIN detalles_pedido" in consultas["resumen_metricas"]
    assert "JOIN detalles_pedido" not in (RAIZ / "services.py").read_text(
        encoding="utf-8"
    )


def test_css_principal_importa_modulos_existentes_en_orden():
    directorio = RAIZ / "static" / "css"
    entrada = (directorio / "styles.css").read_text(encoding="utf-8")
    nombres = [
        "base.css",
        "catalogo.css",
        "carrito-checkout.css",
        "pedidos-pagos.css",
        "admin.css",
        "admin-formularios.css",
    ]
    posiciones = [entrada.index(nombre) for nombre in nombres]
    assert posiciones == sorted(posiciones)
    assert all((directorio / nombre).is_file() for nombre in nombres)


def test_alembic_incluye_baseline_y_reglas_postgresql():
    versiones = list((RAIZ / "alembic" / "versions").glob("*.py"))
    contenido = "\n".join(archivo.read_text(encoding="utf-8") for archivo in versiones)
    assert "baseline_relacional_new_records" in contenido
    assert "rules_codigos_discos.sql" in contenido
    assert "rules_fases7_10.sql" in contenido
    assert "rules_fases12.sql" in contenido

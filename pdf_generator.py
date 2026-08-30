"""Generador de documentos PDF (Comprobantes y Facturas) con ReportLab para New Records."""

import io
import os
import tempfile
from pathlib import Path

from flask import current_app
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from models import Factura, ahora_utc, db

CARPETA_COMPROBANTES = Path(__file__).resolve().parent / "docs" / "comprobantes"


def asegurar_directorio():
    """Crea la carpeta de comprobantes si no existe."""
    carpeta_configurada = current_app.config.get("PDF_OUTPUT_DIR")
    carpeta = Path(carpeta_configurada) if carpeta_configurada else CARPETA_COMPROBANTES
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def ruta_pdf_pedido(pedido, tipo):
    """Calcula la ruta determinística de un documento del pedido."""
    prefijo = "FAC" if tipo == "FACTURA_FINAL" else "COMP"
    return asegurar_directorio() / f"{prefijo}-{pedido.numero}.pdf"


def eliminar_pdf_pedido(pedido, tipo):
    """Elimina un documento incompleto cuando su transacción no pudo confirmarse."""
    try:
        ruta = ruta_pdf_pedido(pedido, tipo)
        if ruta.exists():
            ruta.unlink()
        return True
    except OSError as error:
        current_app.logger.warning(
            "No se pudo eliminar el PDF incompleto de %s: %s",
            pedido.numero,
            error,
        )
        return False


def generar_pdf_pedido(pedido, tipo="COMPROBANTE_PENDIENTE"):
    """Genera un archivo PDF con ReportLab para el pedido especificado.

    Soporta tipos:
    - 'COMPROBANTE_PENDIENTE': Comprobante preliminar tras el checkout.
    - 'FACTURA_FINAL': Factura comercial oficial emitida tras la aprobación.

    Retorna una tupla: (bytes_pdf, nombre_archivo, factura)
    """
    if tipo not in ("COMPROBANTE_PENDIENTE", "FACTURA_FINAL"):
        raise ValueError("El tipo de documento solicitado no es válido.")
    if tipo == "FACTURA_FINAL" and pedido.estado != "APROBADO":
        raise ValueError("La factura final requiere un pedido aprobado.")

    carpeta_comprobantes = asegurar_directorio()

    if tipo == "FACTURA_FINAL":
        prefijo = "FAC"
        titulo_doc = "FACTURA OFICIAL DE VENTA"
        subtitulo_doc = "Documento mercantil y tributario emitido tras aprobación"
    else:
        prefijo = "COMP"
        titulo_doc = "COMPROBANTE DE PEDIDO"
        subtitulo_doc = "Comprobante de orden en revisión administrativa"

    numero_documento = f"{prefijo}-{pedido.numero}"
    nombre_archivo = f"{numero_documento}.pdf"
    ruta_completa = carpeta_comprobantes / nombre_archivo
    try:
        ruta_relativa = str(ruta_completa.relative_to(Path(current_app.root_path)))
    except ValueError:
        ruta_relativa = str(ruta_completa)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    elementos = []
    estilos = getSampleStyleSheet()

    # Estilos personalizados
    estilo_titulo = ParagraphStyle(
        "TituloPrincipal",
        parent=estilos["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#8a2be2"),  # Púrpura New Records
        fontName="Helvetica-Bold",
        alignment=0,
    )

    estilo_subtitulo = ParagraphStyle(
        "SubtituloDoc",
        parent=estilos["Normal"],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#4b5563"),
        fontName="Helvetica",
    )

    estilo_normal = ParagraphStyle(
        "TextoNormal",
        parent=estilos["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1f2937"),
        fontName="Helvetica",
    )

    estilo_negrita = ParagraphStyle(
        "TextoNegrita",
        parent=estilo_normal,
        fontName="Helvetica-Bold",
    )

    estilo_cabecera_tabla = ParagraphStyle(
        "CabeceraTabla",
        parent=estilo_normal,
        fontSize=9,
        leading=11,
        fontName="Helvetica-Bold",
        textColor=colors.white,
        alignment=1,
    )

    estilo_celda = ParagraphStyle(
        "CeldaTabla",
        parent=estilo_normal,
        fontSize=8.5,
        leading=11,
    )

    estilo_celda_centro = ParagraphStyle(
        "CeldaCentro",
        parent=estilo_celda,
        alignment=1,
    )

    estilo_celda_derecha = ParagraphStyle(
        "CeldaDerecha",
        parent=estilo_celda,
        alignment=2,
    )

    # 1. Cabecera con Logotipo y Datos de la Empresa
    datos_cabecera = [
        [
            Paragraph("<b>NEW RECORDS</b><br/><font size=8 color='#6b7280'>Música Física en CD y Vinilo</font>", estilo_titulo),
            Paragraph(
                f"<b>{titulo_doc}</b><br/>"
                f"<font size=8><b>N° Documento:</b> {numero_documento}<br/>"
                f"<b>N° Pedido:</b> {pedido.numero}<br/>"
                f"<b>Fecha:</b> {pedido.fecha_creacion.strftime('%d/%m/%Y %H:%M UTC')}<br/>"
                f"<b>Estado:</b> {pedido.estado}</font>",
                estilo_normal,
            ),
        ]
    ]

    tabla_cabecera = Table(datos_cabecera, colWidths=[3.2 * inch, 4.3 * inch])
    tabla_cabecera.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    elementos.append(tabla_cabecera)
    elementos.append(Spacer(1, 12))
    elementos.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#8a2be2"), spaceAfter=12))

    # 2. Información del Cliente y Método de Pago
    cliente = pedido.cliente
    metodo = pedido.metodo_pago

    info_cliente_texto = (
        f"<b>DATOS DEL CLIENTE</b><br/>"
        f"<b>Nombre:</b> {cliente.nombre}<br/>"
        f"<b>Correo:</b> {cliente.email}<br/>"
        f"<b>Teléfono:</b> {cliente.telefono or 'No registrado'}<br/>"
        f"<b>Dirección:</b> {cliente.direccion or 'No registrada'}, {cliente.ciudad or ''}"
    )

    info_pago_texto = (
        f"<b>DATOS DE FACTURACIÓN Y PAGO</b><br/>"
        f"<b>Método:</b> Tarjeta {metodo.marca} (**** {metodo.ultimos4})<br/>"
        f"<b>Titular:</b> {metodo.titular}<br/>"
        f"<b>Vencimiento:</b> {metodo.mes_vencimiento:02d}/{metodo.anio_vencimiento}<br/>"
        f"<b>Ref. Pago:</b> {pedido.transaccion_pago.referencia if pedido.transaccion_pago else 'N/A'}"
    )

    datos_bloque_info = [
        [
            Paragraph(info_cliente_texto, estilo_normal),
            Paragraph(info_pago_texto, estilo_normal),
        ]
    ]

    tabla_info = Table(datos_bloque_info, colWidths=[3.75 * inch, 3.75 * inch])
    tabla_info.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    elementos.append(tabla_info)
    elementos.append(Spacer(1, 14))

    # 3. Tabla de Productos Comprados (Detalle Histórico)
    filas_productos = [
        [
            Paragraph("Ítem / Álbum", estilo_cabecera_tabla),
            Paragraph("Artista", estilo_cabecera_tabla),
            Paragraph("Formato", estilo_cabecera_tabla),
            Paragraph("Precio Unit.", estilo_cabecera_tabla),
            Paragraph("Cant.", estilo_cabecera_tabla),
            Paragraph("Subtotal", estilo_cabecera_tabla),
        ]
    ]

    for d in pedido.detalles:
        filas_productos.append(
            [
                Paragraph(f"<b>{d.album}</b>", estilo_celda),
                Paragraph(d.artista, estilo_celda),
                Paragraph(d.formato, estilo_celda_centro),
                Paragraph(f"${d.precio_unitario:.2f}", estilo_celda_derecha),
                Paragraph(str(d.cantidad), estilo_celda_centro),
                Paragraph(f"<b>${d.subtotal:.2f}</b>", estilo_celda_derecha),
            ]
        )

    tabla_productos = Table(
        filas_productos,
        colWidths=[2.3 * inch, 1.7 * inch, 0.9 * inch, 0.9 * inch, 0.6 * inch, 1.1 * inch],
    )
    tabla_productos.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8a2be2")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf5ff")]),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elementos.append(tabla_productos)
    elementos.append(Spacer(1, 10))

    # 4. Resumen de Totales
    datos_totales = [
        [
            Paragraph("<font size=7 color='#6b7280'>* Precios unitarios incluyen peso y embalaje protector por formato.</font>", estilo_normal),
            Paragraph(f"<b>TOTAL A PAGAR:</b>", estilo_celda_derecha),
            Paragraph(f"<b>${pedido.total:.2f}</b>", ParagraphStyle("TotalGrande", parent=estilo_negrita, fontSize=11, textColor=colors.HexColor("#008f39"), alignment=2)),
        ]
    ]

    tabla_totales = Table(datos_totales, colWidths=[4.9 * inch, 1.4 * inch, 1.2 * inch])
    tabla_totales.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elementos.append(tabla_totales)
    elementos.append(Spacer(1, 20))

    # 5. Aviso Legal y Timbre
    if tipo == "COMPROBANTE_PENDIENTE":
        aviso_texto = (
            "<b>NOTA DE SEGURIDAD:</b> Este comprobante confirma la recepción de tu orden de compra en New Records. "
            "El pedido se encuentra actualmente en estado <b>PENDIENTE</b> de revisión y control de inventario por parte de nuestro equipo. "
            "Una vez aprobado, el cobro simulado será formalizado y recibirás tu Factura Oficial definitiva."
        )
    else:
        aviso_texto = (
            "<b>CERTIFICACIÓN:</b> Factura final emitida de conformidad con las operaciones de comercio electrónico de New Records. "
            "El pedido ha sido formalmente <b>APROBADO</b> y el stock físico reservado para despacho inmediato."
        )

    tabla_aviso = Table([[Paragraph(aviso_texto, ParagraphStyle("Aviso", parent=estilo_normal, fontSize=7.5, leading=10, textColor=colors.HexColor("#4b5563")))]], colWidths=[7.5 * inch])
    tabla_aviso.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f4f6")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elementos.append(tabla_aviso)

    # Construir documento en memoria
    doc.build(elementos)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    # Guardar de forma atómica: nunca se deja un PDF parcial como documento válido.
    ruta_temporal = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=carpeta_comprobantes,
            prefix=f".{numero_documento}-",
            suffix=".tmp",
            delete=False,
        ) as archivo_temporal:
            ruta_temporal = Path(archivo_temporal.name)
            archivo_temporal.write(pdf_bytes)
            archivo_temporal.flush()
            os.fsync(archivo_temporal.fileno())
        os.replace(ruta_temporal, ruta_completa)
    except OSError as error:
        if ruta_temporal and ruta_temporal.exists():
            ruta_temporal.unlink()
        raise RuntimeError("No se pudo guardar el documento PDF.") from error

    # Registrar o actualizar Factura en base de datos PostgreSQL
    factura = Factura.query.filter_by(pedido_id=pedido.id, tipo=tipo).first()
    if not factura:
        factura = Factura(
            pedido_id=pedido.id,
            numero=numero_documento,
            tipo=tipo,
            fecha_emision=ahora_utc(),
            ruta_pdf=ruta_relativa,
        )
        db.session.add(factura)
    else:
        factura.numero = numero_documento
        factura.fecha_emision = ahora_utc()
        factura.ruta_pdf = ruta_relativa

    db.session.flush()

    return pdf_bytes, nombre_archivo, factura

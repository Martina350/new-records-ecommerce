-- Consultas canónicas de reportes de New Records.
-- Cada bloque `-- name:` es cargado por report_repository.py y también puede
-- ejecutarse de forma independiente en PostgreSQL.

-- name: resumen_metricas
SELECT
    COALESCE(COUNT(DISTINCT p.id), 0) AS total_pedidos,
    COALESCE(SUM(dp.cantidad), 0) AS total_unidades,
    COALESCE(SUM(dp.cantidad * dp.precio_unitario), 0.00) AS total_facturado
FROM pedidos p
JOIN detalles_pedido dp ON dp.pedido_id = p.id
WHERE p.estado = 'APROBADO';

-- name: ventas_diario
WITH ventas_base AS (
    SELECT
        p.id AS pedido_id,
        DATE_TRUNC('day', p.fecha_creacion)::date AS fecha_periodo,
        dp.cantidad,
        dp.cantidad * dp.precio_unitario AS subtotal
    FROM pedidos p
    JOIN detalles_pedido dp ON dp.pedido_id = p.id
    WHERE p.estado = 'APROBADO'
)
SELECT
    fecha_periodo AS fecha_inicio,
    EXTRACT(YEAR FROM fecha_periodo)::integer AS anio,
    EXTRACT(DOY FROM fecha_periodo)::integer AS periodo_num,
    TO_CHAR(fecha_periodo, 'YYYY-MM-DD') AS etiqueta,
    COUNT(DISTINCT pedido_id) AS total_pedidos,
    SUM(cantidad) AS total_unidades,
    SUM(subtotal) AS total_facturado
FROM ventas_base
GROUP BY fecha_periodo
ORDER BY fecha_inicio DESC;

-- name: ventas_semanal
WITH ventas_base AS (
    SELECT
        p.id AS pedido_id,
        DATE_TRUNC('week', p.fecha_creacion)::date AS fecha_periodo,
        dp.cantidad,
        dp.cantidad * dp.precio_unitario AS subtotal
    FROM pedidos p
    JOIN detalles_pedido dp ON dp.pedido_id = p.id
    WHERE p.estado = 'APROBADO'
)
SELECT
    fecha_periodo AS fecha_inicio,
    EXTRACT(YEAR FROM fecha_periodo)::integer AS anio,
    EXTRACT(WEEK FROM fecha_periodo)::integer AS periodo_num,
    'Semana ' || EXTRACT(WEEK FROM fecha_periodo)::text ||
        ' (' || EXTRACT(YEAR FROM fecha_periodo)::text || ')' AS etiqueta,
    COUNT(DISTINCT pedido_id) AS total_pedidos,
    SUM(cantidad) AS total_unidades,
    SUM(subtotal) AS total_facturado
FROM ventas_base
GROUP BY fecha_periodo
ORDER BY fecha_inicio DESC;

-- name: ventas_mensual
WITH ventas_base AS (
    SELECT
        p.id AS pedido_id,
        DATE_TRUNC('month', p.fecha_creacion)::date AS fecha_periodo,
        dp.cantidad,
        dp.cantidad * dp.precio_unitario AS subtotal
    FROM pedidos p
    JOIN detalles_pedido dp ON dp.pedido_id = p.id
    WHERE p.estado = 'APROBADO'
)
SELECT
    fecha_periodo AS fecha_inicio,
    EXTRACT(YEAR FROM fecha_periodo)::integer AS anio,
    EXTRACT(MONTH FROM fecha_periodo)::integer AS periodo_num,
    TO_CHAR(fecha_periodo, 'YYYY-MM') AS etiqueta,
    COUNT(DISTINCT pedido_id) AS total_pedidos,
    SUM(cantidad) AS total_unidades,
    SUM(subtotal) AS total_facturado
FROM ventas_base
GROUP BY fecha_periodo
ORDER BY fecha_inicio DESC;

-- name: ventas_anual
WITH ventas_base AS (
    SELECT
        p.id AS pedido_id,
        DATE_TRUNC('year', p.fecha_creacion)::date AS fecha_periodo,
        dp.cantidad,
        dp.cantidad * dp.precio_unitario AS subtotal
    FROM pedidos p
    JOIN detalles_pedido dp ON dp.pedido_id = p.id
    WHERE p.estado = 'APROBADO'
)
SELECT
    fecha_periodo AS fecha_inicio,
    EXTRACT(YEAR FROM fecha_periodo)::integer AS anio,
    EXTRACT(YEAR FROM fecha_periodo)::integer AS periodo_num,
    TO_CHAR(fecha_periodo, 'YYYY') AS etiqueta,
    COUNT(DISTINCT pedido_id) AS total_pedidos,
    SUM(cantidad) AS total_unidades,
    SUM(subtotal) AS total_facturado
FROM ventas_base
GROUP BY fecha_periodo
ORDER BY fecha_inicio DESC;

-- name: ranking_discos
SELECT
    d.id AS disco_id,
    dp.album,
    dp.artista,
    dp.formato,
    d.imagen,
    d.stock AS stock_actual,
    c.nombre AS categoria_nombre,
    SUM(dp.cantidad) AS total_unidades,
    SUM(dp.cantidad * dp.precio_unitario) AS total_facturado,
    COUNT(DISTINCT p.id) AS total_pedidos
FROM detalles_pedido dp
JOIN pedidos p ON p.id = dp.pedido_id
JOIN discos d ON d.id = dp.disco_id
JOIN categorias c ON c.id = d.categoria_id
WHERE p.estado = 'APROBADO'
GROUP BY d.id, dp.album, dp.artista, dp.formato, d.imagen, d.stock, c.nombre
ORDER BY total_unidades DESC, total_facturado DESC
LIMIT :limite;

-- name: ranking_categorias
SELECT
    c.id AS categoria_id,
    c.nombre AS categoria_nombre,
    c.slug AS categoria_slug,
    c.imagen AS categoria_imagen,
    COUNT(DISTINCT p.id) AS total_pedidos,
    SUM(dp.cantidad) AS total_unidades,
    SUM(dp.cantidad * dp.precio_unitario) AS total_facturado
FROM detalles_pedido dp
JOIN pedidos p ON p.id = dp.pedido_id
JOIN discos d ON d.id = dp.disco_id
JOIN categorias c ON c.id = d.categoria_id
WHERE p.estado = 'APROBADO'
GROUP BY c.id, c.nombre, c.slug, c.imagen
ORDER BY total_facturado DESC, total_unidades DESC;

-- =============================================================================
-- New Records — Consultas SQL Analíticas y Reportes Administrativos (Fase 11)
-- =============================================================================
-- Este archivo documenta las consultas SQL analíticas de ventas en PostgreSQL.
-- Todas las consultas filtran estrictamente por pedidos con estado 'APROBADO',
-- garantizando que transacciones pendientes o canceladas no distorsionen los KPIs.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Resumen Global de Ventas y Métricas Clave
-- -----------------------------------------------------------------------------
-- Calcula la facturación total aprobada, número de pedidos completados,
-- unidades físicas vendidas y el ticket promedio de compra.
SELECT
    COALESCE(COUNT(DISTINCT p.id), 0) AS total_pedidos_aprobados,
    COALESCE(SUM(dp.cantidad), 0) AS total_unidades_vendidas,
    COALESCE(SUM(dp.cantidad * dp.precio_unitario), 0.00) AS total_ingresos_facturados,
    CASE 
        WHEN COUNT(DISTINCT p.id) > 0 
        THEN ROUND(SUM(dp.cantidad * dp.precio_unitario) / COUNT(DISTINCT p.id), 2)
        ELSE 0.00 
    END AS ticket_promedio
FROM pedidos p
JOIN detalles_pedido dp ON dp.pedido_id = p.id
WHERE p.estado = 'APROBADO';


-- -----------------------------------------------------------------------------
-- 2. Reporte de Ventas Diario
-- -----------------------------------------------------------------------------
-- Agrupa las ventas por día cronológico (UTC), mostrando el volumen de órdenes,
-- cantidad de discos despachados y monto total acumulado por jornada.
SELECT
    DATE_TRUNC('day', p.fecha_creacion)::date AS fecha,
    TO_CHAR(DATE_TRUNC('day', p.fecha_creacion)::date, 'YYYY-MM-DD') AS fecha_formateada,
    COUNT(DISTINCT p.id) AS pedidos_aprobados,
    SUM(dp.cantidad) AS unidades_vendidas,
    ROUND(SUM(dp.cantidad * dp.precio_unitario), 2) AS total_facturado
FROM pedidos p
JOIN detalles_pedido dp ON dp.pedido_id = p.id
WHERE p.estado = 'APROBADO'
GROUP BY DATE_TRUNC('day', p.fecha_creacion)::date
ORDER BY fecha DESC;


-- -----------------------------------------------------------------------------
-- 3. Reporte de Ventas Semanal
-- -----------------------------------------------------------------------------
-- Agrupa las ventas por semana del año (ISO Week), facilitando el análisis
-- de tendencias y estacionalidad a corto plazo.
SELECT
    DATE_TRUNC('week', p.fecha_creacion)::date AS inicio_semana,
    EXTRACT(YEAR FROM DATE_TRUNC('week', p.fecha_creacion))::integer AS anio,
    EXTRACT(WEEK FROM DATE_TRUNC('week', p.fecha_creacion))::integer AS semana,
    COUNT(DISTINCT p.id) AS pedidos_aprobados,
    SUM(dp.cantidad) AS unidades_vendidas,
    ROUND(SUM(dp.cantidad * dp.precio_unitario), 2) AS total_facturado
FROM pedidos p
JOIN detalles_pedido dp ON dp.pedido_id = p.id
WHERE p.estado = 'APROBADO'
GROUP BY DATE_TRUNC('week', p.fecha_creacion)::date
ORDER BY inicio_semana DESC;


-- -----------------------------------------------------------------------------
-- 4. Reporte de Ventas Mensual
-- -----------------------------------------------------------------------------
-- Agrupa la facturación por mes calendario.
SELECT
    DATE_TRUNC('month', p.fecha_creacion)::date AS periodo_mes,
    EXTRACT(YEAR FROM DATE_TRUNC('month', p.fecha_creacion))::integer AS anio,
    EXTRACT(MONTH FROM DATE_TRUNC('month', p.fecha_creacion))::integer AS mes,
    TO_CHAR(DATE_TRUNC('month', p.fecha_creacion)::date, 'YYYY-MM') AS etiqueta_mes,
    COUNT(DISTINCT p.id) AS pedidos_aprobados,
    SUM(dp.cantidad) AS unidades_vendidas,
    ROUND(SUM(dp.cantidad * dp.precio_unitario), 2) AS total_facturado
FROM pedidos p
JOIN detalles_pedido dp ON dp.pedido_id = p.id
WHERE p.estado = 'APROBADO'
GROUP BY DATE_TRUNC('month', p.fecha_creacion)::date
ORDER BY periodo_mes DESC;


-- -----------------------------------------------------------------------------
-- 5. Reporte de Ventas Anual
-- -----------------------------------------------------------------------------
-- Consolida todos los pedidos aprobados de cada año calendario.
SELECT
    DATE_TRUNC('year', p.fecha_creacion)::date AS periodo_anio,
    EXTRACT(YEAR FROM p.fecha_creacion)::integer AS anio,
    COUNT(DISTINCT p.id) AS pedidos_aprobados,
    SUM(dp.cantidad) AS unidades_vendidas,
    ROUND(SUM(dp.cantidad * dp.precio_unitario), 2) AS total_facturado
FROM pedidos p
JOIN detalles_pedido dp ON dp.pedido_id = p.id
WHERE p.estado = 'APROBADO'
GROUP BY DATE_TRUNC('year', p.fecha_creacion)::date,
         EXTRACT(YEAR FROM p.fecha_creacion)::integer
ORDER BY periodo_anio DESC;


-- -----------------------------------------------------------------------------
-- 6. Ranking de Discos Más Vendidos (Top Products)
-- -----------------------------------------------------------------------------
-- Combina 'detalles_pedido', 'pedidos' y 'discos' para rankear los álbumes más
-- populares por volumen de unidades y facturación generada, indicando formato.
SELECT
    d.id AS disco_id,
    dp.album,
    dp.artista,
    dp.formato,
    d.imagen,
    d.stock AS stock_actual,
    c.nombre AS categoria_nombre,
    SUM(dp.cantidad) AS unidades_vendidas,
    ROUND(SUM(dp.cantidad * dp.precio_unitario), 2) AS total_recaudado,
    COUNT(DISTINCT p.id) AS num_pedidos
FROM detalles_pedido dp
JOIN pedidos p ON p.id = dp.pedido_id
JOIN discos d ON d.id = dp.disco_id
JOIN categorias c ON c.id = d.categoria_id
WHERE p.estado = 'APROBADO'
GROUP BY d.id, dp.album, dp.artista, dp.formato, d.imagen, d.stock, c.nombre
ORDER BY unidades_vendidas DESC, total_recaudado DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- 7. Ranking de Géneros Musicales Más Vendidos (Top Categories)
-- -----------------------------------------------------------------------------
-- Agrupa las ventas consolidadas por categoría musical, permitiendo identificar
-- los estilos y géneros más demandados en la tienda.
SELECT
    c.id AS categoria_id,
    c.nombre AS categoria_nombre,
    c.slug AS categoria_slug,
    c.imagen AS categoria_imagen,
    COUNT(DISTINCT p.id) AS total_pedidos,
    SUM(dp.cantidad) AS unidades_vendidas,
    ROUND(SUM(dp.cantidad * dp.precio_unitario), 2) AS total_facturado
FROM detalles_pedido dp
JOIN pedidos p ON p.id = dp.pedido_id
JOIN discos d ON d.id = dp.disco_id
JOIN categorias c ON c.id = d.categoria_id
WHERE p.estado = 'APROBADO'
GROUP BY c.id, c.nombre, c.slug, c.imagen
ORDER BY total_facturado DESC, unidades_vendidas DESC;

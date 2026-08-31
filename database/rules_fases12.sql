-- =============================================================================
-- New Records — Integridad Avanzada, Triggers y Restricciones (Fase 12)
-- =============================================================================
-- Este archivo se ejecuta de forma idempotente desde init_db.py y consolida
-- las restricciones relacionales CHECK, UNIQUE y triggers de consistencia.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. Restricciones de texto compartidas con la validación de formularios
-- -----------------------------------------------------------------------------
DO $$ BEGIN
    ALTER TABLE categorias
        ADD CONSTRAINT ck_categorias_nombre_valido
        CHECK (char_length(btrim(nombre)) BETWEEN 2 AND 80);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE discos
        ADD CONSTRAINT ck_discos_album_valido
        CHECK (char_length(btrim(album)) BETWEEN 1 AND 150);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE discos
        ADD CONSTRAINT ck_discos_artista_valido
        CHECK (char_length(btrim(artista)) BETWEEN 1 AND 120);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE discos
        ADD CONSTRAINT ck_discos_descripcion_valida
        CHECK (char_length(btrim(descripcion)) > 0);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE metodos_pago
        ADD CONSTRAINT ck_metodos_pago_titular_valido
        CHECK (char_length(btrim(titular)) BETWEEN 3 AND 120);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE verificaciones_tarjeta
        ADD CONSTRAINT ck_verificaciones_titular_valido
        CHECK (char_length(btrim(titular)) BETWEEN 3 AND 120);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- -----------------------------------------------------------------------------
-- 1. Restricciones de Calidad en Catálogo de Discos
-- -----------------------------------------------------------------------------
ALTER TABLE discos
    DROP CONSTRAINT IF EXISTS ck_discos_stock_no_negativo;
ALTER TABLE discos
    ADD CONSTRAINT ck_discos_stock_no_negativo
    CHECK (stock >= 0);

ALTER TABLE discos
    DROP CONSTRAINT IF EXISTS ck_discos_precio_base_positivo;
ALTER TABLE discos
    ADD CONSTRAINT ck_discos_precio_base_positivo
    CHECK (precio_base > 0);

ALTER TABLE discos
    DROP CONSTRAINT IF EXISTS ck_discos_peso_positivo;
ALTER TABLE discos
    ADD CONSTRAINT ck_discos_peso_positivo
    CHECK (peso_kg > 0);

ALTER TABLE discos
    DROP CONSTRAINT IF EXISTS ck_discos_costo_envio_no_negativo;
ALTER TABLE discos
    ADD CONSTRAINT ck_discos_costo_envio_no_negativo
    CHECK (costo_envio_por_kg >= 0);

ALTER TABLE discos
    DROP CONSTRAINT IF EXISTS ck_discos_costo_embalaje_no_negativo;
ALTER TABLE discos
    ADD CONSTRAINT ck_discos_costo_embalaje_no_negativo
    CHECK (costo_embalaje >= 0);

ALTER TABLE discos
    DROP CONSTRAINT IF EXISTS ck_discos_formato;
ALTER TABLE discos
    ADD CONSTRAINT ck_discos_formato
    CHECK (formato IN ('CD', 'VINILO'));


-- -----------------------------------------------------------------------------
-- 2. Restricciones en Categorías
-- -----------------------------------------------------------------------------
ALTER TABLE categorias
    DROP CONSTRAINT IF EXISTS ck_categorias_slug_formato;
ALTER TABLE categorias
    ADD CONSTRAINT ck_categorias_slug_formato
    CHECK (slug ~ '^[a-z0-9-]+$');


-- -----------------------------------------------------------------------------
-- 3. Restricciones en Usuarios y Roles
-- -----------------------------------------------------------------------------
ALTER TABLE usuarios
    DROP CONSTRAINT IF EXISTS ck_usuarios_rol;
ALTER TABLE usuarios
    ADD CONSTRAINT ck_usuarios_rol
    CHECK (rol IN ('cliente', 'administrador'));


-- -----------------------------------------------------------------------------
-- 4. Restricciones en Pedidos y Transacciones de Pago
-- -----------------------------------------------------------------------------
ALTER TABLE pedidos
    DROP CONSTRAINT IF EXISTS ck_pedidos_estado;
ALTER TABLE pedidos
    ADD CONSTRAINT ck_pedidos_estado
    CHECK (estado IN ('PENDIENTE', 'APROBADO', 'RECHAZADO'));

ALTER TABLE pedidos
    DROP CONSTRAINT IF EXISTS ck_pedidos_total_no_negativo;
ALTER TABLE pedidos
    ADD CONSTRAINT ck_pedidos_total_no_negativo
    CHECK (total >= 0);

ALTER TABLE pedidos
    DROP CONSTRAINT IF EXISTS ck_pedidos_rechazo_con_motivo;
ALTER TABLE pedidos
    ADD CONSTRAINT ck_pedidos_rechazo_con_motivo
    CHECK ((estado <> 'RECHAZADO') OR (motivo_rechazo IS NOT NULL AND length(trim(motivo_rechazo)) > 0));

ALTER TABLE detalles_pedido
    DROP CONSTRAINT IF EXISTS ck_detalles_pedido_cantidad_positiva;
ALTER TABLE detalles_pedido
    ADD CONSTRAINT ck_detalles_pedido_cantidad_positiva
    CHECK (cantidad > 0);

ALTER TABLE detalles_pedido
    DROP CONSTRAINT IF EXISTS ck_detalles_pedido_precio_no_negativo;
ALTER TABLE detalles_pedido
    ADD CONSTRAINT ck_detalles_pedido_precio_no_negativo
    CHECK (precio_unitario >= 0);

ALTER TABLE transacciones_pago
    DROP CONSTRAINT IF EXISTS ck_transacciones_monto_no_negativo;
ALTER TABLE transacciones_pago
    ADD CONSTRAINT ck_transacciones_monto_no_negativo
    CHECK (monto >= 0);

ALTER TABLE transacciones_pago
    DROP CONSTRAINT IF EXISTS ck_transacciones_estado;
ALTER TABLE transacciones_pago
    ADD CONSTRAINT ck_transacciones_estado
    CHECK (estado IN ('PENDIENTE', 'APROBADA', 'RECHAZADA'));


-- -----------------------------------------------------------------------------
-- 5. Restricciones en Facturas y Comprobantes
-- -----------------------------------------------------------------------------
ALTER TABLE facturas
    DROP CONSTRAINT IF EXISTS ck_facturas_tipo;
ALTER TABLE facturas
    ADD CONSTRAINT ck_facturas_tipo
    CHECK (tipo IN ('COMPROBANTE_PENDIENTE', 'FACTURA_FINAL'));


-- -----------------------------------------------------------------------------
-- 6. Trigger de Actualización Automática de Timestamp
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION actualizar_timestamp_modificacion()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.fecha_actualizacion := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_discos_actualizar_fecha ON discos;
CREATE TRIGGER trg_discos_actualizar_fecha
BEFORE UPDATE ON discos
FOR EACH ROW
EXECUTE FUNCTION actualizar_timestamp_modificacion();

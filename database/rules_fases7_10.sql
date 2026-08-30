-- Reglas PostgreSQL de las fases 7 a 10 de New Records.
-- Este archivo se ejecuta de forma idempotente desde init_db.py.

ALTER TABLE metodos_pago
    DROP CONSTRAINT IF EXISTS ck_metodos_pago_anio_vencimiento;
ALTER TABLE metodos_pago
    ADD CONSTRAINT ck_metodos_pago_anio_vencimiento
    CHECK (anio_vencimiento BETWEEN 2020 AND 2100);

ALTER TABLE verificaciones_tarjeta
    DROP CONSTRAINT IF EXISTS ck_verificaciones_intentos;
ALTER TABLE verificaciones_tarjeta
    ADD CONSTRAINT ck_verificaciones_intentos
    CHECK (intentos BETWEEN 0 AND 3);

ALTER TABLE verificaciones_tarjeta
    DROP CONSTRAINT IF EXISTS ck_verificaciones_anio_vencimiento;
ALTER TABLE verificaciones_tarjeta
    ADD CONSTRAINT ck_verificaciones_anio_vencimiento
    CHECK (anio_vencimiento BETWEEN 2020 AND 2100);

ALTER TABLE metodos_pago
    DROP CONSTRAINT IF EXISTS ck_metodos_pago_marca;
ALTER TABLE metodos_pago
    ADD CONSTRAINT ck_metodos_pago_marca
    CHECK (marca IN ('VISA', 'MASTERCARD', 'AMEX'));

ALTER TABLE verificaciones_tarjeta
    DROP CONSTRAINT IF EXISTS ck_verificaciones_marca;
ALTER TABLE verificaciones_tarjeta
    ADD CONSTRAINT ck_verificaciones_marca
    CHECK (marca IN ('VISA', 'MASTERCARD', 'AMEX'));

WITH metodos_repetidos AS (
    SELECT id,
           row_number() OVER (
               PARTITION BY usuario_id
               ORDER BY fecha_verificacion DESC, id DESC
           ) AS posicion
      FROM metodos_pago
     WHERE activo AND predeterminado
)
UPDATE metodos_pago AS metodo
   SET predeterminado = false
  FROM metodos_repetidos AS repetido
 WHERE metodo.id = repetido.id
   AND repetido.posicion > 1;

CREATE UNIQUE INDEX IF NOT EXISTS uq_metodo_pago_predeterminado_activo
    ON metodos_pago (usuario_id)
    WHERE activo AND predeterminado;

CREATE OR REPLACE FUNCTION validar_vencimiento_tarjeta()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    ultimo_dia_vigencia date;
BEGIN
    ultimo_dia_vigencia :=
        (make_date(NEW.anio_vencimiento, NEW.mes_vencimiento, 1)
         + interval '1 month - 1 day')::date;

    IF ultimo_dia_vigencia < CURRENT_DATE THEN
        RAISE EXCEPTION 'La tarjeta se encuentra vencida.'
            USING ERRCODE = '23514';
    END IF;

    IF NEW.anio_vencimiento > EXTRACT(YEAR FROM CURRENT_DATE)::integer + 20 THEN
        RAISE EXCEPTION 'El vencimiento de la tarjeta supera el límite permitido.'
            USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_metodos_pago_vencimiento ON metodos_pago;
CREATE TRIGGER trg_metodos_pago_vencimiento
BEFORE INSERT OR UPDATE OF mes_vencimiento, anio_vencimiento
ON metodos_pago
FOR EACH ROW
EXECUTE FUNCTION validar_vencimiento_tarjeta();

DROP TRIGGER IF EXISTS trg_verificaciones_tarjeta_vencimiento
ON verificaciones_tarjeta;
CREATE TRIGGER trg_verificaciones_tarjeta_vencimiento
BEFORE INSERT OR UPDATE OF mes_vencimiento, anio_vencimiento
ON verificaciones_tarjeta
FOR EACH ROW
EXECUTE FUNCTION validar_vencimiento_tarjeta();

CREATE OR REPLACE PROCEDURE aprobar_pedido_new_records(
    IN p_numero varchar,
    IN p_admin_id integer,
    INOUT p_exito boolean,
    INOUT p_mensaje text
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_pedido_id integer;
    v_estado varchar(20);
    v_detalle record;
    v_stock integer;
BEGIN
    p_exito := false;
    p_mensaje := '';

    SELECT id, estado
      INTO v_pedido_id, v_estado
      FROM pedidos
     WHERE numero = p_numero
     FOR UPDATE;

    IF NOT FOUND THEN
        p_mensaje := 'Pedido no encontrado.';
        RETURN;
    END IF;

    IF v_estado <> 'PENDIENTE' THEN
        p_mensaje := format(
            'El pedido ya fue procesado anteriormente (Estado: %s).',
            v_estado
        );
        RETURN;
    END IF;

    IF NOT EXISTS (
        SELECT 1
          FROM usuarios
         WHERE id = p_admin_id
           AND rol = 'administrador'
           AND activo
    ) THEN
        p_mensaje := 'El administrador indicado no es válido o está inactivo.';
        RETURN;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM detalles_pedido WHERE pedido_id = v_pedido_id
    ) THEN
        p_mensaje := 'El pedido no contiene discos para aprobar.';
        RETURN;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM transacciones_pago WHERE pedido_id = v_pedido_id
    ) THEN
        p_mensaje := 'El pedido no tiene una transacción de pago asociada.';
        RETURN;
    END IF;

    -- El orden estable por disco_id evita interbloqueos entre pedidos concurrentes.
    FOR v_detalle IN
        SELECT disco_id, album, cantidad
          FROM detalles_pedido
         WHERE pedido_id = v_pedido_id
         ORDER BY disco_id
    LOOP
        SELECT stock
          INTO v_stock
          FROM discos
         WHERE id = v_detalle.disco_id
         FOR UPDATE;

        IF NOT FOUND THEN
            p_mensaje := format(
                'El disco "%s" ya no existe en el inventario.',
                v_detalle.album
            );
            RETURN;
        END IF;

        IF v_stock < v_detalle.cantidad THEN
            p_mensaje := format(
                'No hay stock suficiente para "%s". Requerido: %s, disponible: %s.',
                v_detalle.album,
                v_detalle.cantidad,
                v_stock
            );
            RETURN;
        END IF;
    END LOOP;

    UPDATE discos AS d
       SET stock = d.stock - detalle.cantidad,
           fecha_actualizacion = CURRENT_TIMESTAMP
      FROM detalles_pedido AS detalle
     WHERE detalle.pedido_id = v_pedido_id
       AND d.id = detalle.disco_id;

    UPDATE pedidos
       SET estado = 'APROBADO',
           administrador_revisor_id = p_admin_id,
           fecha_revision = CURRENT_TIMESTAMP,
           motivo_rechazo = NULL
     WHERE id = v_pedido_id;

    UPDATE transacciones_pago
       SET estado = 'APROBADA',
           fecha_procesamiento = CURRENT_TIMESTAMP
     WHERE pedido_id = v_pedido_id;

    p_exito := true;
    p_mensaje := format('Pedido %s aprobado exitosamente.', p_numero);
END;
$$;

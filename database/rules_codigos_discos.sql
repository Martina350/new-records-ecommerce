-- Generación automática y transaccional de códigos de discos por categoría.
-- Archivo idempotente: puede ejecutarse en instalaciones nuevas o existentes.

ALTER TABLE categorias
    ADD COLUMN IF NOT EXISTS prefijo_codigo VARCHAR(5);

-- Conserva los prefijos ya utilizados por los datos iniciales.
UPDATE categorias
SET prefijo_codigo = CASE slug
    WHEN 'rock' THEN 'ROC'
    WHEN 'pop' THEN 'POP'
    WHEN 'reggaeton' THEN 'REG'
    ELSE prefijo_codigo
END
WHERE prefijo_codigo IS NULL
  AND slug IN ('rock', 'pop', 'reggaeton');

-- Las categorías antiguas ajenas a los datos iniciales reciben un prefijo
-- inequívoco basado en su PK. Luego el administrador puede conservarlo.
UPDATE categorias
SET prefijo_codigo = 'C' || LPAD(id::TEXT, 4, '0')
WHERE prefijo_codigo IS NULL;

ALTER TABLE categorias
    ALTER COLUMN prefijo_codigo SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ix_categorias_prefijo_codigo
    ON categorias (prefijo_codigo);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_categorias_prefijo_codigo'
          AND conrelid = 'categorias'::regclass
    ) THEN
        ALTER TABLE categorias
            ADD CONSTRAINT ck_categorias_prefijo_codigo
            CHECK (prefijo_codigo ~ '^[A-Z0-9]{3,5}$');
    END IF;
END;
$$;

CREATE TABLE IF NOT EXISTS secuencias_codigo_categoria (
    categoria_id INTEGER PRIMARY KEY
        REFERENCES categorias(id) ON DELETE CASCADE,
    ultimo_numero INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT ck_secuencias_codigo_ultimo_numero
        CHECK (ultimo_numero >= 0)
);

-- Sincroniza instalaciones que ya contienen códigos NR-PREFIJO-NÚMERO.
INSERT INTO secuencias_codigo_categoria (categoria_id, ultimo_numero)
SELECT
    c.id,
    COALESCE(
        MAX(
            CASE
                WHEN d.codigo ~ ('^NR-' || c.prefijo_codigo || '-[0-9]+$')
                THEN SUBSTRING(d.codigo FROM '[0-9]+$')::INTEGER
                ELSE NULL
            END
        ),
        0
    )
FROM categorias AS c
LEFT JOIN discos AS d ON d.categoria_id = c.id
GROUP BY c.id
ON CONFLICT (categoria_id) DO UPDATE
SET ultimo_numero = GREATEST(
    secuencias_codigo_categoria.ultimo_numero,
    EXCLUDED.ultimo_numero
);

CREATE OR REPLACE FUNCTION generar_codigo_disco(p_categoria_id INTEGER)
RETURNS VARCHAR(30)
LANGUAGE plpgsql
AS $$
DECLARE
    v_prefijo VARCHAR(5);
    v_ultimo_numero INTEGER;
    v_maximo_existente INTEGER;
    v_siguiente INTEGER;
    v_sufijo TEXT;
BEGIN
    SELECT prefijo_codigo
    INTO v_prefijo
    FROM categorias
    WHERE id = p_categoria_id
      AND activo = TRUE
    FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'La categoría % no existe o está inactiva.', p_categoria_id
            USING ERRCODE = '23503';
    END IF;

    INSERT INTO secuencias_codigo_categoria (categoria_id, ultimo_numero)
    VALUES (p_categoria_id, 0)
    ON CONFLICT (categoria_id) DO NOTHING;

    SELECT ultimo_numero
    INTO v_ultimo_numero
    FROM secuencias_codigo_categoria
    WHERE categoria_id = p_categoria_id
    FOR UPDATE;

    SELECT COALESCE(
        MAX(SUBSTRING(codigo FROM '[0-9]+$')::INTEGER),
        0
    )
    INTO v_maximo_existente
    FROM discos
    WHERE categoria_id = p_categoria_id
      AND codigo ~ ('^NR-' || v_prefijo || '-[0-9]+$');

    v_siguiente := GREATEST(v_ultimo_numero, v_maximo_existente) + 1;

    UPDATE secuencias_codigo_categoria
    SET ultimo_numero = v_siguiente
    WHERE categoria_id = p_categoria_id;

    v_sufijo := CASE
        WHEN v_siguiente < 1000 THEN LPAD(v_siguiente::TEXT, 3, '0')
        ELSE v_siguiente::TEXT
    END;

    RETURN 'NR-' || v_prefijo || '-' || v_sufijo;
END;
$$;

REVOKE ALL ON FUNCTION generar_codigo_disco(INTEGER) FROM PUBLIC;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'new_records_app') THEN
        GRANT SELECT, INSERT, UPDATE ON secuencias_codigo_categoria
            TO new_records_app;
        GRANT EXECUTE ON FUNCTION generar_codigo_disco(INTEGER)
            TO new_records_app;
    END IF;

    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'new_records_backup') THEN
        GRANT SELECT ON secuencias_codigo_categoria TO new_records_backup;
    END IF;
END;
$$;

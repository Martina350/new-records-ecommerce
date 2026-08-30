-- =============================================================================
-- New Records — Definición de Roles y Principio de Mínimo Privilegio (Fase 12)
-- =============================================================================
-- Este script define los roles de seguridad de base de datos para separar
-- las operaciones de la aplicación web, tareas de respaldo y administración.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Rol de Aplicación Web: new_records_app
-- -----------------------------------------------------------------------------
-- Propósito: Utilizado exclusivamente por Flask para las operaciones diarias.
-- Privilegios: DML completo (SELECT, INSERT, UPDATE, DELETE) en tablas del esquema
-- y uso de secuencias. NO posee permisos de DDL destructivo (DROP, TRUNCATE)
-- ni atributos de SUPERUSER.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'new_records_app') THEN
        CREATE ROLE new_records_app WITH LOGIN PASSWORD 'configurar_en_env';
    END IF;
END
$$;

-- Permisos sobre el esquema público
GRANT USAGE ON SCHEMA public TO new_records_app;

-- Permisos DML en todas las tablas existentes y futuras
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO new_records_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO new_records_app;

-- Permisos en todas las secuencias
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO new_records_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO new_records_app;

-- Permisos de ejecución en procedimientos almacenados y funciones
GRANT EXECUTE ON ALL ROUTINES IN SCHEMA public TO new_records_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON ROUTINES TO new_records_app;


-- -----------------------------------------------------------------------------
-- 2. Rol de Respaldos: new_records_backup
-- -----------------------------------------------------------------------------
-- Propósito: Utilizado por pg_dump y scripts automáticos de copias de seguridad.
-- Privilegios: Estrictamente LECTURA (SELECT) en tablas y secuencias.
-- No puede modificar ningún dato ni estructura.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'new_records_backup') THEN
        CREATE ROLE new_records_backup WITH LOGIN PASSWORD 'configurar_en_env';
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO new_records_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO new_records_backup;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO new_records_backup;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO new_records_backup;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO new_records_backup;


-- -----------------------------------------------------------------------------
-- 3. Rol Administrativo y Migraciones: new_records_admin
-- -----------------------------------------------------------------------------
-- Propósito: Mantenimiento, migraciones de esquema e inicialización.
-- Privilegios: Propietario de los objetos y control completo.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'new_records_admin') THEN
        CREATE ROLE new_records_admin WITH LOGIN CREATEDB PASSWORD 'configurar_en_env';
    END IF;
END
$$;

GRANT ALL PRIVILEGES ON DATABASE new_records_db TO new_records_admin;
GRANT ALL ON SCHEMA public TO new_records_admin;

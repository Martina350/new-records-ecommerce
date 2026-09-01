-- =============================================================================
-- New Records — Roles PostgreSQL y mínimo privilegio (Fase 12)
-- =============================================================================
-- Debe ejecutarse mediante configure_db_roles.py con un usuario bootstrap.
-- Las contraseñas se configuran desde .env y nunca se incluyen en este archivo.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'new_records_admin') THEN
        CREATE ROLE new_records_admin NOLOGIN CREATEDB NOSUPERUSER NOCREATEROLE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'new_records_app') THEN
        CREATE ROLE new_records_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'new_records_backup') THEN
        CREATE ROLE new_records_backup NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;
END
$$;

DO $$
DECLARE
    objeto record;
BEGIN
    EXECUTE format('ALTER DATABASE %I OWNER TO new_records_admin', current_database());
    ALTER SCHEMA public OWNER TO new_records_admin;

    FOR objeto IN
        SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'public'
    LOOP
        EXECUTE format(
            'ALTER TABLE %I.%I OWNER TO new_records_admin',
            objeto.schemaname,
            objeto.tablename
        );
    END LOOP;

    FOR objeto IN
        SELECT sequence_schema, sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema = 'public'
    LOOP
        EXECUTE format(
            'ALTER SEQUENCE %I.%I OWNER TO new_records_admin',
            objeto.sequence_schema,
            objeto.sequence_name
        );
    END LOOP;

    FOR objeto IN
        SELECT n.nspname AS esquema,
               p.proname AS rutina,
               pg_get_function_identity_arguments(p.oid) AS argumentos
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public'
    LOOP
        EXECUTE format(
            'ALTER ROUTINE %I.%I(%s) OWNER TO new_records_admin',
            objeto.esquema,
            objeto.rutina,
            objeto.argumentos
        );
    END LOOP;
END
$$;

DO $$
BEGIN
    EXECUTE format('REVOKE ALL PRIVILEGES ON DATABASE %I FROM PUBLIC', current_database());
    EXECUTE format(
        'GRANT ALL PRIVILEGES ON DATABASE %I TO new_records_admin',
        current_database()
    );
    EXECUTE format(
        'GRANT CONNECT ON DATABASE %I TO new_records_app, new_records_backup',
        current_database()
    );
END
$$;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO new_records_admin;
GRANT USAGE ON SCHEMA public TO new_records_app, new_records_backup;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;
REVOKE EXECUTE ON ALL ROUTINES IN SCHEMA public FROM PUBLIC;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO new_records_app;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO new_records_app;
GRANT EXECUTE ON ALL ROUTINES IN SCHEMA public TO new_records_app;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO new_records_backup;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO new_records_backup;

ALTER DEFAULT PRIVILEGES FOR ROLE new_records_admin IN SCHEMA public
    REVOKE EXECUTE ON ROUTINES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE new_records_admin IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO new_records_app;
ALTER DEFAULT PRIVILEGES FOR ROLE new_records_admin IN SCHEMA public
    GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO new_records_app;
ALTER DEFAULT PRIVILEGES FOR ROLE new_records_admin IN SCHEMA public
    GRANT EXECUTE ON ROUTINES TO new_records_app;
ALTER DEFAULT PRIVILEGES FOR ROLE new_records_admin IN SCHEMA public
    GRANT SELECT ON TABLES TO new_records_backup;
ALTER DEFAULT PRIVILEGES FOR ROLE new_records_admin IN SCHEMA public
    GRANT SELECT ON SEQUENCES TO new_records_backup;

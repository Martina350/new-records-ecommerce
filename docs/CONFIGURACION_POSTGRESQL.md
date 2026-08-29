# Configuración inicial de PostgreSQL

Esta guía completa la conexión de la Fase 2. No crea todavía tablas ni datos de New Records.

## Datos definidos para desarrollo

- Base de datos: `new_records_db`.
- Usuario de aplicación: `new_records_app`.
- Host local: `localhost`.
- Puerto: `5432`.
- Codificación: UTF-8.

La aplicación no debe conectarse habitualmente con el superusuario `postgres`.

## Creación mediante pgAdmin

1. Abrir pgAdmin y conectarse al servidor PostgreSQL local como administrador.
2. Abrir Query Tool sobre la base administrativa `postgres`.
3. Crear el usuario `new_records_app` con una contraseña local segura.
4. Crear `new_records_db` indicando a `new_records_app` como propietario.
5. Confirmar que el usuario puede conectarse a la nueva base.
6. Copiar la misma contraseña únicamente en `DB_PASSWORD` del archivo local `.env`.

Las operaciones SQL equivalentes son:

```sql
CREATE ROLE new_records_app
WITH LOGIN PASSWORD 'REEMPLAZAR_POR_UNA_CONTRASENA_LOCAL_SEGURA';

CREATE DATABASE new_records_db
WITH OWNER = new_records_app
ENCODING = 'UTF8';
```

Si el rol ya existe, no debe intentarse crearlo nuevamente. En ese caso se puede asignar una nueva contraseña local al rol existente y comprobar la propiedad de la base desde pgAdmin.

## Verificación desde el proyecto

Después de completar `.env`, activar el entorno virtual y ejecutar el comando Flask `check-db`. El resultado esperado es el mensaje “Conexión con PostgreSQL correcta”.

El comando realiza solamente una consulta `SELECT 1`; no crea ni modifica información.

## Seguridad

- No copiar la contraseña real en este documento ni en `.env.example`.
- No subir `.env` a Git.
- No utilizar la contraseña del ejemplo literalmente.
- No habilitar autenticación `trust` ni modificar `pg_hba.conf` para evitar la contraseña.


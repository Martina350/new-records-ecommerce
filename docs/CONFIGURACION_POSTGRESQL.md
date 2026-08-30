# Configuración de PostgreSQL para New Records

New Records separa tres responsabilidades técnicas:

- `new_records_admin`: propietario del esquema, migraciones e inicialización.
- `new_records_app`: conexión diaria de Flask con permisos DML.
- `new_records_backup`: lectura destinada a `pg_dump`.

La aplicación nunca debe ejecutarse con el superusuario `postgres`.

## 1. Crear solamente la base vacía

Desde pgAdmin, conectado como administrador, crear `new_records_db` con
codificación UTF-8. No es necesario crear manualmente los tres roles.

## 2. Configurar `.env`

Copiar `.env.example` como `.env` y asignar claves diferentes y aleatorias a:

- `DB_PASSWORD`.
- `DB_ADMIN_PASSWORD`.
- `DB_BACKUP_PASSWORD`.
- `DB_BOOTSTRAP_PASSWORD`.

`DB_BOOTSTRAP_USER` y su clave se usan solamente durante el aprovisionamiento.
No deben utilizarse para iniciar Flask ni compartirse en Git.

Cuando `pg_dump`, `pg_restore`, `createdb` y `dropdb` no estén en `PATH`, definir
`POSTGRES_BIN` con la carpeta `bin` de la instalación.

## 3. Aplicar roles y permisos

Con el entorno virtual activo:

```powershell
python configure_db_roles.py
```

El script crea o actualiza los roles, transfiere la propiedad de la base, esquema,
tablas, secuencias y rutinas a `new_records_admin`, elimina permisos implícitos de
`PUBLIC` y concede únicamente los privilegios necesarios.

Después de que termine correctamente puede retirarse
`DB_BOOTSTRAP_PASSWORD` del `.env` de uso cotidiano y conservarse en un gestor de
secretos administrativo.

## 4. Inicializar y comprobar

```powershell
python init_db.py
python -m flask --app app check-db
python -m pytest -q
```

El comando `check-db` debe informar que Flask se conecta como
`new_records_app`; ese rol no debe ser propietario de la base ni de las tablas.

Para ejecutar la auditoría directa de privilegios:

```powershell
$env:RUN_DB_SECURITY_TESTS="1"
python -m pytest tests/test_seguridad_respaldos.py -v
```

## Seguridad

- No versionar `.env`, dumps, contraseñas ni claves reales.
- Rotar cualquier credencial que alguna vez haya aparecido en un commit.
- Después de cambiar `ADMIN_PASSWORD` o `CLIENTE_DEMO_PASSWORD`, ejecutar
  `python init_db.py` para actualizar sus hashes en PostgreSQL.
- No habilitar autenticación `trust` para simplificar la instalación.
- Usar `SESSION_COOKIE_SECURE=1` cuando el sitio funcione sobre HTTPS.

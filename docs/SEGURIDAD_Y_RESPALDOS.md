# Seguridad, Integridad y Respaldos en New Records

Este documento describe la arquitectura de seguridad relacional, las políticas de mínimo privilegio y los procedimientos operativos de copias de seguridad y recuperación para la plataforma **New Records**.

---

## 1. Roles y Principio de Mínimo Privilegio

La aplicación sigue el principio de mínimo privilegio en PostgreSQL, separando las responsabilidades en tres roles técnicos:

| Rol | Tipo de Acceso | Privilegios Otorgados | Uso Previsto |
|---|---|---|---|
| `new_records_app` | Aplicación Web (DML) | `SELECT, INSERT, UPDATE, DELETE` en tablas y secuencias. `EXECUTE` en funciones y procedimientos. | Conexión operativa estándar de Flask en `.env`. Sin permisos de `DROP`, `TRUNCATE` ni `SUPERUSER`. |
| `new_records_backup` | Copias de Seguridad | `SELECT` en todas las tablas y secuencias. | Utilizado por `pg_dump` y cron jobs de respaldo. Incapaz de alterar registros. |
| `new_records_admin` | Mantenimiento / DDL | `ALL PRIVILEGES` en la base de datos `new_records_db`. | Ejecución de `init_db.py`, creación de extensiones y migraciones estructurales. |

El script [`database/roles_seguridad.sql`](../database/roles_seguridad.sql)
transfiere la propiedad de los objetos al administrador y revoca los permisos
implícitos de `PUBLIC`. Las claves se aplican desde `.env`, sin escribirlas en SQL:

```powershell
python configure_db_roles.py
```

`init_db.py` utiliza `DB_ADMIN_USER`; Flask utiliza `DB_USER`; y el gestor de
respaldos utiliza `DB_BACKUP_USER`. Para auditar los permisos instalados:

```powershell
$env:RUN_DB_SECURITY_TESTS="1"
python -m pytest tests/test_seguridad_respaldos.py -v
```

---

## 2. Integridad de Datos en PostgreSQL

La consistencia y calidad de la información están garantizadas a nivel de motor relacional mediante reglas declaradas en [`database/rules_fases12.sql`](../database/rules_fases12.sql):

### 2.1 Restricciones de Calidad (`CHECK` Constraints)
- **Inventario y Precios**:
  - `discos.stock >= 0`: Imposibilita inventarios negativos.
  - `discos.precio_base > 0`: Todo álbum debe tener valor positivo.
  - `discos.peso_kg > 0`: Requerido para cálculo de envíos.
  - `discos.costo_envio_por_kg >= 0` y `discos.costo_embalaje >= 0`.
  - `discos.formato IN ('CD', 'VINILO')`: Restringe a los tipos polimórficos soportados.
- **Identidad y Acceso**:
  - `usuarios.rol IN ('cliente', 'administrador')`.
  - Validación de formato en correos y slugs de categorías.
- **Transaccionalidad y Estados**:
  - `pedidos.estado IN ('PENDIENTE', 'APROBADO', 'RECHAZADO')`.
  - Exigencia obligatoria de `motivo_rechazo` si el estado es `RECHAZADO`.
  - `transacciones_pago.estado IN ('PENDIENTE', 'APROBADA', 'RECHAZADA')`.
  - `facturas.tipo IN ('COMPROBANTE_PENDIENTE', 'FACTURA_FINAL')`.

### 2.2 Triggers de Base de Datos
- `trg_metodos_pago_vencimiento`: Comprueba en PostgreSQL que la tarjeta no esté vencida ni supere el límite razonable de 20 años futuros.
- `trg_discos_actualizar_fecha`: Actualiza automáticamente el campo `fecha_actualizacion` cada vez que se modifica un disco.

---

## 3. Seguridad en la Capa de Aplicación

1. **Gestión Criptográfica de Credenciales**:
   - Todas las contraseñas se almacenan como hashes generados mediante Werkzeug (`scrypt`). Nunca se persiste texto plano.
   - El PIN de verificación de tarjetas se cifra como hash temporal con caducidad estricta de 5 minutos y límite de 3 intentos.
2. **Cabeceras HTTP de Seguridad (Security Headers)**:
   - `X-Content-Type-Options: nosniff`: Previene el MIME type sniffing.
   - `X-Frame-Options: SAMEORIGIN`: Protege contra ataques de Clickjacking.
   - `X-XSS-Protection: 1; mode=block`: Filtro XSS en navegadores compatibles.
   - `Referrer-Policy: strict-origin-when-cross-origin`: Minimiza la fuga de datos de referencia en enlaces externos.
3. **Control de Acceso Basado en Roles (RBAC)**:
    - Decoradores `@login_requerido` y `@rol_requerido('administrador' | 'cliente')` aplicados en backend a nivel de controlador.
4. **Sesiones y formularios**:
   - Todos los formularios POST contienen un token CSRF validado por Flask-WTF.
   - El cierre de sesión utiliza POST y requiere token.
   - Las cookies de sesión son `HttpOnly`, `SameSite=Lax` y se marcan `Secure`
     cuando `SESSION_COOKIE_SECURE=1` en un entorno HTTPS.

---

## 4. Estrategia de Copias de Seguridad (Backups)

Los respaldos se almacenan localmente en el directorio [`backups/`](../backups/), el cual está explícitamente excluido del control de versiones en `.gitignore`.

### 4.1 Generación Mediante Comando CLI de Flask

Con el entorno virtual activado:

```bash
# Respaldo en formato SQL plano (por defecto)
python -m flask --app app crear-backup --formato plain

# Respaldo en formato binario comprimido de PostgreSQL
python -m flask --app app crear-backup --formato custom
```

### 4.2 Generación Manual Mediante `pg_dump`

```bash
# Respaldo completo en formato custom comprimido
pg_dump -h localhost -p 5432 -U new_records_backup -d new_records_db -F c -f backups/backup_manual.dump

# Respaldo en script SQL legible
pg_dump -h localhost -p 5432 -U new_records_backup -d new_records_db -F p -f backups/backup_manual.sql
```

---

## 5. Procedimiento de Restauración

La verificación recomendada crea un dump `custom`, lo restaura en una base con
nombre aleatorio y prefijo controlado, comprueba las tablas y datos iniciales, y
elimina el destino temporal incluso si ocurre un error:

```powershell
python -m flask --app app verificar-restauracion
```

Para ejecutar la misma comprobación como prueba de integración:

```powershell
$env:RUN_DB_RESTORE_TEST="1"
python -m pytest tests/test_seguridad_respaldos.py -v
```

### 5.1 Restauración desde Archivo Custom (`.dump`)

1. Asegurarse de que las conexiones activas estén cerradas o crear una base de datos limpia de destino:
   ```bash
   createdb -h localhost -p 5432 -U new_records_admin new_records_db_restaurada
   ```
2. Ejecutar `pg_restore`:
   ```bash
pg_restore -h localhost -p 5432 -U new_records_admin -d new_records_db_restaurada --no-owner --no-privileges -v backups/archivo_respaldo.dump
   ```

### 5.2 Restauración desde Archivo SQL Plano (`.sql`)

```bash
psql -h localhost -p 5432 -U new_records_admin -d new_records_db -f backups/archivo_respaldo.sql
```

---

## 6. Verificación Periódica de Consistencia

Para comprobar que la base de datos mantenga la integridad y estructura requerida, ejecutar:

```bash
python -m pytest -q
python -m flask --app app verificar-restauracion
```

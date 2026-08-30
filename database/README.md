# Base de datos de New Records

En la Fase 3, los modelos de `models.py` son la fuente principal del esquema y `init_db.py` crea las tablas iniciales mediante SQLAlchemy.

`schema_fase3.sql` es una referencia legible generada desde PostgreSQL después de validar el esquema. No reemplaza los modelos ni debe editarse para cambiar tablas.

`rules_fases7_10.sql` contiene las restricciones de pago, la validación dinámica de vencimiento mediante triggers y el procedimiento transaccional que aprueba pedidos con bloqueo de inventario. `init_db.py` aplica estas reglas de forma idempotente tanto en instalaciones nuevas como existentes.

`reports.sql` documenta los reportes diario, semanal, mensual y anual, además de
los rankings de discos y géneros. `rules_fases12.sql` contiene las restricciones
y triggers finales. `roles_seguridad.sql` se aplica mediante
`configure_db_roles.py`, nunca desde la cuenta web.

`schema_fase3.sql` conserva únicamente la referencia histórica de la Fase 3; las
reglas posteriores prevalecen sobre esa fotografía inicial.

Nunca debe añadirse a esta carpeta una copia de `.env`, contraseñas o respaldos con datos reales.

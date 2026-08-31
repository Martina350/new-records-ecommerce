# Reglas de Negocio — Plataforma New Records

Este documento especifica formalmente las reglas de negocio implementadas en los tres niveles de la arquitectura: **Interfaz de Usuario (Frontend)**, **Lógica de Aplicación (Flask/Python)** y **Motor de Base de Datos Relacional (PostgreSQL)**.

---

## 1. Identidad, Roles y Autenticación

1. **Roles del Sistema**:
   - `cliente`: Rol predeterminado para todo registro público. Permite explorar el catálogo, agregar al carrito, registrar tarjetas con verificación PIN, realizar pedidos y descargar comprobantes/facturas de sus compras.
   - `administrador`: Rol privilegiado para la gestión del catálogo (CRUD de discos y categorías), bandeja de pedidos pendientes, aprobación/rechazo de pedidos con auditoría, consulta de reportes analíticos y respaldos.
2. **Registro de Usuarios**:
   - El correo electrónico es obligatorio, se normaliza eliminando espacios y convirtiéndolo a minúsculas, y debe ser único en el sistema.
   - Las contraseñas deben contener al menos 8 caracteres y se almacenan exclusivamente como hashes criptográficos con Werkzeug (`scrypt`).
3. **Control de Acceso y Sesión**:
   - Toda ruta protegida valida la sesión del usuario mediante los decoradores `@login_requerido` y `@rol_requerido`.
   - Las sesiones almacenan únicamente los datos mínimos indispensables (`usuario_id`, `nombre`, `rol`). El cierre de sesión (`/logout`) limpia completamente la sesión.

---

## 2. Catálogo y Herencia Polimórfica

1. **Formatos Físicos Exclusivos**:
   - El catálogo comercializa únicamente música en formato físico: **CD** y **Vinilo** (`VINILO`).
   - Implementado mediante herencia de tabla única (Single Table Inheritance) en SQLAlchemy sobre la tabla `discos` con columna discriminadora `formato`.
2. **Cálculo Polimórfico de Precios y Envíos**:
   - Todo disco posee `precio_base > 0`, `peso_kg > 0`, `costo_envio_por_kg >= 0` y `costo_embalaje >= 0`.
   - El método polimórfico `precio_final()` calcula:
     $$\text{Precio Final} = \text{precio\_base} + (\text{peso\_kg} \times \text{costo\_envio\_por\_kg}) + \text{costo\_embalaje}$$
3. **Gestión y Eliminación Suave (Soft Delete)**:
   - Los discos y categorías nunca se eliminan físicamente de la base de datos si tienen historial de pedidos o relaciones activas.
   - Se utiliza el atributo booleano `activo`. Los productos inactivos no se muestran en el catálogo público ni pueden agregarse al carrito.
   - La desactivación de una categoría con discos activos exige confirmación explícita y desactiva lógicamente sus discos asociados en cascada controlada.
4. **Código Único Automático**:
   - Cada categoría define un prefijo único de 3 a 5 caracteres alfanuméricos en mayúsculas.
   - Al crear un disco, PostgreSQL reserva el siguiente consecutivo mediante `generar_codigo_disco(integer)` y produce un SKU como `NR-ROC-005`.
   - El formulario administrativo no permite escribir ni reemplazar manualmente este código.
   - El contador se bloquea dentro de la misma transacción que crea el disco, evitando duplicados por concurrencia; un rollback también revierte la reserva.
   - El prefijo de una categoría deja de ser editable cuando ya existen discos asociados, para conservar la coherencia histórica de sus SKU.

---

## 3. Carrito de Compras

1. **Persistencia en Sesión**:
   - El carrito reside en la sesión firmada de Flask del cliente (`session['carrito']`), estructurado como un diccionario `{disco_id: cantidad}`.
   - No permite cantidades que superen el stock físico disponible en tiempo real ni cantidades menores o iguales a cero.
2. **Restricción de Rol**:
   - Solo los usuarios con rol `cliente` pueden utilizar el carrito y procesar compras. Los administradores tienen prohibido comprar desde su cuenta administrativa.

---

## 4. Métodos de Pago y Verificación Segura por PIN

1. **Tokenización y Privacidad de Datos Financieros**:
   - El sistema **nunca** almacena el número de tarjeta completo (PAN) ni el código de seguridad (CVV).
   - Se almacenan únicamente los últimos 4 dígitos (`ultimos4`), la marca comercial (`VISA`, `MASTERCARD`, etc.), el titular y el mes/año de vencimiento.
2. **Verificación de Tarjeta mediante PIN Temporal**:
   - Al registrar una tarjeta, se genera una `VerificacionTarjeta` con un PIN aleatorio de 6 dígitos enviado por correo (simulado o SMTP).
   - El PIN se almacena como hash con vigencia de 5 minutos y un límite estricto de 3 intentos. Al tercer intento fallido, la verificación queda automáticamente bloqueada.
   - Solo tras la validación exitosa del PIN se crea el registro permanente `MetodoPago` con estado `activo = True`.
3. **Validación de Vigencia**:
   - Se rechaza cualquier tarjeta cuya fecha de vencimiento sea anterior al mes/año actual o superior a 20 años en el futuro.

---

## 5. Pedidos, Procedimiento de Aprobación y Facturación

1. **Ciclo de Vida del Pedido**:
   - **Checkout**: El cliente selecciona su método de pago verificado y confirma la orden. El pedido se crea con estado `PENDIENTE` y se genera de forma inmediata el `COMPROBANTE_PENDIENTE` en PDF. El stock aún no se descuenta en este punto.
   - **Líneas Inmutables**: Los registros en `detalles_pedido` guardan una copia histórica de álbum, artista, formato y precio unitario para preservar la fidelidad contable ante cambios futuros del catálogo.
2. **Aprobación Administrativa Atómica**:
   - El administrador audita el pedido en la bandeja administrativa.
   - Al aprobar, se ejecuta el procedimiento almacenado de PostgreSQL `aprobar_pedido_new_records` en una transacción atómica:
     1. Bloquea las filas de los discos involucrados (`FOR UPDATE`).
     2. Verifica que todas las líneas tengan existencias suficientes (`stock >= cantidad`).
     3. Descuenta atómicamente el stock físico.
     4. Actualiza el pedido a `APROBADO` y la transacción a `APROBADA`.
     5. Emite la `FACTURA_FINAL` en PDF y notifica al cliente por correo.
3. **Rechazo de Pedidos**:
   - Exige obligatoriamente el registro de un `motivo_rechazo`.
   - Actualiza el estado a `RECHAZADO` y la transacción a `RECHAZADA`.
   - No altera las existencias del catálogo.

---

## 6. Reportes y Analítica

1. **Filtro Estricto de Ingresos**:
   - Únicamente los pedidos en estado `APROBADO` se consideran ventas efectivas para el cálculo de facturación, volumen de unidades, ticket promedio y rankings.
2. **Agrupaciones Temporales**:
   - Los reportes consolidan ventas por jornada (`diario`), semana calendario (`semanal`), mes (`mensual`) y año (`anual`).
3. **Rankings de Rendimiento**:
   - Ranking de álbumes más vendidos ordenados por unidades vendidas e ingresos brutos generados.
   - Distribución porcentual de ventas por género musical / categoría.

---

## 7. Respaldos y Seguridad Operacional

1. **Mínimo Privilegio**:
   - Tres roles en PostgreSQL: `new_records_app` (DML Flask), `new_records_backup` (solo lectura `pg_dump`) y `new_records_admin` (DDL).
2. **Cabeceras HTTP de Seguridad**:
   - Inyección en todas las respuestas de `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection: 1; mode=block` y `Referrer-Policy: strict-origin-when-cross-origin`.
3. **Copias de Seguridad**:
   - Respaldos automatizados y vía CLI `flask crear-backup` almacenados en `backups/` (excluido de Git).

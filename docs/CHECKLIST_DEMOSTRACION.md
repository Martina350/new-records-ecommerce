# Guía y Checklist de Demostración — New Records

Esta guía describe el recorrido secuencial recomendado para la presentación y evaluación del proyecto de comercio electrónico **New Records**.

---

## 1. Preparación Previa al Demo

1. **Entorno y Base de Datos**:
   - Activar el entorno virtual e inicializar la base de datos limpia con datos de demostración:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     python init_db.py
     ```
   - Iniciar el servidor Flask:
     ```powershell
     python -m flask --app app run --debug
     ```
   - Abrir el navegador en `http://127.0.0.1:5000`.

2. **Cuentas de Prueba Preconfiguradas**:
   - **Administrador**: `admin@newrecords.local` / `admin12345` (o el configurado en `.env`).
   - **Cliente Demo**: `cliente@newrecords.local` / `cliente12345` (o el configurado en `.env`).

---

## 2. Checklist de Demostración Paso a Paso

### 🛒 Paso 1: Portada, Navegación y Catálogo Dinámico
- [ ] Mostrar la página principal con el banner de bienvenida y la sección de lanzamientos destacados.
- [ ] Navegar a **Categorías** (`/categorias`) y mostrar los géneros Rock, Pop y Reggaeton consultados desde PostgreSQL.
- [ ] Explorar el **Catálogo Completo** (`/productos`), filtrando por categoría (ej. Rock) y buscando por texto (ej. "Pink Floyd" o "Bad Bunny").
- [ ] Acceder al **Detalle del Producto** de un CD y de un Vinilo, destacando el cálculo polimórfico del desglose de precio (precio base, peso en kg, costo de envío y costo de embalaje).

### 👤 Paso 2: Autenticación, Perfil y Registro de Métodos de Pago
- [ ] Demostrar el registro de un nuevo cliente con validación de contraseña segura y normalización de correo.
- [ ] Iniciar sesión como cliente y acceder a **Mi Perfil** (`/perfil`).
- [ ] Ir a **Métodos de Pago** (`/perfil/pagos`) y registrar una nueva tarjeta.
- [ ] Demostrar la **Verificación por PIN**:
  - Explicar la simulación o recepción del código PIN de 6 dígitos con límite de 3 intentos y caducidad de 5 minutos.
  - Ingresar el PIN correcto y verificar la tarjeta.

### 🛍️ Paso 3: Carrito de Compras y Checkout
- [ ] Agregar al menos un CD y un Vinilo al carrito.
- [ ] Ir a `/carrito` y demostrar la actualización de cantidades y el recálculo reactivo del subtotal polimórfico.
- [ ] Proceder al **Checkout** (`/checkout`), seleccionando el método de pago verificado.
- [ ] Confirmar la compra:
  - Mostrar la pantalla de confirmación con el número de pedido `NR-XXXX-XXXX` y estado `PENDIENTE`.
  - Descargar de inmediato el **Comprobante de Pedido en PDF** (`/pedidos/<numero>/comprobante`).
  - Intentar descargar la Factura Final y mostrar que se encuentra bloqueada hasta la aprobación administrativa.

### ⚙️ Paso 4: Panel Administrativo y Aprobación Atómica de Pedidos
- [ ] Cerrar sesión e iniciar sesión como **Administrador** (`admin@newrecords.local`).
- [ ] Acceder al **Dashboard Administrativo** (`/admin/dashboard`) y señalar las métricas en vivo (discos activos, categorías, pedidos pendientes, ingresos).
- [ ] Ir a la **Bandeja de Pedidos** (`/admin/pedidos`) y abrir el pedido pendiente recién creado.
- [ ] Mostrar la auditoría técnica con la verificación de existencias en tiempo real.
- [ ] **Aprobar el Pedido**:
  - Explicar la ejecución del procedimiento almacenado transaccional en PostgreSQL (`aprobar_pedido_new_records`).
  - Demostrar el descuento atómico de stock en el inventario.
  - Mostrar la generación de la **Factura Final PDF**.

### 📊 Paso 5: Reportes y Analítica de Ventas
- [ ] Desde el panel de administración, acceder a **Reportes de Ventas** (`/admin/reportes`).
- [ ] Navegar entre las pestañas de **Período Diario**, **Semanal** y **Mensual / Anual**.
- [ ] Mostrar cómo el pedido aprobado impacta directamente en los ingresos acumulados, unidades físicas vendidas y ticket promedio.
- [ ] Señalar el **Ranking de Discos más Vendidos** con sus medallas de posición y el gráfico de barras porcentuales por **Género Musical**.

### 🛡️ Paso 6: Integridad, Seguridad y Respaldos
- [ ] Demostrar la gestión CRUD de discos y categorías con **eliminación suave (Soft Delete)** y confirmación en cascada.
- [ ] Generar un respaldo formal de la base de datos desde la terminal:
  ```powershell
  python -m flask --app app crear-backup --formato plain
  ```
  - Verificar la creación del archivo con timestamp UTC en la carpeta `backups/`.
- [ ] Ejecutar la suite completa de pruebas automatizadas:
  ```powershell
  python -m pytest -v
  ```
  - Mostrar los 97+ tests pasando con 100% de éxito.

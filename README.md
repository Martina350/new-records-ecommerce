# New Records — Plataforma de Comercio Electrónico para Música Física

**New Records** es una aplicación web monolítica de comercio electrónico desarrollada con **Flask**, **SQLAlchemy** y **PostgreSQL**, orientada a la venta de música en formato físico (**CD** y **Vinilo**).

El sistema cuenta con una arquitectura relacional sólida respaldada por procedimientos almacenados, triggers y restricciones de integridad en PostgreSQL, seguridad en capa web, generación de comprobantes y facturas en PDF mediante ReportLab, reportes analíticos de ventas y una suite exhaustiva de pruebas automatizadas.

---

## 🌟 Características Principales

- 🎵 **Catálogo Dinámico y Polimorfismo**:
  - Especialización de productos en `CD` y `Vinilo` mediante herencia de tabla única en SQLAlchemy.
  - Desglose de precios polimórfico en tiempo real (precio base, peso en kg, embalaje y costo de envío).
  - Filtro interactivo por géneros musicales (Rock, Pop, Reggaeton, Jazz, etc.) y buscador por texto.
- 🔐 **Autenticación y Control de Acceso (RBAC)**:
  - Roles bien diferenciados: `cliente` y `administrador`.
  - Contraseñas cifradas con Werkzeug (`scrypt`).
  - Gestión de perfil de usuario y cierre seguro de sesiones.
- 💳 **Métodos de Pago y Verificación por PIN**:
  - Almacenamiento seguro de tarjetas tokenizadas y enmascaradas (sin PAN completo ni CVV).
  - Verificación de tarjeta mediante PIN temporal de 6 dígitos con vigencia de 5 minutos y bloqueo al tercer intento.
- 🛒 **Carrito y Checkout Transaccional**:
  - Carrito persistente en sesión que valida existencias de stock en tiempo real.
  - Proceso de checkout que genera un pedido con estado inicial `PENDIENTE` y emite un **Comprobante de Pedido en PDF**.
- 🛠️ **Panel Administrativo y Procedimientos Almacenados**:
  - Dashboard con métricas clave en vivo (inventario, pedidos pendientes, ingresos).
  - CRUD de discos y categorías con **eliminación suave (Soft Delete)** y confirmación en cascada.
  - Aprobación concurrente de pedidos mediante el procedimiento almacenado de PostgreSQL `aprobar_pedido_new_records`, el cual descuenta stock de forma atómica y emite la **Factura Final en PDF**.
  - Rechazo de pedidos con registro obligatorio de motivo sin alterar inventario.
- 📈 **Reportes Analíticos de Ventas**:
  - Evolución temporal de ingresos por período diario, semanal, mensual y anual.
  - Ranking de discos más vendidos con medallas de posición y distribución de ventas por categoría musical.
- 🛡️ **Seguridad, Mínimo Privilegio y Respaldos**:
  - Definición de roles de base de datos (`new_records_app`, `new_records_backup`, `new_records_admin`).
  - Cabeceras HTTP de seguridad (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`).
  - Comando CLI `flask crear-backup` para copias de seguridad consistentes con `pg_dump`.

---

## 🚀 Tecnologías Utilizadas

- **Backend**: Python 3.10+ / Flask 3.x
- **ORM**: Flask-SQLAlchemy / SQLAlchemy 2.x
- **Base de Datos**: PostgreSQL 15+
- **Frontend**: HTML5, CSS3 responsive y Jinja2
- **Documentos PDF**: ReportLab
- **Seguridad**: Werkzeug Security (`scrypt`) y decoradores RBAC
- **Pruebas Automatizadas**: pytest

---

## 📂 Estructura del Repositorio

```text
new-records-ecommerce/
├── app.py                      # Aplicación Flask principal y rutas
├── auth.py                     # Decoradores de autenticación y helpers de sesión
├── backup_manager.py           # Gestor y orquestador de respaldos pg_dump
├── config.py                   # Configuración y variables de entorno
├── configure_db_roles.py       # Aprovisionamiento seguro de roles PostgreSQL
├── init_db.py                  # Script de inicialización y carga de datos demo
├── mailer.py                   # Notificaciones por correo electrónico (SMTP/simulado)
├── models.py                   # Modelos de datos y herencia polimórfica SQLAlchemy
├── payments.py                 # Lógica de métodos de pago y verificación por PIN
├── pdf_generator.py            # Generador de comprobantes y facturas en PDF
├── services.py                 # Capa de servicios y lógica analítica de negocio
├── database/                   # Scripts SQL de esquema, reglas, procedimientos y roles
│   ├── reports.sql             # Consultas analíticas de reportes
│   ├── roles_seguridad.sql     # Roles de mínimo privilegio PostgreSQL
│   ├── rules_codigos_discos.sql # Códigos automáticos por categoría
│   ├── rules_fases7_10.sql     # Procedimiento de aprobación y triggers
│   ├── rules_fases12.sql       # Restricciones CHECK y triggers avanzados
│   └── schema_fase3.sql        # Esquema inicial DDL
├── docs/                       # Documentación técnica y de negocio
│   ├── CHECKLIST_DEMOSTRACION.md
│   ├── CONFIGURACION_POSTGRESQL.md
│   ├── DICCIONARIO_DATOS.md
│   ├── MODELO_ENTIDAD_RELACION.md
│   ├── REGLAS_NEGOCIO.md
│   └── SEGURIDAD_Y_RESPALDOS.md
├── static/                     # CSS, JavaScript e imágenes estáticas
├── templates/                  # Plantillas Jinja2 organizadas por módulo
└── tests/                      # Suite completa de pruebas automatizadas
```

---

## ⚙️ Instalación y Puesta en Marcha

### 1. Clonar el repositorio

```bash
git clone https://github.com/Martina350/new-records-ecommerce.git
cd new-records-ecommerce
```

### 2. Crear y activar el entorno virtual

En Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

En Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copiar `.env.example` como `.env` y reemplazar todos los valores que comienzan
con `change_`. Cada integrante utiliza credenciales locales propias. No se deben
copiar contraseñas desde pruebas, documentación ni mensajes del equipo.

```ini
SECRET_KEY=tu_clave_secreta_segura
DB_HOST=localhost
DB_PORT=5432
DB_NAME=new_records_db
DB_USER=new_records_app
DB_PASSWORD=change_app_db_password
DB_ADMIN_USER=new_records_admin
DB_ADMIN_PASSWORD=change_admin_db_password
DB_BACKUP_USER=new_records_backup
DB_BACKUP_PASSWORD=change_backup_db_password
DB_BOOTSTRAP_USER=postgres
DB_BOOTSTRAP_PASSWORD=change_postgres_bootstrap_password

ADMIN_NAME=Administrador New Records
ADMIN_EMAIL=admin@newrecords.local
ADMIN_PASSWORD=change_admin_password

CLIENTE_DEMO_NAME=Cliente Demo
CLIENTE_DEMO_EMAIL=cliente@newrecords.local
CLIENTE_DEMO_PASSWORD=change_client_password
```

### 5. Configurar roles e inicializar la base de datos

Después de crear una base vacía llamada `new_records_db`, configurar los tres
roles técnicos. El usuario bootstrap se utiliza únicamente durante este paso:

```powershell
python configure_db_roles.py
python init_db.py
```

`init_db.py` se conecta como `new_records_admin`. Flask utiliza
`new_records_app`, que no es propietario de las tablas, y `pg_dump` utiliza
`new_records_backup`, que solo tiene permisos de lectura.

### 6. Iniciar el Servidor de Desarrollo

```powershell
python -m flask --app app run --debug
```

Acceder en el navegador a `http://127.0.0.1:5000`.

---

## 🧪 Pruebas Automatizadas

La suite valida todos los componentes sin persistir datos de prueba ni escribir
PDF en el repositorio. Las comprobaciones que crean una base temporal son opt-in.

Para ejecutar todas las pruebas:

```powershell
python -m pytest -v
```

Después de configurar los roles, ejecutar también la auditoría de privilegios:

```powershell
$env:RUN_DB_SECURITY_TESTS="1"
python -m pytest tests/test_seguridad_respaldos.py -v
```

---

## 📦 Copias de Seguridad (Backups)

Generar una copia de seguridad en formato SQL plano:
```powershell
python -m flask --app app crear-backup --formato plain
```

Generar una copia de seguridad en formato binario comprimido de PostgreSQL (`pg_dump`):
```powershell
python -m flask --app app crear-backup --formato custom
```

Los respaldos se almacenan automáticamente en la carpeta `backups/`. Consulta [`docs/SEGURIDAD_Y_RESPALDOS.md`](docs/SEGURIDAD_Y_RESPALDOS.md) para más detalles sobre restauración y roles.

Para crear un dump temporal, restaurarlo en una base aislada, validar su esquema
y eliminar el destino de prueba automáticamente:

```powershell
python -m flask --app app verificar-restauracion
```

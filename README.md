# New Records

New Records es un proyecto académico de comercio electrónico para la venta de música en formato físico, específicamente CD y vinilo. El sistema se desarrollará como un monolito sencillo con Flask, SQLAlchemy y PostgreSQL, reutilizando el prototipo responsive existente.

## Estado actual

Las fases 1 a 11 están implementadas y verificadas. El proyecto incluye la base Flask, PostgreSQL, autenticación y roles, perfil, catálogo dinámico, carrito, métodos de pago con PIN, pedidos, comprobantes y facturas PDF, notificaciones, administración de catálogo y pedidos, y reportes analíticos de ventas (diario, semanal, mensual, ranking de discos y ranking de categorías).

La aprobación de pedidos y el descuento concurrente de stock se realizan mediante un procedimiento almacenado de PostgreSQL. La suite automatizada contiene 85 pruebas aisladas que no persisten información ni escriben PDFs en el repositorio. La integridad avanzada, seguridad y respaldos pertenecen a la Fase 12.

El alcance completo y la regla de aprobación entre fases están documentados en `PLAN_IMPLEMENTACION.md`, que también puede ser entregado por separado a cada colaborador.

## Tecnologías previstas

- Python 3.10 o superior.
- Flask y Jinja2.
- Flask-SQLAlchemy.
- PostgreSQL.
- HTML5, CSS3 y JavaScript.
- Werkzeug para contraseñas.
- SMTP para códigos PIN y notificaciones.
- ReportLab para comprobantes PDF.
- pytest para pruebas.

## Estructura inicial

- `templates/`: páginas HTML del prototipo y futuras plantillas Jinja2.
- `static/`: CSS, JavaScript e imágenes.
- `database/`: restricciones, triggers, procedimientos y reportes PostgreSQL de fases posteriores.
- `migrations/`: historial futuro de cambios del esquema.
- `tests/`: pruebas del proyecto.
- `docs/`: inventario, decisiones y documentación funcional.
- `backups/`: destino local para respaldos; su contenido no se versiona.

Los módulos nuevos de la aplicación se crearán únicamente cuando se aprueben sus fases correspondientes.

## Guía para clonar el repositorio y continuar el desarrollo

El repositorio queda preparado hasta la **Fase 11**. La siguiente persona debe completar estos pasos desde la raíz del proyecto antes de comenzar la Fase 12.

### 1. Clonar el repositorio

```bash
git clone --branch origin/martina-implementations --single-branch https://github.com/Martina350/new-records-ecommerce.git
cd new-records-ecommerce
```

El comando anterior clona directamente la rama de continuidad utilizada por el equipo. Debe ejecutarse después de que los cambios de la Fase 10 hayan sido confirmados y publicados en el remoto.

### 2. Crear y activar el entorno virtual

Se recomienda utilizar Python 3.10 o superior.

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

En Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar las dependencias

Con el entorno virtual activado:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Configurar PostgreSQL

PostgreSQL debe estar instalado y el servicio debe encontrarse iniciado. Desde pgAdmin o `psql`, crear los siguientes recursos locales:

- Usuario de aplicación: `new_records_app`.
- Base de datos: `new_records_db`.
- Propietario de la base: `new_records_app`.
- Codificación: UTF-8.

La contraseña debe ser elegida por cada colaborador y no debe compartirse ni subirse a Git. La aplicación no debe utilizar normalmente el superusuario `postgres`.

Las instrucciones detalladas se encuentran en [Configuración de PostgreSQL](docs/CONFIGURACION_POSTGRESQL.md).

### 5. Crear y completar el archivo de entorno

Copiar `.env.example` como `.env`.

En Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

En Linux o macOS:

```bash
cp .env.example .env
```

Editar únicamente el archivo local `.env` y completar, como mínimo:

- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` y `DB_NAME` con la configuración PostgreSQL local.
- `SECRET_KEY` con un valor aleatorio propio.
- Las contraseñas de las cuentas iniciales de administrador y cliente.

Puede generarse una clave secreta con:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

No se debe copiar el archivo `.env` de otro integrante. Este archivo está excluido de Git y cada entorno debe utilizar sus propias credenciales.

### 6. Comprobar la conexión e inicializar la base de datos

Primero verificar que Flask pueda conectarse a PostgreSQL:

```bash
python -m flask --app app check-db
```

Después crear las tablas y cargar el catálogo y las cuentas iniciales:

```bash
python init_db.py
```

El inicializador puede volver a ejecutarse sin borrar ni duplicar los datos iniciales existentes.

### 7. Ejecutar las pruebas

```bash
python -m pytest -q
```

Antes de continuar se espera que todas las pruebas existentes terminen correctamente.

### 8. Iniciar la aplicación

```bash
python -m flask --app app run --debug
```

La dirección predeterminada es `http://127.0.0.1:5000`.

### 9. Continuar con las fases restantes

El desarrollo debe continuar desde la **Fase 12**, siguiendo la copia actualizada de `PLAN_IMPLEMENTACION.md` proporcionada por la persona responsable del proyecto. El plan puede entregarse por separado y no contiene credenciales.

Antes de implementar una fase nueva, se debe confirmar que la fase anterior esté aprobada, trabajar en una rama propia y evitar modificar o eliminar las funcionalidades y pruebas ya terminadas.

## Ejecución de Flask

Con el entorno virtual activado y las dependencias instaladas, iniciar la aplicación desde la raíz del proyecto. La portada estará disponible en la dirección local mostrada por Flask.

Rutas disponibles en la Fase 2:

- `/`
- `/categorias`
- `/productos`
- `/contacto`

Una ruta inexistente debe mostrar la página 404 propia de New Records.

## Conexión con PostgreSQL

La preparación del usuario y la base está explicada en [Configuración de PostgreSQL](docs/CONFIGURACION_POSTGRESQL.md).

Después de configurar el archivo local `.env`, el comando Flask `check-db` comprueba la conexión mediante una lectura sin modificar datos.

## Inicialización del modelo y catálogo

Después de configurar las variables de las cuentas iniciales en `.env`, ejecutar `init_db.py`. El proceso crea las tablas faltantes y carga categorías, discos y usuarios de demostración sin borrar ni duplicar datos existentes.

La estructura resultante está descrita en:

- [Modelo entidad-relación](docs/MODELO_ENTIDAD_RELACION.md)
- [Diccionario de datos](docs/DICCIONARIO_DATOS.md)

## Flujo de trabajo con Git

- `main`: versión estable y revisada.
- Una rama corta por fase o funcionalidad.
- No mezclar cambios de varias fases en una misma rama.
- Revisar `git status` y ejecutar las verificaciones correspondientes antes de integrar.
- Nunca versionar `.env`, contraseñas, facturas generadas ni respaldos reales.

## Documentación

- [Inventario del prototipo](docs/PROTOTIPO_INICIAL.md)
- [Pendientes del frontend](docs/PENDIENTES_FRONTEND.md)
- [Configuración de PostgreSQL](docs/CONFIGURACION_POSTGRESQL.md)
- [Modelo entidad-relación](docs/MODELO_ENTIDAD_RELACION.md)
- [Diccionario de datos](docs/DICCIONARIO_DATOS.md)

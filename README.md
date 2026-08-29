# New Records

New Records es un proyecto académico de comercio electrónico para la venta de música en formato físico, específicamente CD y vinilo. El sistema se desarrollará como un monolito sencillo con Flask, SQLAlchemy y PostgreSQL, reutilizando el prototipo responsive existente.

## Estado actual

La Fase 1 prepara el repositorio y preserva el prototipo. Todavía no contiene rutas Flask, modelos SQLAlchemy, tablas, autenticación, carrito ni procesos de compra.

El alcance completo y la regla de aprobación entre fases están documentados en [PLAN_IMPLEMENTACION.md](PLAN_IMPLEMENTACION.md).

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

Los módulos Python de la aplicación se crearán únicamente cuando se aprueben sus fases correspondientes.

## Preparación local

1. Instalar Python y PostgreSQL.
2. Confirmar que PostgreSQL está iniciado y que `psql` puede ejecutarse.
3. Crear un entorno virtual llamado `.venv`.
4. Activar el entorno virtual.
5. Instalar las dependencias declaradas en `requirements.txt`.
6. Copiar `.env.example` como `.env` y reemplazar sus valores localmente.

El archivo `.env` contiene secretos y está excluido de Git.

## Vista previa del prototipo

Mientras Flask todavía no está implementado, el prototipo puede revisarse iniciando un servidor HTTP desde la raíz del repositorio y abriendo `/templates/index.html` en el navegador.

Las páginas disponibles son:

- `/templates/index.html`
- `/templates/categorias.html`
- `/templates/productos.html`
- `/templates/contacto.html`

## Flujo de trabajo con Git

- `main`: versión estable y revisada.
- Una rama corta por fase o funcionalidad.
- No mezclar cambios de varias fases en una misma rama.
- Revisar `git status` y ejecutar las verificaciones correspondientes antes de integrar.
- Nunca versionar `.env`, contraseñas, facturas generadas ni respaldos reales.

## Documentación

- [Plan de implementación](PLAN_IMPLEMENTACION.md)
- [Inventario del prototipo](docs/PROTOTIPO_INICIAL.md)
- [Pendientes del frontend](docs/PENDIENTES_FRONTEND.md)


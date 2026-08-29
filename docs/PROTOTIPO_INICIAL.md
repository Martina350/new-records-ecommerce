# Inventario del prototipo inicial

## Punto de preservación

El prototipo original está preservado en el historial Git mediante el commit `9f4e5cf` (`initial_commit`). La reorganización de la Fase 1 conserva sus archivos y utiliza movimientos detectables por Git, por lo que el contenido anterior puede recuperarse desde ese commit sin mantener copias duplicadas.

## Páginas recibidas

- `index.html`: portada de New Records.
- `categorias.html`: Rock, Pop y Reggaeton.
- `productos.html`: catálogo estático de doce discos.
- `contacto.html`: formulario con validación visual en JavaScript.

Durante la Fase 1 estas páginas se trasladan a `templates/`. Permanecen como HTML estático; su conversión real a Jinja2 corresponde a fases posteriores.

## Recursos recibidos

- Una hoja de estilos principal.
- Un archivo JavaScript para menú móvil, filtros y validación de contacto.
- Un banner de inicio.
- Tres imágenes de categorías.
- Doce portadas de discos.

Los recursos se trasladan de `assets/` a `static/`, conservando las subcarpetas `css`, `js` e `img`.

## Codificación

Los archivos declaran UTF-8 y sus bytes contienen correctamente los caracteres en español. La apariencia dañada observada inicialmente provenía de una lectura de consola sin especificar UTF-8, no de contenido corrupto. No se realizó una conversión destructiva; las verificaciones posteriores deben leer los archivos explícitamente como UTF-8.

## Contenido repetido identificado

- Cabecera y navegación.
- Menú móvil.
- Enlaces globales.
- Pie de página.
- Inclusión de fuentes, CSS y JavaScript.

Estos elementos se trasladarán a `templates/base.html` cuando se apruebe la adaptación a Jinja2.

## Estado de herramientas verificado

- Python detectado: 3.14.6.
- PostgreSQL detectado: servicio `postgresql-x64-18` activo.
- Cliente detectado: PostgreSQL `psql` 18.1.
- Observación local: la carpeta `bin` de PostgreSQL no está añadida al PATH, aunque el ejecutable existe en la instalación asociada al servicio.

No se creó la base `new_records_db` ni se modificó PostgreSQL durante la Fase 1.


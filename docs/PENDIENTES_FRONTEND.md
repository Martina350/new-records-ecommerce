# Revisión final del frontend

Este documento conserva la revisión iniciada en la Fase 1 y registra su cierre
en la Fase 13.

## Elementos completados

- Plantilla `base.html`, navegación compartida, mensajes flash y rutas `url_for`.
- Catálogo, filtros, estados vacíos, detalle, stock, carrito y recomendaciones
  alimentados desde PostgreSQL.
- Menú móvil con `aria-controls`, actualización de `aria-expanded`, cierre con
  la tecla `Escape`, devolución del foco y cierre al seleccionar un enlace.
- Indicadores globales de `focus-visible` para navegación por teclado.
- Textos alternativos en las imágenes informativas y elementos decorativos
  ocultos mediante `aria-hidden`.
- Formularios POST protegidos con token CSRF y mensajes de error comprensibles.
- Reglas responsive verificables en los puntos de corte móvil, tableta y escritorio.

## Mejora futura fuera del alcance académico

- Convertir portadas pesadas a WebP manteniendo una alternativa compatible.
- Integrar el formulario de contacto con un proveedor real de mensajería.
- Ejecutar auditorías automáticas Lighthouse/axe dentro de CI cuando exista un
  entorno de despliegue.

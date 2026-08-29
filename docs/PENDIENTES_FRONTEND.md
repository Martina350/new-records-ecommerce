# Pendientes del frontend

Este documento registra mejoras detectadas en la Fase 1. No se implementan todavía para evitar modificar el comportamiento visible del prototipo antes de la fase correspondiente.

## Jinja2

- Crear `base.html` y eliminar la repetición de cabecera, navegación y pie.
- Reemplazar enlaces estáticos por `url_for`.
- Cargar categorías y discos desde PostgreSQL.
- Convertir tarjetas repetidas en bucles Jinja2.
- Mostrar mensajes flash en un componente común.

## Accesibilidad

- Añadir `aria-controls` y actualizar `aria-expanded` en el botón del menú móvil.
- Permitir cerrar el menú con teclado y al cambiar de página.
- No depender exclusivamente de `hover` para mostrar descripciones.
- Reemplazar atributos `alt` aplicados a elementos `div` por alternativas semánticas válidas.
- Añadir indicadores de foco visibles y revisar el orden de navegación.

## Rendimiento

- Optimizar las imágenes más pesadas.
- Evaluar WebP manteniendo una alternativa compatible.
- Definir dimensiones de imágenes para reducir movimientos durante la carga.

## Funcionalidad pendiente

- Sustituir el filtro visual por consultas dinámicas del catálogo.
- Enviar realmente el formulario de contacto o retirarlo del alcance final.
- Incorporar estados vacíos y errores provenientes de Flask.
- Añadir detalle individual, stock, formato, carrito y recomendaciones.


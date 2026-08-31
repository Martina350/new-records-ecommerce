# Diccionario de datos de New Records

## `usuarios`

- `id`: PK entera.
- `nombre`: nombre completo obligatorio, máximo 100 caracteres.
- `email`: correo normalizado obligatorio, único e indexado.
- `password_hash`: hash obligatorio; nunca almacena la contraseña original.
- `rol`: obligatorio, con valor inicial `cliente` y restricción a `cliente` o `administrador`.
- `telefono`, `direccion`, `ciudad`: información editable del perfil.
- `activo`: booleano obligatorio, inicialmente verdadero.
- `fecha_registro`: fecha y hora UTC de creación, con valor predeterminado en PostgreSQL.

## `categorias`

- `id`: PK entera.
- `nombre`: nombre del género, obligatorio, único y de 2 a 80 caracteres sin contar espacios laterales.
- `slug`: identificador para URL, obligatorio, único e indexado.
- `prefijo_codigo`: prefijo único de 3 a 5 letras mayúsculas o números usado para generar los SKU de sus discos.
- `descripcion`: explicación del género.
- `imagen`: ruta relativa dentro de `static`.
- `activo`: estado para eliminación lógica.
- `fecha_creacion`, `fecha_actualizacion`: fechas UTC de auditoría básica, con valor predeterminado en PostgreSQL.

## `discos`

- `id`: PK entera.
- `categoria_id`: FK obligatoria hacia `categorias`, con eliminación restrictiva.
- `codigo`: SKU obligatorio, único e indexado, generado en PostgreSQL con el formato `NR-PREFIJO-NÚMERO`.
- `album`: nombre del álbum obligatorio, no vacío y de máximo 150 caracteres.
- `artista`: artista obligatorio, no vacío, de máximo 120 caracteres e indexado.
- `descripcion`: información comercial obligatoria y no vacía.
- `precio_base`: valor decimal estrictamente positivo.
- `stock`: entero no negativo, inicialmente cero.
- `formato`: discriminador obligatorio limitado a `CD` o `VINILO`.
- `peso_kg`: decimal positivo.
- `costo_envio_por_kg`: decimal no negativo.
- `costo_embalaje`: decimal no negativo.
- `imagen`: ruta relativa de la portada.
- `activo`: estado para eliminación lógica.
- `fecha_creacion`, `fecha_actualizacion`: fechas UTC, con valor predeterminado en PostgreSQL.

## `secuencias_codigo_categoria`

- `categoria_id`: PK y FK hacia `categorias`; existe un solo contador por género.
- `ultimo_numero`: último consecutivo reservado, obligatorio y no negativo.
- Su fila se bloquea durante la generación para evitar códigos duplicados ante solicitudes concurrentes.

## `metodos_pago`

- `id`: PK entera.
- `usuario_id`: FK obligatoria hacia el propietario.
- `token`: referencia simulada o del proveedor, obligatoria y única.
- `marca`: marca comercial de la tarjeta.
- `ultimos4`: exactamente cuatro dígitos; nunca contiene el número completo.
- `titular`: nombre impreso o asociado a la tarjeta, entre 3 y 120 caracteres.
- `mes_vencimiento`: entero entre 1 y 12.
- `anio_vencimiento`: entero entre 2020 y 2100; un trigger exige que la tarjeta siga vigente y no supere veinte años desde la fecha actual.
- `predeterminado`: indica si se precarga en checkout.
- `activo`: permite desactivar el método sin borrar el historial.
- `fecha_verificacion`: fecha UTC en la que se confirmó el PIN.

## `verificaciones_tarjeta`

- `id`: PK entera.
- `usuario_id`: FK obligatoria hacia el solicitante.
- `token_verificacion`: identificador temporal único.
- `pin_hash`: hash del PIN, nunca el código original.
- `token_tarjeta`: token temporal; no contiene PAN ni CVV.
- `marca`, `ultimos4`, `titular`, `mes_vencimiento`, `anio_vencimiento`: datos enmascarados pendientes de verificación; el titular admite entre 3 y 120 caracteres.
- `fecha_creacion`, `fecha_expiracion`: delimitan la vigencia; la fecha de creación tiene valor predeterminado en PostgreSQL.
- `intentos`: entero entre 0 y 3, inicialmente cero.
- `verificada`: confirma que el PIN fue utilizado correctamente.

## `pedidos`

- `id`: PK entera.
- `numero`: identificador público obligatorio, único e indexado.
- `cliente_id`: FK obligatoria hacia `usuarios`.
- `metodo_pago_id`: FK obligatoria hacia un método verificado.
- `estado`: inicialmente `PENDIENTE`; admite `APROBADO` o `RECHAZADO`.
- `total`: decimal no negativo.
- `fecha_creacion`: fecha UTC del checkout, con valor predeterminado en PostgreSQL.
- `fecha_revision`: fecha UTC de aprobación o rechazo.
- `administrador_revisor_id`: FK opcional hacia el administrador.
- `motivo_rechazo`: obligatorio por restricción cuando el pedido está rechazado.

## `detalles_pedido`

- `id`: PK entera.
- `pedido_id`: FK obligatoria con eliminación en cascada para pedidos de prueba.
- `disco_id`: FK obligatoria y restrictiva hacia el disco.
- `album`, `artista`, `formato`: copia histórica del producto comprado.
- `precio_unitario`: decimal histórico no negativo.
- `cantidad`: entero mayor que cero.
- La combinación `pedido_id` y `disco_id` es única.
- El subtotal se calcula como precio unitario por cantidad.

## `transacciones_pago`

- `id`: PK entera.
- `pedido_id`: FK obligatoria y única hacia el pedido.
- `metodo_pago_id`: FK obligatoria hacia el método utilizado.
- `monto`: decimal no negativo.
- `estado`: `PENDIENTE`, `APROBADA` o `RECHAZADA`.
- `referencia`: identificador simulado obligatorio y único.
- `fecha_procesamiento`: fecha UTC del resultado.

## `facturas`

- `id`: PK entera.
- `pedido_id`: FK obligatoria hacia el pedido.
- `numero`: identificador documental obligatorio, único e indexado.
- `tipo`: `COMPROBANTE_PENDIENTE` o `FACTURA_FINAL`.
- `fecha_emision`: fecha UTC con valor predeterminado en PostgreSQL.
- `ruta_pdf`: ubicación controlada del documento generado.
- La combinación `pedido_id` y `tipo` es única.

## Datos iniciales

`init_db.py` carga de forma idempotente:

- 3 categorías: Rock, Pop y Reggaeton.
- 12 discos pertenecientes al dominio New Records.
- 1 cuenta administradora de desarrollo.
- 1 cuenta cliente de desarrollo.

Las contraseñas iniciales se leen desde `.env` y se almacenan exclusivamente como hash.

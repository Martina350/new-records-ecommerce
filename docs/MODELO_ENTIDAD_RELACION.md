# Modelo entidad-relación de New Records

## Alcance

El modelo cubre catálogo, usuarios, verificación de tarjetas, pedidos, cobros simulados y documentos PDF. El carrito no utiliza una tabla porque permanecerá temporalmente en la sesión Flask hasta que el cliente confirme el checkout.

## Diagrama

```mermaid
erDiagram
    CATEGORIAS {
        int id PK
        varchar nombre UK
        varchar slug UK
        varchar prefijo_codigo UK
        boolean activo
    }
    SECUENCIAS_CODIGO_CATEGORIA {
        int categoria_id PK,FK
        int ultimo_numero
    }
    DISCOS {
        int id PK
        int categoria_id FK
        varchar codigo UK
        varchar album
        varchar artista
        numeric precio_base
        int stock
        varchar formato
        boolean activo
    }
    USUARIOS {
        int id PK
        varchar nombre
        varchar email UK
        varchar password_hash
        varchar rol
        boolean activo
    }
    METODOS_PAGO {
        int id PK
        int usuario_id FK
        varchar marca
        varchar ultimos4
        varchar titular
        boolean predeterminado
        boolean activo
    }
    VERIFICACIONES_TARJETA {
        int id PK
        int usuario_id FK
        varchar token_verificacion UK
        varchar pin_hash
        int intentos
        boolean verificada
    }
    PEDIDOS {
        int id PK
        int cliente_id FK
        int metodo_pago_id FK
        int administrador_revisor_id FK
        varchar numero UK
        varchar estado
        numeric total
    }
    DETALLES_PEDIDO {
        int id PK
        int pedido_id FK
        int disco_id FK
        int cantidad
        numeric precio_unitario
        varchar album
        varchar artista
        varchar formato
    }
    TRANSACCIONES_PAGO {
        int id PK
        int pedido_id FK,UK
        int metodo_pago_id FK
        varchar referencia UK
        varchar estado
        numeric monto
    }
    FACTURAS {
        int id PK
        int pedido_id FK
        varchar numero UK
        varchar tipo
        varchar ruta_pdf
    }

    CATEGORIAS ||--o{ DISCOS : clasifica
    CATEGORIAS ||--o| SECUENCIAS_CODIGO_CATEGORIA : numera
    USUARIOS ||--o{ METODOS_PAGO : registra
    USUARIOS ||--o{ VERIFICACIONES_TARJETA : solicita
    USUARIOS ||--o{ PEDIDOS : realiza
    USUARIOS o|--o{ PEDIDOS : revisa
    METODOS_PAGO ||--o{ PEDIDOS : utiliza
    PEDIDOS ||--|{ DETALLES_PEDIDO : contiene
    DISCOS ||--o{ DETALLES_PEDIDO : aparece_en
    PEDIDOS ||--o| TRANSACCIONES_PAGO : genera
    METODOS_PAGO ||--o{ TRANSACCIONES_PAGO : procesa
    PEDIDOS ||--o{ FACTURAS : documenta
```

## Herencia POO de discos

`Disco` es la clase padre persistente y abstracta para SQLAlchemy. `CD` y `Vinilo` son sus únicas clases concretas.

La estrategia es herencia de tabla única:

- Todos los formatos se almacenan en `discos`.
- La columna `formato` funciona como discriminador.
- Los valores permitidos son `CD` y `VINILO`.
- Al consultar `Disco`, SQLAlchemy crea automáticamente un objeto `CD` o `Vinilo`.
- Cada clase concreta sobrescribe `precio_final()` para aplicar su propia regla física de envío y embalaje.

No existen productos digitales, perecibles ni clases provenientes del ejemplo de tienda genérica.

## Decisiones relacionales

- Una categoría puede clasificar muchos discos, pero cada disco pertenece a una categoría.
- Cada categoría mantiene como máximo una secuencia transaccional para generar códigos únicos.
- Un usuario puede registrar varios métodos de pago y realizar varios pedidos.
- `Pedido` tiene dos relaciones diferentes con `Usuario`: cliente y administrador revisor.
- Cada pedido conserva sus líneas en `detalles_pedido`.
- El detalle conserva álbum, artista, formato y precio unitario históricos, aunque el disco cambie posteriormente.
- Un pedido admite una transacción simulada principal.
- Un pedido puede tener un comprobante pendiente y una factura final.
- Las FK históricas utilizan eliminación restrictiva; la aplicación deberá desactivar usuarios, categorías y discos en lugar de borrarlos.

## Normalización

- **Primera forma normal (1FN):** cada columna contiene un valor atómico. Los discos de un pedido se almacenan como filas independientes en `detalles_pedido` y no como listas dentro de `pedidos`.
- **Segunda forma normal (2FN):** los atributos dependen de la clave completa de su entidad. Categorías, usuarios, métodos de pago y discos conservan sus propios datos y se referencian mediante FK.
- **Tercera forma normal (3FN):** no se repiten datos derivados entre entidades operativas. El género pertenece a `categorias`, la tarjeta simulada a `metodos_pago` y el cobro a `transacciones_pago`.
- La copia de álbum, artista, formato y precio en `detalles_pedido` es una desnormalización controlada para preservar la evidencia histórica de la venta.

El diseño de clases, métodos, herencia y asociaciones se encuentra en [`DIAGRAMA_CLASES.md`](DIAGRAMA_CLASES.md).

## Estados controlados

- Usuario: `cliente` o `administrador`.
- Disco: `CD` o `VINILO`.
- Pedido: `PENDIENTE`, `APROBADO` o `RECHAZADO`.
- Transacción: `PENDIENTE`, `APROBADA` o `RECHAZADA`.
- Factura: `COMPROBANTE_PENDIENTE` o `FACTURA_FINAL`.

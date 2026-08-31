# Diagrama UML de clases de New Records

El diagrama representa las entidades persistentes, sus operaciones principales, las asociaciones y la herencia polimórfica de los formatos físicos.

```mermaid
classDiagram
    class Usuario {
        +int id
        +str nombre
        +str email
        -str password_hash
        +str rol
        +bool activo
        +set_password(password_plano) void
        +check_password(password_plano) bool
        +es_administrador() bool
    }

    class Categoria {
        +int id
        +str nombre
        +str slug
        +str prefijo_codigo
        +bool activo
    }

    class SecuenciaCodigoCategoria {
        +int categoria_id
        +int ultimo_numero
    }

    class Disco {
        <<abstract>>
        +int id
        +int categoria_id
        +str codigo
        +str album
        +str artista
        +Decimal precio_base
        +int stock
        +str formato
        +bool activo
        +precio_final()* Decimal
        +ficha() str
    }

    class CD {
        +precio_final() Decimal
    }

    class Vinilo {
        +Decimal costo_embalaje
        +precio_final() Decimal
    }

    class MetodoPago {
        +int id
        +int usuario_id
        +str marca
        +str ultimos4
        +str titular
        +bool predeterminado
        +bool activo
    }

    class VerificacionTarjeta {
        +int id
        +int usuario_id
        +str token_verificacion
        -str pin_hash
        +int intentos
        +bool verificada
    }

    class Pedido {
        +int id
        +str numero
        +int cliente_id
        +int metodo_pago_id
        +int administrador_revisor_id
        +str estado
        +Decimal total
        +esta_pendiente() bool
    }

    class DetallePedido {
        +int id
        +int pedido_id
        +int disco_id
        +int cantidad
        +Decimal precio_unitario
        +subtotal() Decimal
    }

    class TransaccionPago {
        +int id
        +int pedido_id
        +int metodo_pago_id
        +str referencia
        +str estado
        +Decimal monto
    }

    class Factura {
        +int id
        +int pedido_id
        +str numero
        +str tipo
        +str ruta_pdf
    }

    Disco <|-- CD
    Disco <|-- Vinilo
    Categoria "1" --> "0..*" Disco : clasifica
    Categoria "1" --> "0..1" SecuenciaCodigoCategoria : numera
    Usuario "1" --> "0..*" MetodoPago : registra
    Usuario "1" --> "0..*" VerificacionTarjeta : solicita
    Usuario "1" --> "0..*" Pedido : compra
    Usuario "0..1" --> "0..*" Pedido : revisa
    MetodoPago "1" --> "0..*" Pedido : utiliza
    Pedido "1" *-- "1..*" DetallePedido : contiene
    Disco "1" --> "0..*" DetallePedido : referencia
    Pedido "1" --> "0..1" TransaccionPago : genera
    MetodoPago "1" --> "0..*" TransaccionPago : procesa
    Pedido "1" *-- "0..*" Factura : documenta
```

## Decisiones POO

- `Disco` es una clase padre persistente y abstracta: define el contrato `precio_final()` y concentra los datos comunes del producto físico.
- `CD` y `Vinilo` implementan el mismo contrato con reglas distintas. El consumidor no pregunta por el formato para calcular el precio.
- SQLAlchemy implementa la jerarquía mediante herencia de tabla única y utiliza `Disco.formato` como discriminador.
- La contraseña y el PIN se almacenan como hashes; la comparación se realiza mediante métodos y no exponiendo los valores persistidos.
- Los servicios de aplicación coordinan transacciones completas, mientras que las entidades conservan comportamiento propio del dominio.

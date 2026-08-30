# Plan de Implementación por Fases - New Records

## 1. Contexto del proyecto

**New Records** es una plataforma web de comercio electrónico especializada en la venta de música en formato físico, principalmente CD y vinilo. El punto de partida es un prototipo estático construido con HTML, CSS y JavaScript que ya contiene una página principal, una vista de categorías, un catálogo de discos, un formulario de contacto y recursos gráficos de productos y géneros musicales.

El objetivo es transformar ese prototipo en una aplicación web completa, funcional y deliberadamente sencilla, apropiada para un proyecto de nivel junior. La solución se desarrollará como un monolito Flask conectado a PostgreSQL y seguirá la metodología explicada en los tutoriales de las semanas 1, 2 y 3: configuración centralizada, modelos SQLAlchemy, herencia polimórfica, rutas Flask, plantillas Jinja2, sesiones, mensajes flash, decoradores de autenticación y autorización, CRUD y carrito.

La aplicación tendrá dos roles:

- **CLIENTE:** podrá registrarse, iniciar sesión, editar su perfil, explorar el catálogo, utilizar el carrito, registrar un método de pago mediante verificación por PIN, confirmar pedidos y consultar sus comprobantes.
- **ADMINISTRADOR:** podrá administrar discos y categorías, revisar pedidos pendientes, aprobar o rechazar pedidos y consultar reportes de ventas.

## 2. Objetivos principales

- Reutilizar y adaptar el diseño responsive existente al sistema de plantillas Jinja2.
- Implementar autenticación básica, sesiones y autorización por roles.
- Construir un catálogo dinámico con categorías, filtros y detalles de cada disco.
- Implementar un carrito sencillo apoyado en la sesión de Flask.
- Registrar métodos de pago simulados sin almacenar el número completo de tarjeta ni el CVV.
- Verificar el registro de tarjetas mediante un PIN temporal enviado por correo.
- Crear pedidos con estado inicial pendiente y aprobación manual del administrador.
- Controlar y descontar el stock de manera segura al aprobar una venta.
- Generar un comprobante PDF para el pedido y una factura final después de su aprobación.
- Implementar CRUD de discos y categorías con eliminación lógica cuando corresponda.
- Mostrar ventas por periodo, discos más vendidos y géneros más vendidos.
- Reforzar las reglas de negocio con restricciones, triggers y procedimientos de PostgreSQL.
- Incorporar pruebas, documentación, control de versiones y una estrategia básica de respaldos.

## 3. Stack tecnológico

- **Frontend:** HTML5, CSS3, JavaScript y Jinja2.
- **Backend:** Python y Flask.
- **ORM:** Flask-SQLAlchemy.
- **Base de datos:** PostgreSQL.
- **Autenticación:** sesiones firmadas de Flask y contraseñas protegidas con Werkzeug.
- **Correo:** SMTP para el envío del PIN y notificaciones.
- **PDF:** biblioteca Python compatible con Flask para documentos descargables.
- **Control de versiones:** Git y repositorio remoto.
- **Pruebas:** pytest y pruebas manuales de aceptación.

## 4. Principios de implementación

1. Se mantendrá un monolito sencillo con los archivos centrales `app.py`, `models.py`, `config.py`, `auth.py`, `services.py`, `reports.py` e `init_db.py`.
2. No se introducirán microservicios, API separada, framework frontend, repositorios ni capas empresariales innecesarias.
3. La jerarquía POO se adaptará al dominio mediante una clase padre `Disco` y las especializaciones `CD` y `Vinilo`, siguiendo la herencia polimórfica de SQLAlchemy mostrada en los tutoriales.
4. Las validaciones importantes existirán en tres niveles: interfaz, Flask y PostgreSQL.
5. Las operaciones críticas de pedidos y stock serán transaccionales.
6. Los productos y categorías utilizados por el prototipo se cargarán desde `init_db.py` y dejarán de estar escritos directamente en los HTML.
7. Las eliminaciones de discos utilizados en pedidos serán lógicas para preservar el historial.
8. Nunca se guardarán números completos de tarjeta, CVV ni PIN en texto plano.
9. Los reportes contarán solamente pedidos aprobados.
10. Cada fase requerirá aprobación explícita antes de iniciar la siguiente.

## 5. Metodología de los tutoriales incorporada al plan

Este apartado conserva las instrucciones arquitectónicas y didácticas de los tutoriales originales para que dichos archivos puedan eliminarse sin perder información necesaria. Los tutoriales dejan de ser una dependencia documental: este plan será la fuente de referencia del proyecto.

### 5.1 Adaptación obligatoria al dominio New Records

Los ejemplos de tienda genérica de los tutoriales se utilizarán únicamente como referencia metodológica. No se copiarán sus nombres, productos ni reglas de negocio.

Sustituciones obligatorias de contexto:

- La clase genérica `Producto` se convierte en `Disco`.
- `ProductoFisico` se especializa en las clases concretas `CD` y `Vinilo`.
- No se implementarán `ProductoDigital` ni `ProductoPerecible`.
- Los audífonos, cursos, fresas y demás datos de demostración del tutorial no formarán parte de la aplicación.
- Los datos iniciales serán los álbumes, artistas, formatos, precios, portadas y géneros del prototipo New Records.
- El catálogo mostrará álbum, artista, género, formato, precio, descripción y stock.
- El CRUD genérico de productos se convertirá en CRUD de discos y categorías musicales.
- El carrito contendrá discos físicos, no productos genéricos.
- Las ventas se representarán mediante `Pedido` y `DetallePedido`.
- Los roles del sistema serán `cliente` y `administrador`.

Todo nombre de clase, variable, función, ruta, plantilla, mensaje flash y comentario futuro deberá describir el dominio musical de New Records. No se aceptarán nombres heredados del ejemplo genérico cuando exista un término propio del negocio.

### 5.2 Secuencia didáctica que debe conservarse

La implementación seguirá la progresión de los tutoriales:

1. Verificar Python y PostgreSQL.
2. Crear y activar un entorno virtual.
3. Instalar las dependencias mínimas.
4. Configurar secretos y conexión mediante `.env` y `config.py`.
5. Definir los modelos SQLAlchemy y su herencia polimórfica.
6. Conectar SQLAlchemy con Flask mediante inicialización diferida.
7. Crear e inicializar la base de datos dentro del contexto de la aplicación.
8. Transformar el frontend en plantillas Jinja2 con una plantilla base.
9. Implementar rutas de lectura y detalle.
10. Incorporar CRUD mediante peticiones GET y POST.
11. Implementar registro, login, sesiones y mensajes flash.
12. Incorporar decoradores de autenticación y autorización.
13. Implementar el carrito en la sesión.
14. Extender la base con checkout, pagos simulados, pedidos, PDF, administración y reportes.

Cada bloque deberá funcionar y probarse antes de avanzar al siguiente.

### 5.3 Configuración de Flask y PostgreSQL

- Las credenciales nunca se escribirán directamente en los archivos Python.
- `.env` almacenará las credenciales locales y no se versionará.
- `.env.example` documentará las variables necesarias sin valores secretos.
- `config.py` leerá las variables de entorno y construirá la conexión PostgreSQL.
- Se deshabilitará el seguimiento innecesario de modificaciones de SQLAlchemy.
- La clave secreta de Flask se obtendrá del entorno y protegerá las sesiones.
- La instancia de SQLAlchemy se declarará separada de la aplicación y se conectará desde `app.py`.
- Toda operación de inicialización ejecutada fuera de una ruta utilizará el contexto de aplicación de Flask.

### 5.4 POO y herencia polimórfica

La demostración de POO seguirá el mecanismo de herencia de SQLAlchemy enseñado en los tutoriales, adaptado a discos:

- `Disco` será la clase padre persistente y concentrará identidad, código, álbum, artista, precio, stock, estado, descripción, categoría e imagen.
- `CD` y `Vinilo` heredarán de `Disco`.
- Una columna discriminadora permitirá a SQLAlchemy reconstruir el tipo correcto al consultar la tabla de discos.
- Se utilizará herencia de tabla única para mantener el mismo nivel de dificultad que el tutorial.
- `Disco` expondrá comportamientos comunes, como obtener su ficha comercial y calcular su precio final.
- `CD` y `Vinilo` podrán sobrescribir comportamientos relacionados con peso, embalaje o envío, demostrando polimorfismo justificable.
- La lógica específica deberá residir en las clases y no duplicarse mediante condicionales dispersos en las rutas.
- Las contraseñas se manipularán mediante métodos encapsulados en `Usuario`, nunca directamente desde las rutas.
- Los estados y transiciones del pedido deberán representarse con métodos y reglas con nombres propios del dominio.

La herencia no se utilizará artificialmente en todas las entidades. Categorías, pedidos, detalles, tarjetas y facturas se modelarán mediante composición y relaciones normales.

### 5.5 Convenciones de rutas y formularios

- Las rutas de consulta utilizarán GET.
- Las operaciones que modifican datos utilizarán POST.
- Los formularios de creación y edición podrán compartir una URL para GET y POST cuando simplifique el aprendizaje.
- Flask leerá los datos del formulario, los normalizará y validará antes de construir o modificar objetos.
- Los valores numéricos se convertirán de manera controlada y mostrarán mensajes claros ante errores.
- Después de una escritura exitosa se realizará `commit` y una redirección.
- Ante un error de base de datos se realizará `rollback` antes de continuar usando la sesión SQLAlchemy.
- Se utilizará `url_for` para generar enlaces y evitar direcciones escritas manualmente.
- Los registros inexistentes producirán una respuesta 404 controlada.
- Crear, editar, desactivar, agregar al carrito, confirmar, aprobar y rechazar nunca dependerán de una petición GET.

### 5.6 Jinja2 y mensajes flash

- `base.html` concentrará cabecera, navegación, mensajes flash, contenido principal y pie de página.
- Las páginas específicas extenderán la plantilla base mediante bloques de título y contenido.
- Los discos y categorías se recorrerán con bucles Jinja2 a partir de datos enviados por Flask.
- Las vistas contemplarán resultados vacíos, por ejemplo un catálogo sin discos o un carrito vacío.
- Los mensajes flash utilizarán categorías visuales coherentes para éxito, advertencia y error.
- El navbar cambiará según la existencia de una sesión y el rol del usuario.
- Ocultar elementos en Jinja2 mejorará la interfaz, pero nunca reemplazará la protección de la ruta en el backend.

### 5.7 Registro, login y sesiones

- El correo de registro se normalizará eliminando espacios y convirtiéndolo a minúsculas.
- Se comprobará la duplicidad del correo antes de registrar y PostgreSQL reforzará la regla con `UNIQUE`.
- El formulario público nunca decidirá el rol: toda cuenta pública se creará como cliente.
- Las contraseñas se guardarán como hash mediante Werkzeug.
- El login devolverá un mensaje genérico cuando las credenciales sean incorrectas.
- La sesión conservará solamente identificadores y datos mínimos necesarios, como ID, nombre y rol.
- El logout limpiará completamente la sesión.
- Los decoradores se implementarán con preservación de la función original y comprobarán primero la sesión y después el rol.
- Las rutas administrativas exigirán el rol de administrador aunque el enlace no aparezca en la interfaz.
- El carrito, perfil, métodos de pago y pedidos exigirán una sesión de cliente.

### 5.8 Carrito basado en sesión

- El carrito inicial se almacenará como un diccionario simple dentro de la sesión Flask.
- Las claves de los discos se guardarán como texto para que la sesión pueda serializarse correctamente.
- La cantidad se incrementará cuando el mismo disco vuelva a agregarse.
- Después de modificar el diccionario se reasignará el carrito a la sesión para garantizar que Flask registre el cambio.
- La vista del carrito volverá a consultar cada disco en PostgreSQL.
- Los discos inexistentes o inactivos no se procesarán como compras válidas.
- Los subtotales se calcularán utilizando el comportamiento polimórfico del disco.
- El carrito de sesión será temporal; al confirmar el checkout, los datos históricos se copiarán a `Pedido` y `DetallePedido`.

### 5.9 Mejoras necesarias respecto al tutorial base

Las siguientes correcciones amplían el tutorial sin abandonar su metodología:

- Los importes monetarios se planificarán con un tipo decimal de PostgreSQL, no con números flotantes.
- `init_db.py` no borrará automáticamente la base de datos en cada ejecución.
- La eliminación de discos será lógica para preservar pedidos y reportes.
- Las validaciones del navegador se repetirán en Flask y PostgreSQL.
- Las operaciones críticas de aprobación y stock serán transaccionales.
- Las tarjetas no guardarán PAN completo, CVV ni PIN legible.
- Los formularios que modifican datos deberán incorporar protección CSRF durante la implementación.
- Las excepciones se registrarán internamente; el usuario recibirá mensajes comprensibles sin detalles sensibles.
- El modo debug se limitará al entorno de desarrollo.

### 5.10 Modelo de datos de referencia para New Records

El modelo definitivo se documentará mediante un diagrama entidad-relación antes de crear las tablas. Como referencia obligatoria, la base incluirá las siguientes entidades y responsabilidades.

#### `usuarios`

- Identificador entero como PK.
- Nombre completo obligatorio.
- Correo normalizado, obligatorio y único.
- Hash de contraseña obligatorio.
- Rol obligatorio con valores limitados a cliente y administrador.
- Teléfono, dirección y ciudad para el perfil.
- Fecha de registro con valor por defecto.
- Estado activo para impedir acceso sin perder el historial.

#### `categorias`

- Identificador entero como PK.
- Nombre musical obligatorio y único.
- Identificador legible para URL obligatorio y único.
- Descripción e imagen.
- Estado activo con valor por defecto verdadero.
- Relación uno-a-muchos con discos.

#### `discos`

- Identificador entero como PK.
- FK obligatoria hacia categoría.
- Código o SKU obligatorio y único.
- Álbum y artista obligatorios.
- Descripción comercial.
- Precio decimal obligatorio y no negativo.
- Stock entero obligatorio y no negativo.
- Formato discriminador limitado a CD o VINILO.
- Peso y datos de embalaje necesarios para el comportamiento físico.
- Ruta de portada.
- Estado activo y fechas de creación y actualización.
- La columna de formato funcionará también como discriminador para la herencia polimórfica de SQLAlchemy.

#### `metodos_pago`

- Identificador entero como PK.
- FK obligatoria hacia el usuario propietario.
- Token simulado o del proveedor, nunca número completo de tarjeta.
- Marca, últimos cuatro dígitos, titular, mes y año de vencimiento.
- Indicador de método predeterminado.
- Fecha de verificación y estado activo.
- Restricciones para mes válido, cuatro dígitos y vencimiento coherente.

#### `verificaciones_tarjeta`

- Identificador entero como PK.
- FK obligatoria hacia usuario.
- Hash del PIN, nunca PIN legible.
- Fecha de creación y caducidad.
- Número de intentos con valor inicial cero y límite definido.
- Estado utilizado o verificado.
- Referencia temporal para asociar la verificación con la tarjeta en proceso.

#### `pedidos`

- Identificador entero como PK.
- Número público de pedido obligatorio y único.
- FK obligatoria hacia el cliente.
- FK hacia el método de pago verificado.
- Estado limitado a PENDIENTE, APROBADO o RECHAZADO.
- Total decimal obligatorio y no negativo.
- Fechas de creación y revisión.
- FK opcional hacia el administrador que revisó.
- Razón de rechazo opcional, obligatoria cuando el estado sea rechazado.
- Relación uno-a-muchos con detalles.

#### `detalles_pedido`

- Identificador entero como PK.
- FK obligatoria hacia pedido.
- FK obligatoria hacia disco.
- Cantidad entera mayor que cero.
- Precio unitario histórico decimal y no negativo.
- Copia histórica de álbum, artista y formato.
- Restricción única opcional por pedido y disco para evitar líneas duplicadas.
- El subtotal se calculará a partir de cantidad y precio unitario.

#### `transacciones_pago`

- Identificador entero como PK.
- FK obligatoria y única hacia pedido para el cobro simulado principal.
- FK obligatoria hacia método de pago.
- Monto decimal no negativo.
- Estado limitado a PENDIENTE, APROBADA o RECHAZADA.
- Referencia simulada única y fecha de procesamiento.
- Nunca almacenará información sensible completa de la tarjeta.

#### `facturas`

- Identificador entero como PK.
- FK obligatoria hacia pedido.
- Número de documento obligatorio y único.
- Tipo limitado a COMPROBANTE_PENDIENTE o FACTURA_FINAL.
- Fecha de emisión.
- Ubicación o nombre controlado del PDF generado.
- Restricción única por pedido y tipo para evitar documentos duplicados.

### 5.11 Relaciones y reglas de eliminación

- Una categoría puede tener muchos discos; un disco pertenece a una categoría.
- Un usuario puede tener varios métodos de pago y verificaciones.
- Un cliente puede realizar varios pedidos.
- Un pedido contiene uno o más detalles.
- Un disco puede aparecer en muchos detalles históricos.
- Un administrador puede revisar muchos pedidos.
- Un pedido puede tener una transacción simulada y hasta dos documentos: comprobante pendiente y factura final.
- No se eliminarán físicamente usuarios, categorías o discos con historial relacionado.
- Los detalles podrán eliminarse en cascada únicamente cuando se elimine un pedido de prueba que todavía no represente una venta real.
- Las FK de información histórica utilizarán una política restrictiva o de conservación adecuada.

### 5.12 Flujo de creación e inicialización de PostgreSQL

La preparación de la base seguirá estos pasos, que deberán documentarse en el README:

1. Instalar PostgreSQL y confirmar que el servicio está activo.
2. Crear una base exclusiva para New Records con codificación UTF-8.
3. Crear un usuario de aplicación diferente del superusuario `postgres`.
4. Concederle solamente los permisos necesarios sobre la base y su esquema.
5. Configurar las credenciales locales mediante `.env`.
6. Comprobar la conexión desde Flask.
7. Definir todos los modelos antes de ejecutar la creación inicial.
8. Crear las tablas mediante SQLAlchemy dentro del contexto de la aplicación.
9. Aplicar las restricciones, funciones, triggers y procedimientos versionados.
10. Ejecutar `init_db.py` para cargar datos propios de New Records.
11. Consultar PostgreSQL para comprobar categorías, discos, tipos polimórficos, usuarios y restricciones.
12. Registrar los cambios posteriores del esquema mediante migraciones.

`init_db.py` será idempotente: si una categoría, disco o usuario inicial ya existe, lo actualizará de manera controlada o lo omitirá; no duplicará información. La eliminación total de tablas no formará parte del flujo normal.

### 5.13 Integridad, triggers y procedimientos previstos

Las validaciones simples se resolverán primero con tipos correctos, nulabilidad, `CHECK`, `DEFAULT`, `UNIQUE` y FK. Los triggers se reservarán para reglas que no puedan expresarse limpiamente con esas restricciones.

Se planifican como máximo los siguientes triggers:

- Actualizar automáticamente la fecha de modificación de discos y categorías.
- Impedir una transición de pedido incompatible con su estado actual si la operación no se ejecuta mediante el procedimiento autorizado.
- Validar coherencia adicional entre rechazo, administrador revisor y razón de rechazo cuando una restricción normal no sea suficiente.

Se planifican los siguientes procedimientos almacenados:

- **Aprobar pedido:** bloquear el pedido y los discos involucrados, comprobar que siga pendiente, verificar stock de todas las líneas, registrar el cobro simulado, descontar existencias, marcar el pedido como aprobado y dejar preparada la emisión de factura. Todo deberá completarse o revertirse como una sola transacción.
- **Rechazar pedido:** comprobar que siga pendiente, registrar administrador, razón y fecha, y cambiar el estado sin modificar stock.

El carrito no requerirá un procedimiento mientras permanezca en la sesión. La operación crítica comienza cuando el carrito se convierte en pedido y especialmente cuando el administrador lo aprueba.

### 5.14 Consultas de reportes que deben conservarse

El archivo `database/reports.sql` documentará como mínimo:

- **Ventas por periodo:** pedidos aprobados unidos con usuarios y detalles, agrupados por día, semana o año, mostrando cantidad de pedidos, unidades y total vendido.
- **Discos más vendidos:** pedidos aprobados unidos con detalles y discos, agrupados por álbum y artista, ordenados por unidades vendidas.
- **Géneros más vendidos:** pedidos aprobados unidos con detalles, discos y categorías, agrupados por género, mostrando unidades e ingresos.

Las consultas deberán utilizar múltiples `JOIN`, agregaciones, filtros por estado y parámetros de fecha. Los resultados mostrados por Flask deberán coincidir con la ejecución directa en PostgreSQL.

## 6. Regla de avance y aprobación

El plan es secuencial. En cada ciclo de trabajo se seguirá este proceso:

1. Presentar el alcance detallado de una sola fase.
2. Identificar archivos afectados, reglas de negocio, pruebas y criterios de aceptación.
3. Solicitar aprobación explícita.
4. Implementar únicamente la fase aprobada.
5. Verificar el resultado y comunicar los hallazgos.
6. Solicitar autorización antes de detallar o implementar la fase siguiente.

La lista completa de fases aparece a continuación para demostrar la cobertura del proyecto. Sin embargo, en este documento solo está desarrollada en profundidad la **Fase 1**. Las demás fases son una hoja de ruta resumida y permanecen bloqueadas.

## 7. Hoja de ruta completa

### Fase 1 - Preparación del proyecto y saneamiento del prototipo

**Estado:** completada; pendiente de aprobación para iniciar la Fase 2.

Tareas principales:

- Revisar y preservar el prototipo original.
- Corregir los problemas de codificación UTF-8.
- Definir la estructura mínima de archivos y carpetas.
- Preparar Git, `.gitignore`, variables de entorno y documentación inicial.
- Verificar Python, PostgreSQL y las dependencias necesarias.
- Organizar los HTML e imágenes para su futura adaptación a Flask.

### Fase 2 - Base Flask, configuración y conexión con PostgreSQL

**Estado:** completada; pendiente de aprobación para iniciar la Fase 3.

Tareas previstas:

- Crear en PostgreSQL una base de datos de desarrollo identificada como New Records, sin reutilizar el nombre `tienda_online` del tutorial.
- Declarar en `.env` usuario, contraseña, host, puerto, nombre de base y clave secreta; mantener ese archivo fuera de Git.
- Centralizar en `config.py` la lectura de variables y la URI de PostgreSQL.
- Declarar una única instancia de SQLAlchemy en `models.py` sin vincularla inmediatamente a una aplicación.
- Crear la aplicación Flask en `app.py`, cargar la configuración y conectar la instancia mediante inicialización diferida.
- Mantener por ahora las rutas en `app.py`, conforme al nivel y estructura de los tutoriales.
- Comprobar la conexión mediante una operación de lectura controlada.
- Configurar Flask para utilizar `templates/` y `static/`.
- Crear `base.html` con bloques de título y contenido, navegación y espacio para mensajes flash.
- Crear una ruta inicial que renderice la portada de New Records.
- Utilizar `url_for` desde el comienzo para todos los enlaces internos.
- Preparar páginas básicas para errores 403, 404 y 500.
- Verificar que el servidor inicia, sirve los recursos del prototipo y puede detenerse sin errores.

Resultado de ejecución:

- Se crearon `app.py`, `config.py` y `models.py` con inicialización diferida de SQLAlchemy.
- Se configuraron `.env` y `.env.example` sin versionar ni mostrar credenciales reales.
- Se creó `base.html` con navegación, bloques Jinja2 y espacio para mensajes flash.
- Las cuatro páginas del prototipo se convirtieron en plantillas hijas y utilizan `url_for`.
- Se añadieron páginas propias para errores 403, 404 y 500.
- Se añadió el comando de lectura `check-db` para verificar usuario, base, codificación y propietario.
- Se creó la base `new_records_db` con codificación UTF-8.
- Se creó el usuario exclusivo `new_records_app` y se asignó como propietario de la base.
- La aplicación se conecta con `new_records_app`, no con el superusuario `postgres`.
- Las rutas públicas, recursos estáticos y página 404 respondieron correctamente mediante Flask.
- Las seis pruebas automatizadas de la fase finalizaron correctamente.
- No se crearon modelos del dominio, tablas ni datos iniciales de la Fase 3.

### Fase 3 - Modelo relacional, POO e inicialización de datos

**Estado:** completada; pendiente de aprobación para iniciar la Fase 4.

Tareas previstas:

- Diseñar el modelo entidad-relación normalizado exclusivamente para New Records.
- Definir PK, FK, relaciones, índices, obligatoriedad y reglas de eliminación.
- Modelar `Usuario`, `Categoria`, `Disco`, `CD`, `Vinilo`, `MetodoPago`, `VerificacionTarjeta`, `Pedido`, `DetallePedido` y `Factura`.
- Usar una relación uno-a-muchos entre categoría y discos, usuario y métodos de pago, usuario y pedidos, y pedido y detalles.
- Mantener en cada detalle una copia histórica del álbum, artista, formato, precio unitario y cantidad.
- Implementar herencia de tabla única para `Disco`, `CD` y `Vinilo`, con una columna discriminadora controlada por SQLAlchemy.
- Definir en `Disco` el comportamiento común y sobrescribir en `CD` y `Vinilo` únicamente reglas físicas justificables.
- Evitar las clases y campos del tutorial correspondientes a licencias digitales o vencimiento de perecibles.
- Usar tipos decimales para precios y totales, enteros para cantidades y fechas con hora para eventos del sistema.
- Incorporar `CHECK` para precio no negativo, stock no negativo, cantidad positiva, vencimiento válido, rol permitido y estado de pedido permitido.
- Incorporar `UNIQUE` para correo, código de disco, identificador de categoría, número de pedido y número de factura.
- Incorporar valores `DEFAULT` para rol cliente, disco activo, stock inicial, fecha de creación y pedido pendiente.
- Crear `init_db.py` para ejecutar la inicialización dentro del contexto de Flask.
- Hacer la carga inicial repetible sin duplicar registros.
- Insertar las categorías Rock, Pop y Reggaeton tomadas del prototipo.
- Insertar los discos reales del HTML: álbum, artista, género, precio, descripción, portada, formato y stock inicial definido para demostración.
- Crear un administrador y un cliente de demostración con contraseñas protegidas, nunca visibles en el repositorio de producción.
- No ejecutar `drop_all()` automáticamente; cualquier reinicio destructivo deberá ser una acción explícita y limitada al desarrollo.
- Comprobar desde PostgreSQL que la columna discriminadora reconstruye correctamente objetos `CD` y `Vinilo`.
- Documentar el modelo ER y el diccionario de datos antes de avanzar.

Resultado de ejecución:

- Se implementaron nueve tablas normalizadas para usuarios, catálogo, pagos, pedidos y facturas.
- Se definieron PK, FK, relaciones, índices y políticas de eliminación según el historial del negocio.
- Se incorporaron restricciones `CHECK`, `DEFAULT`, `UNIQUE` y valores obligatorios en PostgreSQL.
- `Disco` funciona como clase padre polimórfica abstracta y `CD`/`Vinilo` como clases concretas.
- La consulta de la clase padre reconstruye correctamente instancias `CD` y `Vinilo` desde la columna `formato`.
- `precio_final()` presenta comportamiento diferente según el formato físico.
- Las contraseñas de `Usuario` se encapsulan mediante métodos de hash y verificación.
- `init_db.py` crea solamente tablas faltantes y no contiene `drop_all()`.
- Se cargaron 3 categorías, 12 discos del prototipo y 2 cuentas de demostración.
- Dos ejecuciones consecutivas conservaron los mismos conteos, demostrando idempotencia.
- Las contraseñas iniciales se obtuvieron del `.env` local y no se incluyeron en archivos versionables.
- PostgreSQL rechazó correctamente una operación de prueba con stock negativo.
- Se generó `database/schema_fase3.sql` como referencia del esquema real validado.
- Se documentaron el modelo entidad-relación y el diccionario de datos.
- Las trece pruebas acumuladas hasta esta fase finalizaron correctamente, incluyendo la verificación de defaults y restricciones directamente en PostgreSQL.

### Fase 4 - Autenticación, perfil, sesiones y roles

**Estado:** completada; pendiente de aprobación para iniciar la Fase 5.

Tareas previstas:

- Implementar registro público asignando siempre el rol `cliente` desde el backend.
- Normalizar el correo con recorte de espacios y conversión a minúsculas.
- Comprobar la duplicidad en Flask y reforzarla con la restricción `UNIQUE` de PostgreSQL.
- Validar nombre, correo y longitud de contraseña en navegador, Flask y base de datos cuando corresponda.
- Encapsular en `Usuario` los métodos para generar y verificar el hash de contraseña con Werkzeug.
- Implementar login con un mensaje genérico ante correo o contraseña incorrectos.
- Guardar en la sesión únicamente el ID, nombre y rol necesarios para la navegación.
- Implementar logout mediante limpieza completa de la sesión.
- Construir la visualización y edición del perfil, limitando cada usuario a sus propios datos.
- Crear en `auth.py` un decorador de sesión requerida y otro de rol requerido.
- Preservar los metadatos de las funciones decoradas.
- Verificar primero la existencia de sesión y después el rol, para devolver mensajes correctos.
- Colocar el decorador de autorización en todas las rutas administrativas, no solamente condiciones en las plantillas.
- Mostrar enlaces de perfil y carrito solamente al cliente, y panel de administración solamente al administrador.
- Incorporar mensajes flash diferenciados para éxito, advertencia y error.
- Probar acceso directo a URLs protegidas como visitante, cliente y administrador.

Resultado de ejecución:

- Se creó el módulo `auth.py` con los decoradores `@login_requerido` y `@rol_requerido(*roles)`, preservando metadatos mediante `wraps`.
- Se implementaron las funciones auxiliares `iniciar_sesion()`, `cerrar_sesion()` y `obtener_usuario_actual()`.
- Se incorporaron en `app.py` las rutas `/registro`, `/login`, `/logout`, `/perfil` y el panel `/admin/dashboard`.
- El registro asigna de forma forzada el rol `cliente`, normaliza correos a minúsculas y valida contraseñas con longitud mínima de 8 caracteres.
- El login verifica credenciales contra el hash de contraseñas de PostgreSQL y devuelve mensajes genéricos de error.
- Se implementó la visualización y edición segura del perfil del usuario autenticado con persistencia en base de datos.
- Las rutas administrativas quedan restringidas mediante código de estado `403` ante accesos no autorizados.
- Se crearon las plantillas Jinja2 `templates/auth/login.html`, `templates/auth/registro.html`, `templates/auth/perfil.html` y `templates/admin/dashboard.html`.
- Se actualizó `base.html` con navegación responsive condicional para visitantes, clientes y administradores, e integración de mensajes flash con estilos (`success`, `warning`, `error`, `info`).
- Se añadieron estilos CSS dedicados en `static/css/styles.css` respetando el diseño cyberpunk oscuro y acentos neón.
- Se agregaron 11 pruebas automatizadas en `tests/test_auth.py`, alcanzando un total de **24/24 pruebas pasando exitosamente**.

### Fase 5 - Catálogo dinámico y detalle de discos

**Estado:** completada; pendiente de aprobación para iniciar la Fase 6.

Tareas previstas:

- Convertir inicio, categorías y productos en plantillas hijas de `base.html`.
- Eliminar de los HTML los arreglos y tarjetas escritos manualmente una vez que `init_db.py` provea los datos.
- Cargar únicamente categorías activas y discos activos desde PostgreSQL.
- Construir el menú desplegable global recorriendo las categorías recibidas desde Flask.
- Implementar filtros por categoría mediante parámetros de URL o rutas con identificador legible.
- Utilizar búsquedas que produzcan un 404 controlado cuando el disco solicitado no exista.
- Crear el detalle con álbum, artista, género, tipo real `CD` o `Vinilo`, precio final polimórfico, descripción y stock.
- Mostrar la información física específica del subtipo sin utilizar condiciones de productos digitales o perecibles.
- Incorporar discos recomendados de la misma categoría, excluyendo el disco actual y limitando el resultado.
- Usar bucles Jinja2 y mensajes alternativos para catálogos, categorías o recomendaciones vacías.
- Generar enlaces con `url_for` y no con rutas HTML escritas manualmente.
- Mantener el diseño responsive del prototipo y corregir accesibilidad básica del menú, imágenes y controles.

Resultado de ejecución:

- Se dinamizaron las rutas `/categorias`, `/productos` y la nueva ruta `/productos/<codigo>` en `app.py`.
- Se incorporó un menú desplegable global y responsive que carga los géneros activos desde PostgreSQL.
- Se eliminaron las listas estáticas de discos y categorías de los archivos HTML, cargándose dinámicamente desde PostgreSQL.
- Las consultas cargan exclusivamente registros con `activo == True`.
- Se implementó el filtrado dinámico por categoría (`?categoria=slug`) y búsqueda por texto (`?q=termino`).
- Se construyó la plantilla `templates/detalle_producto.html` mostrando álbum, artista, género, SKU, tipo `CD` o `Vinilo`, descripción, stock y desglose polimórfico del cálculo de precio final (`precio_base`, costo por peso y embalaje).
- Se implementó la sección de discos recomendados de la misma categoría (hasta 4 discos excluyendo el actual).
- Se agregaron estilos dedicados en `static/css/styles.css` para tarjetas, barra de búsqueda, migas de pan, estados vacíos y desglose de precios.
- Se crearon 9 pruebas automatizadas en `tests/test_catalogo.py`, alcanzando un total de **33/33 pruebas pasando exitosamente**.

### Fase 6 - Carrito y preparación del checkout

**Estado:** completada; pendiente de aprobación para iniciar la Fase 7.

Tareas previstas:

- Implementar el carrito como diccionario dentro de la sesión Flask, siguiendo la Semana 3.
- Guardar los identificadores de discos como claves de texto para asegurar su serialización.
- Incrementar la cantidad cuando el cliente agregue nuevamente el mismo disco.
- Reasignar el diccionario a la sesión después de cada modificación.
- Proteger todas las acciones del carrito para el rol cliente.
- Utilizar POST para agregar, actualizar o quitar discos.
- Volver a consultar cada disco en PostgreSQL al mostrar el carrito.
- Ignorar o advertir sobre discos inexistentes, inactivos o sin stock.
- Impedir cantidades menores que uno o mayores que el stock disponible.
- Calcular subtotales usando el método polimórfico de precio final.
- Calcular el total en el servidor y no confiar en valores enviados por JavaScript.
- Mostrar un estado claro cuando el carrito esté vacío.
- Preparar el resumen de checkout sin crear todavía el pedido definitivo.

Resultado de ejecución:

- Se creó el módulo `cart.py` con las funciones `obtener_carrito_sesion()`, `agregar_disco()`, `actualizar_cantidad()`, `eliminar_disco()`, `vaciar_carrito()` y `obtener_detalle_carrito()`.
- Los IDs de discos se serializan como texto y la sesión se fuerza como modificada ante cada cambio.
- Cada consulta revalida existencias en PostgreSQL y ajusta cantidades automáticamente según el stock real.
- Los subtotales e importe total acumulado se calculan estrictamente en el backend mediante el método polimórfico `disco.precio_final()`.
- Se incorporaron en `app.py` las rutas `/carrito` (`GET`), `/carrito/agregar/<disco_id>` (`POST`), `/carrito/actualizar/<disco_id>` (`POST`), `/carrito/eliminar/<disco_id>` (`POST`), `/carrito/vaciar` (`POST`) y `/checkout/resumen` (`GET`), todas protegidas exclusivamente para el rol `cliente`.
- Se actualizaron el context processor de `app.py` y `templates/base.html` para incluir un enlace e ícono con badge contador dinámico (`total_items_carrito`).
- Se crearon las plantillas `templates/carrito.html` y `templates/checkout_resumen.html`.
- Se vinculó el botón "Agregar al Carrito" en `templates/detalle_producto.html`.
- Se añadieron estilos CSS dedicados en `static/css/styles.css` para la grilla de carrito, controles de cantidad, tarjetas de resumen y badge contador.
- Se agregaron 9 pruebas automatizadas en `tests/test_carrito.py`, alcanzando un total de **42/42 pruebas pasando exitosamente**. Las pruebas web se aíslan mediante transacciones reversibles para no alterar los datos de desarrollo.

### Fase 7 - Métodos de pago y verificación por PIN

**Estado:** completada y verificada.

Tareas previstas:

- Crear la pantalla de métodos de pago del cliente.
- Validar datos básicos de tarjeta en frontend, backend y base de datos.
- Conservar únicamente marca, últimos cuatro dígitos, vencimiento y token simulado.
- Generar un PIN temporal con caducidad y límite de intentos.
- Enviar el PIN mediante SMTP.
- Confirmar la tarjeta únicamente después de verificar el PIN.
- Seleccionar automáticamente el método verificado durante el checkout.

Resultado de ejecución:

- Se instaló `Flask-Mail 0.10.0` y se actualizaron `requirements.txt` y `config.py` con los parámetros SMTP.
- Se creó `mailer.py` con la función `enviar_pin()` y detección automática de SMTP configurado; en modo desarrollo el PIN se muestra en un mensaje flash.
- Se creó `payments.py` con las funciones `crear_verificacion()`, `verificar_pin()`, `obtener_metodos_pago_activos()`, `desactivar_metodo_pago()` y `establecer_predeterminado()`.
- El PIN se genera con `secrets` como 6 dígitos numéricos, se almacena únicamente como hash Werkzeug en `verificaciones_tarjeta.pin_hash` y caduca en 5 minutos con un máximo de 3 intentos, replicado en PostgreSQL.
- Solo se persisten: marca, últimos 4 dígitos, titular, mes/año de vencimiento y un token UUID simulado. Nunca el número completo ni el CVV.
- Se incorporaron en `app.py` las rutas `/pago/metodos` (`GET`), `/pago/agregar` (`GET`, `POST`), `/pago/verificar/<token>` (`GET`, `POST`), `/pago/predeterminado/<id>` (`POST`) y `/pago/eliminar/<id>` (`POST`), todas protegidas con `@rol_requerido('cliente')`.
- Se actualizó `/checkout/resumen` para mostrar los métodos de pago verificados del usuario o un aviso con enlace a registro si no tiene ninguno.
- Se crearon las plantillas `templates/pago/metodos.html`, `templates/pago/agregar.html` y `templates/pago/verificar_pin.html`.
- Se eliminó el aviso placeholder de Fase 7 de `templates/checkout_resumen.html`.
- Se añadieron estilos CSS dedicados en `static/css/styles.css` para tarjetas de crédito, badge predeterminada, campo PIN, indicador de intentos y aviso de caducidad.
- Se agregaron 10 pruebas automatizadas en `tests/test_pagos.py`, incluyendo vencimiento dinámico y bloqueo exacto del PIN, alcanzando un total acumulado de **52 pruebas**.

### Fase 8 - Pedidos, stock y cobro simulado

**Estado:** completada y verificada.

Tareas previstas:

- Convertir el carrito confirmado en pedido y detalles históricos.
- Asignar estado inicial `PENDIENTE`.
- Validar nuevamente precio, actividad y stock.
- Implementar un procedimiento almacenado para aprobar pedidos y descontar stock.
- Implementar el cobro simulado de forma controlada.
- Evitar aprobación duplicada o stock negativo.
- Vaciar el carrito solamente después de crear correctamente el pedido.
- Construir historial y detalle de pedidos del cliente.

Resultado de ejecución:

- Se creó el módulo `services.py` con las funciones transaccionales `procesar_checkout()`, `generar_numero_pedido()`, `generar_referencia_pago()`, `obtener_pedidos_cliente()` y `obtener_pedido_por_numero()`.
- La creación de `Pedido`, `DetallePedido` y `TransaccionPago` se ejecuta dentro de una transacción atómica con `db.session.commit()` y `rollback()` automático ante cualquier error o inconsistencia de stock.
- Se incorporó `aprobar_pedido_new_records` como procedimiento almacenado idempotente. Bloquea el pedido y los discos en orden estable, evita aprobaciones duplicadas y descuenta stock sin carreras concurrentes.
- Cada línea de `DetallePedido` almacena una copia histórica inmutable de álbum, artista, formato, precio unitario (`disco.precio_final()`) y cantidad.
- El carrito en sesión solo se vacía una vez confirmado el guardado exitoso en base de datos.
- Se incorporaron en `app.py` las rutas `/checkout/confirmar` (`POST`), `/pedidos` (`GET`) y `/pedidos/<numero>` (`GET`).
- Se crearon las plantillas `templates/pedidos/lista.html` y `templates/pedidos/detalle.html`.
- Se actualizó `templates/checkout_resumen.html` para incluir el selector de método de pago verificado y el botón de confirmación de pedido.
- Se actualizó `templates/base.html` con enlaces directos a "Mis Pedidos" y "Métodos de Pago" en el menú de navegación.
- Se añadieron estilos CSS dedicados en `static/css/styles.css` para badges de estado (`PENDIENTE`, `APROBADO`, `RECHAZADO`), tarjetas de detalle de compra e historial.
- Se agregaron 9 pruebas automatizadas en `tests/test_pedidos.py`, incluyendo rollback cuando falla el comprobante, alcanzando un total acumulado de **61 pruebas**.

### Fase 9 - Comprobantes PDF y notificaciones

**Estado:** completada y verificada.

Tareas previstas:

- Generar un comprobante de pedido pendiente después del checkout.
- Generar la factura final después de la aprobación administrativa.
- Incluir cliente, número de pedido, discos, cantidades, precios y total.
- Permitir descarga e impresión.
- Restringir cada documento a su propietario o a un administrador.
- Enviar notificaciones de creación, aprobación o rechazo.

Resultado de ejecución:

- Se creó el módulo `pdf_generator.py` utilizando ReportLab (`SimpleDocTemplate`, `Table`, `Paragraph`, `TableStyle`, `colors`) para la maquetación estética de documentos imprimibles y descargables.
- Se implementó la generación automática y transaccional de dos tipos de documentos: `COMPROBANTE_PENDIENTE` durante el checkout y `FACTURA_FINAL` durante la aprobación administrativa.
- Cada emisión registra o actualiza la entidad `Factura` en PostgreSQL con su número único (`COMP-<numero>` o `FAC-<numero>`), tipo, fecha de emisión y ruta del archivo en `docs/comprobantes/`.
- Se incorporaron en `app.py` los endpoints de descarga `/pedidos/<numero>/comprobante` y `/pedidos/<numero>/factura`, restringiendo el acceso exclusivamente al cliente propietario o a un administrador.
- La descarga de la Factura Final valida estrictamente que el pedido se encuentre en estado `APROBADO`.
- Se añadieron en `mailer.py` las funciones `notificar_creacion_pedido()` y `notificar_cambio_estado()`, integradas en el flujo de confirmación de checkout.
- Se actualizaron las plantillas `templates/pedidos/detalle.html` y `templates/pedidos/lista.html` con botones y accesos rápidos de descarga en formato PDF.
- Se agregaron estilos CSS en `static/css/styles.css` para los botones y notas de documentos PDF.
- Se agregaron 6 pruebas automatizadas en `tests/test_pdf_notificaciones.py`, alcanzando un total acumulado de **67 pruebas**.

### Fase 10 - Administración de catálogo y pedidos

**Estado:** completada y verificada; preparada para iniciar la Fase 11.

Tareas previstas:

- Crear el dashboard administrativo.
- Implementar CRUD de discos.
- Implementar CRUD de categorías.
- Usar desactivación lógica para datos con historial.
- Impedir desactivar categorías con productos activos sin una decisión explícita.
- Construir la bandeja de pedidos pendientes.
- Mostrar usuario y lista exacta de discos en el detalle.
- Permitir aprobación o rechazo con una razón registrada.
- Aplicar el patrón GET/POST del tutorial en los formularios de creación y edición.
- Convertir de forma controlada precio y stock antes de actualizar los modelos.
- Ejecutar `commit` después de operaciones válidas y `rollback` ante errores.
- Mostrar mensajes flash específicos sin exponer excepciones internas.
- Proteger todas las rutas de creación, edición, desactivación, aprobación y rechazo con el rol administrador.
- Implementar desactivación lógica mediante el estado activo, siguiendo la eliminación suave enseñada en la Semana 2.
- Verificar con solicitudes directas que ocultar botones no sea el único control de seguridad.

Resultado de ejecución:

- Se actualizaron en `app.py` y `services.py` las rutas y funciones de administración:
  - Dashboard administrativo (`/admin/dashboard`) con métricas KPI en tiempo real (discos activos, categorías, pedidos pendientes y facturación acumulada).
  - CRUD completo de Discos (`/admin/discos`, `/admin/discos/nuevo`, `/admin/discos/<id>/editar`, `/admin/discos/<id>/desactivar`, `/admin/discos/<id>/reactivar`), con soporte polimórfico para `CD` y `Vinilo`.
  - CRUD completo de Categorías (`/admin/categorias`, `/admin/categorias/nueva`, `/admin/categorias/<id>/editar`, `/admin/categorias/<id>/desactivar`, `/admin/categorias/<id>/reactivar`).
  - Eliminación suave (Soft Delete) implementada mediante alternancia del campo booleano `activo`.
  - Las categorías con discos activos exigen confirmación explícita y desactivan lógicamente sus discos para mantener un catálogo coherente.
  - Bandeja de pedidos con pestañas de filtrado por estado (`/admin/pedidos`).
  - Auditoría técnica de pedido (`/admin/pedidos/<numero>`) con comprobación en vivo de existencias físicas disponibles.
  - Aprobación atómica de pedidos (`/admin/pedidos/<numero>/aprobar`): descuenta stock del inventario, marca `APROBADO`, actualiza la transacción de pago, genera la `FACTURA_FINAL` en PDF y notifica al cliente.
  - Rechazo de pedidos (`/admin/pedidos/<numero>/rechazar`): exige motivo explícito obligatorio, marca `RECHAZADO`, actualiza cobro a `RECHAZADA`, no altera existencias y notifica al cliente.
- Todas las rutas administrativas están estrictamente protegidas con `@rol_requerido('administrador')`.
- Se crearon las plantillas `templates/admin/discos/lista.html`, `templates/admin/discos/formulario.html`, `templates/admin/categorias/lista.html`, `templates/admin/categorias/formulario.html`, `templates/admin/pedidos/lista.html` y `templates/admin/pedidos/detalle.html`, y se actualizó `templates/admin/dashboard.html`.
- Se añadieron estilos dedicados en `static/css/styles.css` para KPIs, tablas administrativas, badges de stock y decisiones.
- Se agregaron 11 pruebas automatizadas en `tests/test_admin.py`, incluyendo procedimiento PostgreSQL, aprobación duplicada, cascada explícita y rollback de factura. La suite completa alcanza **78/78 pruebas pasando exitosamente** sin persistir datos de prueba.

### Fase 11 - Reportes administrativos

**Estado:** completada y verificada; preparada para iniciar la Fase 12.

Tareas previstas:

- Crear reporte de ventas diario, semanal y anual.
- Crear ranking de discos más vendidos.
- Crear ranking de géneros más vendidos.
- Utilizar consultas con múltiples `JOIN`, agrupaciones y agregaciones.
- Filtrar únicamente pedidos aprobados.
- Mostrar totales y cantidades de forma clara en el dashboard.
- Guardar y documentar las consultas relevantes en `database/reports.sql`.

Resultado de ejecución:

- Se creó el script [`database/reports.sql`](file:///c:/Users/Windows-PC/OneDrive%20-%20Pontificia%20Universidad%20Cat%C3%B3lica%20del%20Ecuador/Documentos/PUCE/proyectofinalll/new-records-ecommerce/database/reports.sql) documentando las consultas SQL analíticas de ventas con sintaxis optimizada (`DATE_TRUNC`, CTEs, `JOIN`, `GROUP BY`, `SUM` y `COUNT`) filtrando estrictamente por pedidos con estado `APROBADO`.
- Se incorporaron en [`services.py`](file:///c:/Users/Windows-PC/OneDrive%20-%20Pontificia%20Universidad%20Cat%C3%B3lica%20del%20Ecuador/Documentos/PUCE/proyectofinalll/new-records-ecommerce/services.py) las funciones analíticas `obtener_resumen_metricas_ventas()`, `obtener_reporte_ventas_temporal()`, `obtener_ranking_discos()` y `obtener_ranking_categorias()`.
- Se añadió en [`app.py`](file:///c:/Users/Windows-PC/OneDrive%20-%20Pontificia%20Universidad%20Cat%C3%B3lica%20del%20Ecuador/Documentos/PUCE/proyectofinalll/new-records-ecommerce/app.py) la ruta protegida `@app.route("/admin/reportes")` con filtro dinámico de períodos (`diario`, `semanal`, `mensual`).
- Se crearon las plantillas [`templates/admin/reportes.html`](file:///c:/Users/Windows-PC/OneDrive%20-%20Pontificia%20Universidad%20Cat%C3%B3lica%20del%20Ecuador/Documentos/PUCE/proyectofinalll/new-records-ecommerce/templates/admin/reportes.html) y se actualizó [`templates/admin/dashboard.html`](file:///c:/Users/Windows-PC/OneDrive%20-%20Pontificia%20Universidad%20Cat%C3%B3lica%20del%20Ecuador/Documentos/PUCE/proyectofinalll/new-records-ecommerce/templates/admin/dashboard.html).
- Se añadieron estilos CSS dedicados en [`static/css/styles.css`](file:///c:/Users/Windows-PC/OneDrive%20-%20Pontificia%20Universidad%20Cat%C3%B3lica%20del%20Ecuador/Documentos/PUCE/proyectofinalll/new-records-ecommerce/static/css/styles.css) para medallas de ranking, barras de progreso y filtros temporales.
- Se agregaron 7 pruebas automatizadas en [`tests/test_reportes.py`](file:///c:/Users/Windows-PC/OneDrive%20-%20Pontificia%20Universidad%20Cat%C3%B3lica%20del%20Ecuador/Documentos/PUCE/proyectofinalll/new-records-ecommerce/tests/test_reportes.py), alcanzando un total de **85/85 pruebas pasando exitosamente**.

### Fase 12 - Integridad avanzada, seguridad y respaldos

**Estado:** completada y verificada; preparada para iniciar la Fase 13.

Tareas previstas:

- Replicar validaciones críticas mediante restricciones PostgreSQL.
- Incorporar solamente los triggers estrictamente necesarios.
- Verificar y reutilizar el procedimiento almacenado de stock y aprobación implementado en la Fase 8.
- Definir roles mínimos para aplicación, administración y respaldo.
- Revisar protección de rutas, sesiones, secretos y formularios.
- Configurar respaldos con `pg_dump` y restauración con `pg_restore`.
- Probar una restauración completa.

Resultado de ejecución:

- Se creó el script [`database/rules_fases12.sql`](file:///c:/Users/Windows-PC/OneDrive%20-%20Pontificia%20Universidad%20Cat%C3%B3lica%20del%20Ecuador/Documentos/PUCE/proyectofinalll/new-records-ecommerce/database/rules_fases12.sql) con restricciones `CHECK` para calidad de catálogo (precios positivos, peso positivo, stock no negativo, formato CD/VINILO), integridad de usuarios (roles válidos), pedidos (estados válidos, motivo de rechazo obligatorio), transacciones y facturas.
- Se implementó el trigger `trg_discos_actualizar_fecha` para actualización automática de `fecha_actualizacion` en PostgreSQL.
- Se integró la aplicación idempotente de `rules_fases12.sql` dentro de [`init_db.py`](file:///c:/Users/Windows-PC/OneDrive%20-%20Pontificia%20Universidad%20Cat%C3%B3lica%20del%20Ecuador/Documentos/PUCE/proyectofinalll/new-records-ecommerce/init_db.py).
- Se definió la política de mínimo privilegio en [`database/roles_seguridad.sql`](file:///c:/Users/Windows-PC/OneDrive%20-%20Pontificia%20Universidad%20Cat%C3%B3lica%20del%20Ecuador/Documentos/PUCE/proyectofinalll/new-records-ecommerce/database/roles_seguridad.sql) (`new_records_app`, `new_records_backup`, `new_records_admin`).
- Se añadieron cabeceras de seguridad HTTP (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection`, `Referrer-Policy`) y el comando CLI `flask crear-backup` en [`app.py`](file:///c:/Users/Windows-PC/OneDrive%20-%20Pontificia%20Universidad%20Cat%C3%B3lica%20del%20Ecuador/Documentos/PUCE/proyectofinalll/new-records-ecommerce/app.py).
- Se creó el gestor de respaldos [`backup_manager.py`](file:///c:/Users/Windows-PC/OneDrive%20-%20Pontificia%20Universidad%20Cat%C3%B3lica%20del%20Ecuador/Documentos/PUCE/proyectofinalll/new-records-ecommerce/backup_manager.py) y la documentación de operaciones en [`docs/SEGURIDAD_Y_RESPALDOS.md`](file:///c:/Users/Windows-PC/OneDrive%20-%20Pontificia%20Universidad%20Cat%C3%B3lica%20del%20Ecuador/Documentos/PUCE/proyectofinalll/new-records-ecommerce/docs/SEGURIDAD_Y_RESPALDOS.md).
- Se agregaron 9 pruebas automatizadas en [`tests/test_seguridad_respaldos.py`](file:///c:/Users/Windows-PC/OneDrive%20-%20Pontificia%20Universidad%20Cat%C3%B3lica%20del%20Ecuador/Documentos/PUCE/proyectofinalll/new-records-ecommerce/tests/test_seguridad_respaldos.py), alcanzando un total de **94/94 pruebas pasando exitosamente**.

### Fase 13 - Pruebas, documentación y entrega

**Estado:** bloqueada.

Tareas previstas:

- Probar modelos, autenticación, roles, catálogo, carrito, checkout y administración.
- Probar restricciones, triggers y procedimientos directamente en PostgreSQL.
- Ejecutar pruebas de los flujos completos de cliente y administrador.
- Revisar diseño responsive, accesibilidad y mensajes de error.
- Verificar generación y lectura de los PDF.
- Completar README, modelo ER, diccionario de datos y reglas del negocio.
- Revisar historial Git, ramas y ausencia de secretos.
- Preparar datos de demostración y checklist de presentación.
- Repetir los checklists didácticos de los tutoriales ya adaptados: catálogo dinámico, detalle por subtipo, CRUD, eliminación lógica, contraseñas cifradas, sesiones, roles y carrito persistente durante la sesión.
- Confirmar que no quede ningún nombre, dato o regla de la tienda genérica en clases, rutas, plantillas, mensajes, pruebas o documentación.

## 8. Detalle autorizado para revisión: Fase 1

### 8.1 Objetivo

Preparar una base limpia, reproducible y entendible para iniciar la transformación del prototipo estático, sin implementar todavía funcionalidades de e-commerce ni modificar el comportamiento visible del sitio.

### 8.2 Alcance incluido

#### A. Protección del punto de partida

- Registrar el estado actual de los HTML, CSS, JavaScript e imágenes.
- Confirmar que no existan archivos ajenos que deban sobrescribirse.
- Mantener una copia identificable del prototipo antes de convertirlo a Jinja2.
- Confirmar que todos los recursos referenciados por los HTML existen.

#### B. Saneamiento del frontend

- Comprobar y corregir, si fuera necesario, palabras como “Categorías”, “música” y el símbolo de copyright.
- Asegurar que todos los documentos estén guardados realmente como UTF-8.
- Revisar enlaces internos, rutas de imágenes y hojas de estilo.
- Identificar contenido repetido que posteriormente se moverá a `base.html`.
- Registrar mejoras pendientes de accesibilidad sin rediseñar el prototipo.
- Mantener los productos y categorías estáticos durante esta fase; su migración a PostgreSQL corresponde a la Fase 3.

#### C. Estructura mínima del repositorio

- Preparar las carpetas `templates`, `static`, `database`, `migrations`, `tests`, `docs` y `backups`.
- Trasladar los recursos existentes a `static` solamente si las rutas quedan verificadas.
- Reservar la raíz para los módulos principales definidos por los tutoriales.
- Evitar crear Blueprints, repositorios o capas adicionales.

#### D. Preparación del entorno

- Verificar una versión compatible de Python.
- Verificar que PostgreSQL esté instalado y accesible.
- Definir el nombre de la base de datos de desarrollo.
- Preparar un entorno virtual aislado.
- Definir las dependencias mínimas necesarias.
- Crear una plantilla de variables de entorno sin secretos reales.
- Documentar cómo instalar y ejecutar el proyecto localmente.

#### E. Preparación para Git

- Crear o revisar `.gitignore`.
- Excluir `.env`, entorno virtual, cachés, respaldos, facturas generadas y archivos temporales.
- Definir una rama principal estable y ramas de trabajo por fase.
- Evitar incluir credenciales o contraseñas en el repositorio.
- Preparar un README inicial con propósito, requisitos y estado del proyecto.

### 8.3 Archivos previstos en esta fase

Esta fase podrá crear o reorganizar únicamente elementos de infraestructura y documentación:

- `.gitignore`.
- `.env.example`.
- `requirements.txt`.
- `README.md`.
- Carpetas base del proyecto.
- Archivos del prototipo reorganizados dentro de `templates` y `static`.

No se crearán todavía modelos SQLAlchemy, rutas funcionales, tablas, triggers, procedimientos, autenticación ni carrito.

### 8.4 Decisiones que quedan fijadas

- Arquitectura monolítica Flask.
- PostgreSQL como única base de datos objetivo.
- SQLAlchemy como ORM.
- Sesiones Flask conforme a los tutoriales.
- Roles `cliente` y `administrador`.
- Catálogo limitado a CD y vinilo.
- Carrito inicialmente almacenado en sesión.
- Eliminación lógica de discos con historial.
- Tarjetas simuladas y enmascaradas, sin almacenamiento de datos sensibles completos.
- Pedido pendiente antes de la aprobación administrativa.
- Comprobante pendiente y factura final como documentos distintos.

### 8.5 Fuera de alcance de esta fase

- Conexión activa con PostgreSQL.
- Creación de tablas.
- Modelos o herencia SQLAlchemy.
- Registro, login o perfiles.
- CRUD del administrador.
- Catálogo dinámico.
- Carrito y checkout.
- Tarjetas, PIN o correo.
- Pedidos, facturas y reportes.
- Triggers y procedimientos almacenados.
- Despliegue en producción.

### 8.6 Verificaciones de la fase

- El prototipo debe continuar abriendo sus páginas sin recursos rotos.
- Todos los textos deben mostrarse correctamente en español.
- No debe existir ninguna credencial real versionada.
- La estructura debe coincidir con el nivel básico definido.
- Las dependencias y requisitos del entorno deben quedar documentados.
- Git debe mostrar únicamente los cambios intencionales de preparación.

### 8.7 Criterios de aceptación

La Fase 1 se considerará completada cuando:

- El prototipo original esté preservado y revisado.
- La codificación UTF-8 esté corregida.
- La estructura mínima esté preparada.
- Los recursos frontend estén organizados y sus rutas funcionen.
- El entorno requerido esté documentado.
- `.env` y demás archivos sensibles estén excluidos de Git.
- No se haya implementado todavía ninguna funcionalidad de fases posteriores.

### 8.8 Riesgos y mitigaciones

- **Riesgo:** romper rutas de imágenes al reorganizar archivos.  
  **Mitigación:** comprobar cada referencia antes y después del traslado.

- **Riesgo:** perder el prototipo original.  
  **Mitigación:** registrar el punto de partida antes de cualquier reorganización.

- **Riesgo:** agregar complejidad no enseñada en los tutoriales.  
  **Mitigación:** conservar los módulos centrales y evitar patrones avanzados.

- **Riesgo:** versionar contraseñas o respaldos.  
  **Mitigación:** definir `.gitignore` antes de crear archivos locales sensibles.

### 8.9 Resultado de ejecución

- El prototipo original quedó preservado en el commit `9f4e5cf`.
- Las cuatro páginas se trasladaron a `templates/`.
- CSS, JavaScript e imágenes se trasladaron de `assets/` a `static/`.
- Se actualizaron las rutas relativas sin convertir todavía los HTML a Jinja2.
- Se comprobaron 68 referencias locales sin encontrar archivos rotos.
- Las cuatro páginas, la hoja de estilos, el JavaScript y el banner respondieron correctamente mediante una vista previa HTTP local.
- Los archivos ya contenían UTF-8 válido; no fue necesaria una reconversión de texto.
- Se creó el entorno virtual `.venv`, excluido de Git.
- Se documentaron las dependencias en `requirements.txt` y las variables necesarias en `.env.example`.
- Se validó en modo de simulación que todas las dependencias declaradas tienen distribuciones compatibles con el Python local.
- Se verificó Python 3.14.6.
- Se verificó PostgreSQL 18.1 con su servicio activo. El ejecutable `psql` existe, aunque su carpeta no está incluida en el PATH local.
- Se añadieron README, inventario del prototipo y registro de pendientes frontend.
- `.gitignore` excluye secretos, entornos virtuales, facturas generadas y respaldos reales.
- No se crearon rutas Flask, modelos SQLAlchemy, tablas ni funcionalidades de fases posteriores.

## 9. Matriz resumida de cobertura

- **PostgreSQL relacional:** Fases 2 y 3.
- **PK, FK y normalización:** Fase 3.
- **CHECK, DEFAULT y UNIQUE:** Fases 3 y 12.
- **Triggers y procedimientos almacenados:** Fases 8 y 12.
- **Reportes mediante JOIN:** Fase 11.
- **Seguridad y respaldos:** Fase 12.
- **Jinja2 y frontend responsive:** Fases 2 y 5.
- **Mensajes flash y validaciones:** Fases 4 a 10.
- **POO y polimorfismo:** Fase 3.
- **Datos iniciales mediante `init_db.py`:** Fase 3.
- **Registro, login, perfil y roles:** Fase 4.
- **Catálogo, filtros, stock y recomendaciones:** Fase 5.
- **Carrito:** Fase 6.
- **Tarjeta y PIN por correo:** Fase 7.
- **Checkout, pedido pendiente y stock:** Fase 8.
- **PDF y notificaciones:** Fase 9.
- **CRUD y aprobación administrativa:** Fase 10.
- **Dashboard y rankings:** Fase 11.
- **Pruebas, documentación y Git:** Fases 1 y 13.

---

## Solicitud de aprobación

**¿Apruebas esta fase para proceder con la siguiente?**
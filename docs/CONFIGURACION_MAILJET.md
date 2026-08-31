# Configuración de Mailjet

New Records utiliza Mailjet mediante su retransmisión SMTP y Flask-Mail. No se
requiere instalar el SDK de Mailjet. Las credenciales se guardan exclusivamente
en el archivo local `.env`, que está excluido de Git.

## 1. Preparar la cuenta

1. Crear o ingresar a una cuenta de Mailjet.
2. Validar la dirección que se usará como remitente. Para un despliegue real se
   recomienda validar el dominio completo.
3. Configurar SPF y DKIM para ese dominio antes de enviar correos a clientes.
4. Abrir la administración de claves API y obtener una **API Key** y su
   correspondiente **Secret Key**. La clave secreta no debe compartirse ni
   incorporarse al repositorio.

## 2. Configurar el entorno local

Copiar `.env.example` como `.env` si todavía no existe y completar estas
variables:

```ini
MAIL_SERVER=in-v3.mailjet.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USE_SSL=0
MAIL_DEBUG=0
MAIL_USERNAME=API_KEY_DE_MAILJET
MAIL_PASSWORD=SECRET_KEY_DE_MAILJET
MAIL_DEFAULT_SENDER=correo-remitente-validado@dominio.com
```

- `MAIL_USERNAME` autentica la aplicación con la API Key de Mailjet; no es el
  correo de un cliente.
- `MAIL_PASSWORD` contiene la Secret Key de Mailjet.
- `MAIL_DEFAULT_SENDER` es la dirección que aparecerá como remitente y debe
  estar validada en Mailjet.
- Los destinatarios no se configuran en `.env`: la aplicación toma el correo de
  cada cliente registrado.

Después de guardar `.env`, reiniciar Flask para que cargue los nuevos valores.

## 3. Flujos que utilizan correo

Cada flujo utiliza una plantilla HTML responsiva con la identidad visual de New
Records y conserva una versión de texto plano para clientes de correo que no
puedan mostrar HTML.

- Registro de una tarjeta: el PIN temporal se envía a la dirección del cliente
  autenticado.
- Creación de un pedido: el cliente recibe la confirmación y el estado
  pendiente.
- Aprobación o rechazo: el cliente recibe el resultado de la revisión.

Actualmente el administrador consulta los pedidos nuevos desde su panel. No se
envía una notificación de correo al administrador.

## 4. Verificación manual

1. Reiniciar la aplicación.
2. Registrar o utilizar un cliente con una dirección de correo real.
3. Iniciar el registro de una tarjeta y comprobar la recepción del PIN.
4. Confirmar un pedido y revisar el correo de recepción.
5. Aprobar o rechazar ese pedido desde el panel administrativo y comprobar la
   notificación de cambio de estado.
6. Revisar en Mailjet las estadísticas del mensaje si no llega a la bandeja de
   entrada.

No deben utilizarse las cuentas de demostración con dominio `.local` para una
prueba real, porque no representan buzones entregables.

## 5. Controles básicos

- Nunca subir `.env`, API Keys ni Secret Keys a Git.
- Rotar inmediatamente una Secret Key que haya sido expuesta.
- Mantener TLS activado en el puerto 587.
- Mantener `MAIL_DEBUG=0` para que la autenticación SMTP no aparezca en los
  registros de desarrollo.
- Usar un remitente propio y autenticado con SPF/DKIM.
- Ejecutar las pruebas automatizadas con `MAIL_SUPPRESS_SEND=True` para evitar
  envíos accidentales.

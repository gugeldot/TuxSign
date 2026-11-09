# Política de seguridad

TuxSign maneja certificados y documentos firmados, así que nos tomamos los avisos de seguridad en serio.

## Qué versiones reciben arreglos

Solo la última versión publicada. Si usas una anterior, actualiza antes de avisar de un fallo.

## Cómo avisar de una vulnerabilidad

Por favor, **no abras una issue pública** con los detalles. Usa el aviso privado de GitHub:

1. Entra en la pestaña **Security** del repositorio.
2. Pulsa **Report a vulnerability**, o ve directamente a [este enlace](https://github.com/gugeldot/TuxSign/security/advisories/new).
3. Cuéntanos la versión (`tuxsign --version`), cómo reproducirlo y qué impacto crees que tiene.

TuxSign lo mantiene una sola persona en su tiempo libre, así que no podemos prometer plazos. Intentaremos contestar en una semana y publicar el arreglo lo antes posible, citándote si quieres.

## Qué cuenta como vulnerabilidad

Algunos ejemplos que nos interesan mucho:

- Fugas de la clave privada o de la contraseña del certificado.
- Un PDF manipulado que consiga ejecutar código, leer archivos o salir del proceso de render.
- Formas de saltarse la comprobación de integridad o el bloqueo de red.
- Firmas que parezcan válidas sin serlo, o que cubran menos de lo que muestran.
- Datos personales que acaben en el registro o en archivos que no deberían.

Quedan fuera los fallos que exigen que el atacante ya controle tu cuenta o pueda modificar los archivos de la aplicación, y los problemas de las librerías que usamos (avísales a ellas, y a nosotros si afecta a TuxSign).

## Más información

El diseño completo, con los controles, lo que cubren y sus límites, está en [docs/seguridad.md](docs/seguridad.md).

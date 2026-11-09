# Seguridad y privacidad en TuxSign

Este documento explica qué hace TuxSign para proteger tu certificado y tus documentos, qué normas tiene como referencia y, sobre todo, dónde están sus límites. Está alineado con ISO/IEC 27001 (Anexo A), ISO/IEC 27002:2022 y el RGPD. Ojo: una aplicación no "cumple ISO 27001" por sí sola, porque lo que se certifica es el sistema de gestión de una organización. Aquí solo describimos los controles técnicos que la aplicación aporta.

## Dos ideas que conviene tener claras

**La ofuscación no es seguridad.** Compilar el código a binario nativo (`./build.sh native`) dificulta leerlo, pero no evita ningún fallo. Es una capa extra y no sustituye a nada de lo demás.

**Los CVE llegan sobre todo por las dependencias.** Por eso las versiones están fijadas y `./build.sh audit` busca vulnerabilidades conocidas. En este proyecto ya encontró 39 avisos en Pillow 12.3.0, que se corrigieron subiendo a la 13.0.0. Un paquete "sin CVE" solo lo es hasta que se publica el siguiente, así que hay que repetir la auditoría en cada versión y de vez en cuando entre versiones.

## Qué amenazas tenemos en mente

| Qué proteger | Qué puede ir mal | Cómo se responde |
|---|---|---|
| La clave privada del `.p12` | Volcados de memoria, ptrace, fugas por logs, fuerza bruta | Controles 1 a 4, 7 y 8 |
| El PDF que abres (no es de fiar) | Un PDF hecho para explotar el lector, archivos enormes o especiales | Controles 6 y 18a |
| El código instalado | Que alguien lo modifique o plante módulos, o use variables de entorno | Controles 15, 16 y 18b |
| El PDF firmado | Escrituras a medias, sobrescribir el original | Escritura atómica y firma incremental |
| Tus datos personales | Retención excesiva, fugas por logs o telemetría | Apartado de privacidad |
| La cadena de suministro | Una dependencia vulnerable o comprometida | Control 12 |

## Controles técnicos

| # | Qué hace | Cómo | Referencia ISO 27002:2022 |
|---|---|---|---|
| 1 | Evita volcados de memoria | `RLIMIT_CORE=0` y `PR_SET_DUMPABLE=0` | 8.12, 8.24 |
| 2 | Impide escalar privilegios | `PR_SET_NO_NEW_PRIVS` | 8.2, 8.9 |
| 3 | No usa la red | Seccomp bloquea los sockets AF_INET, AF_INET6 y AF_PACKET (TCP y UDP), Landlock bloquea TCP y el Flatpak no tiene red. Los sockets Unix siguen permitidos para Wayland, X11 y D-Bus | 8.20, 8.22, 8.23 |
| 4 | Niega llamadas al sistema peligrosas | Seccomp: `ptrace`, `process_vm_*`, `mount`, `bpf`, `perf_event_open`, `kexec_*`, carga de módulos, `keyctl`, `reboot` y similares. Se comprueba la arquitectura y se bloquea la ABI x32 | 8.9, 8.19 |
| 5 | Permisos mínimos | `umask 077`, directorios 0700, archivos 0600, escritura atómica con `O_EXCL`, `fsync` y `rename` | 5.15, 8.3 |
| 6 | Valida lo que lee | Solo archivos regulares (con `fstat` sobre el descriptor), máximo 200 MiB para PDF y 1 MiB para `.p12`, 2000 páginas, cabecera `%PDF-`, sin PDF cifrados ni JavaScript | 8.26, 8.28 |
| 7 | Protege el uso de la clave | La contraseña no se escribe en disco ni en logs, hay retardo creciente tras tres fallos, el error es genérico y el `.p12` se descarta al desbloquear | 5.17, 8.5 |
| 8 | Bloquea por inactividad | A los 5 minutos sin actividad se descartan el certificado y la firma manuscrita | 8.1, 8.11 |
| 9 | Criptografía estándar | PAdES con CMS y SHA-256 mediante `cryptography` (OpenSSL) | 8.24 |
| 10 | Registro sin datos personales | Cadena de hashes que detecta manipulaciones, `flock`, `fsync` y una lista cerrada de eventos | 8.15, 8.17 |
| 11 | Errores que no filtran nada | Los errores usan claves de idioma, sin trazas ni nombres del titular. Los logs de pyHanko se silencian y lo que viene del PDF se escapa en la interfaz | 8.15, 8.28 |
| 12 | Cadena de suministro | Versiones fijadas, `pip-audit` y `bandit`, instalación en Flatpak con `--require-hashes` y sin red, y PyMuPDF 1.x sin dependencias de IA | 5.19 a 5.22, 8.8, 8.30 |
| 13 | Aislamiento del Flatpak | Sin `--filesystem`, los archivos llegan por el portal de escritorio. Solo Wayland, X11 y GPU | 8.20, 8.22 |
| 14 | Argumentos de Qt | `QApplication([argv0])`, así que no se aceptan opciones arbitrarias de Qt | 8.9 |
| 15 | Integridad del código | `MANIFEST.json` con el SHA-256 de cada archivo, firmado con Ed25519. Al arrancar se comprueba la firma y que no sobre, falte ni cambie nada, módulos plantados incluidos. Si falla, sale con código 70 | 8.32, 8.19 |
| 16 | Intérprete aislado | Se relanza con `-I -B`, ignorando `PYTHONPATH`, el directorio actual y el user-site. Solo se admiten rutas bajo `sys.prefix`, `/usr` o `/app` que otros no puedan escribir | 8.9, 8.19 |
| 17 | Compilado nativo | `./build.sh native` usa Nuitka para generar un `.so` sin `.py`, sin docstrings ni asserts y sin símbolos | 8.28 |
| 18a | Separación de privilegios | El render del PDF vive en otro proceso. Landlock le niega todo acceso a archivos, seccomp le niega sockets y `execve`, tiene tope de memoria, límites de píxeles y tamaño de página, y timeouts. El proceso principal, con la clave del certificado, no carga MuPDF | 8.22, 8.27 |
| 18b | Entorno saneado | Se eliminan `LD_PRELOAD`, `LD_*`, `QT_PLUGIN_PATH`, `PYTHON*` y similares. En Flatpak se conservan las rutas que fija el propio runtime | 8.9, 8.19 |
| 18c | Protecciones de memoria | El `.so` propio se compila con canario de pila, `-D_FORTIFY_SOURCE=3`, PIE, CET y RELRO completo. `build.sh` falla si `scripts/checksec.py` no lo confirma | 8.28, 8.29 |
| 19 | Versionado | SemVer con una única fuente (`tuxsign/__init__.py`), CHANGELOG, id de build y `tuxsign --version` | 8.32 |

## Privacidad y RGPD

| Principio | Qué hace TuxSign |
|---|---|
| Transparencia (arts. 5.1.a y 13) | Aviso de privacidad en cinco idiomas en el primer arranque, con aceptación expresa |
| Minimización (art. 5.1.c) | El registro solo guarda fecha, evento y una huella de 16 caracteres del documento. Nunca nombres, rutas, contraseñas ni contenido |
| Limitación del plazo (art. 5.1.e) | El registro se conserva entre 30 y 730 días, y se purga solo |
| Acceso y portabilidad (arts. 15 y 20) | "Exportar registro" lo saca en JSON Lines |
| Supresión (art. 17) | "Borrar todos mis datos" sobrescribe y elimina ajustes y registros |
| Privacidad por diseño (art. 25) | Sin red ni telemetría, registro opcional y firma manuscrita desactivada por defecto |
| Encargados y transferencias (arts. 28 y 44) | No hay: ningún dato sale del equipo |

El PDF firmado lleva el nombre del certificado y, si la activas, la imagen de la firma manuscrita. Solo se guarda la imagen y no la dinámica del trazo, que sí podría ser un dato biométrico. Si lo vas a usar de forma masiva en una organización, conviene documentar una evaluación de impacto (art. 35) y el registro de actividades (art. 30).

## Límites y riesgo que queda

Queremos ser claros con lo que TuxSign no consigue.

- **La contraseña en memoria.** Python no permite borrar de forma fiable el texto que guarda Qt ni los `bytes` que se pasan a `cryptography`. Se reduce el tiempo de exposición, pero la clave descifrada vive en memoria mientras el certificado esté desbloqueado. Para claves de mucho valor es mejor un token o un HSM (PKCS#11), que TuxSign aún no soporta.
- **La integridad no es magia.** Un atacante que pueda escribir en el paquete podría sustituir también la clave pública incrustada. La protección real es que el paquete sea de solo lectura, como `/app` en Flatpak, o que se instale como administrador. La clave de firma de las releases debe custodiarse y respaldarse fuera del repositorio.
- **El lector de PDF.** Los wheels de PyPI de PyMuPDF y Pillow no traen canario de pila ni RELRO completo, a diferencia de Qt, lxml y cryptography. Por eso MuPDF corre aislado (control 18a). Un exploit quedaría confinado sin archivos, red ni `exec`, aunque seguiría pudiendo leer el PDF que recibe y devolver píxeles manipulados. Pillow solo procesa la imagen de firma que genera la propia aplicación.
- **El filtro del lector es una lista de bloqueo.** Reduce la superficie de llamadas al sistema, pero no la elimina. Una lista de permitidos exigiría revisarla con cada versión de Python o MuPDF.
- **El compilado nativo.** Se puede desensamblar y solo sube el coste de la ingeniería inversa. Nuitka y PySide6 no funcionan bien juntos con Python 3.14 (da un `SystemError` en `connect()`), así que `build.sh native` pide Python 3.13 o anterior. Está probado con 3.12.
- **Seccomp y Landlock dependen del kernel.** Landlock para TCP necesita 6.7 o superior. Si algo no está disponible, se omite sin fallar. Efecto secundario conocido: `PR_SET_DUMPABLE=0` impide que el portal de escritorio registre el id de la aplicación (aparece un aviso en consola), aunque el selector de archivos sigue funcionando. Un `DISPLAY` de X11 por TCP, como el de `ssh -X`, no funcionará.
- **PAdES-B-B.** Sin sello de tiempo ni datos de validación a largo plazo, porque no hay red. La fecha visible es la del reloj local.
- **"Ver firmas".** Comprueba la integridad de la firma, no si confías en quien emitió el certificado.
- **Borrado.** Sobrescribir un archivo no garantiza que desaparezca en un SSD o en un sistema de archivos con copia en escritura. Usa cifrado de disco.
- **Licencias.** PyMuPDF es AGPL-3.0, y eso afecta a quien redistribuya paquetes que lo incluyan.

## Mantenerlo al día

En cada versión, y de vez en cuando entre versiones: `./build.sh audit`, actualizar `requirements.txt`, pasar `./build.sh test`, subir la versión con `./build.sh bump patch` y publicar. Conviene seguir los avisos de Qt y PySide6, PyMuPDF (MuPDF), pyHanko, cryptography y Pillow.

Lo que le toca a quien despliega TuxSign en una organización queda fuera de la aplicación: la política de claves criptográficas (A.8.24), las altas y bajas de certificados (A.5.16 y A.5.18), el cifrado de disco, las copias de seguridad (A.8.13), la formación (A.6.3) y la gestión de incidentes (A.5.24 a A.5.26).

## Cómo verificarlo

```bash
./build.sh test     # 15 tests: firma, verificación, manipulación, validación, seccomp, integridad, idiomas y aislamiento del render
./build.sh audit    # pip-audit y bandit
./build.sh checksec # protecciones de memoria de los binarios
```

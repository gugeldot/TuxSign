# Cómo contribuir

Gracias por querer echar una mano. TuxSign es un proyecto pequeño y cualquier ayuda cuenta: un fallo bien descrito, una traducción, una mejora de la interfaz o un parche.

## Preparar el entorno

```bash
git clone https://github.com/gugeldot/TuxSign.git
cd TuxSign
./build.sh test      # crea .venv, instala lo necesario y pasa los tests
./build.sh run       # abre la aplicación
```

Necesitas Linux con Wayland o X11 y Python 3.10 o superior.

## Antes de abrir un PR

1. Pasa `./build.sh test` y `./build.sh audit`. Si añades algo que toque seguridad, añade también un test.
2. Si tocas la interfaz, ejecuta `python scripts/make_screenshots.py` para comprobar que sigue funcionando y regenerar las capturas.
3. Mantén los cambios pequeños y explica el motivo en la descripción. Un PR que hace una sola cosa se revisa mucho más rápido.
4. No subas claves, certificados ni documentos reales. Los tests generan sus propios certificados de prueba.

## Reglas de seguridad que no conviene saltarse

- **El proceso principal no carga MuPDF.** Todo lo que toque PDF para dibujar va por `render_worker.py`.
- **Nada de red.** Ni peticiones, ni telemetría, ni comprobar actualizaciones.
- **El registro no guarda datos personales.** Nombres, rutas y contraseñas no entran en él.
- **Los errores no cuentan detalles internos.** Usa claves de idioma, no el texto de la excepción.
- **Las dependencias se fijan** en `requirements.txt` y se auditan con `./build.sh audit`.

## Traducciones

Los textos están en `tuxsign/i18n.py`. Para añadir un idioma copia el bloque de `en`, tradúcelo y regístralo en `LANGUAGES`. El test `test_i18n_complete` comprueba que no falte ninguna clave.

## Estilo de los textos

Para que todo suene igual, en la documentación, la web y los textos de la interfaz seguimos unas reglas sencillas:

- Escribe como hablarías, con frases cortas y sin jerga innecesaria.
- Usa comillas rectas (`"así"`), nunca comillas angulares ni tipográficas.
- No uses guiones largos. Sirven mejor los dos puntos, una coma o un punto.
- No uses punto y coma en prosa. Parte la frase en dos.
- En español, cuida las tildes y los signos de apertura (¿ y ¡).

El script `python scripts/check_text_style.py` revisa estas reglas y se ejecuta en la integración continua.

## Versiones

Seguimos [SemVer](https://semver.org/lang/es/). `./build.sh bump <major|minor|patch>` sube la versión y prepara el CHANGELOG.

## Licencia

Al contribuir aceptas que tu aportación se publique bajo la licencia [MIT](LICENSE) del proyecto.

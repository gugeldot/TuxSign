# Registro de cambios

Sigue el formato de [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado [SemVer](https://semver.org/lang/es/).

## [Sin publicar]

## [1.2.0] - 2026-11-09

### Novedades
- El PDF se dibuja ahora en un proceso aparte, sin acceso a archivos, red ni programas. El proceso principal, que guarda tu certificado, ya no carga MuPDF.
- Botón con una X junto a "Abrir PDF" para descartar el documento y volver a la pantalla de inicio.
- El diálogo "Acerca de" ya no enseña el estado del endurecimiento del proceso.
- El binario nativo se compila con las protecciones de memoria activadas y `./build.sh checksec` las comprueba.
- Paquete Flatpak compilado y verificado dentro de su entorno aislado.

### Seguridad
- Los nombres de archivo se muestran como texto plano, para que uno con código HTML no se interprete.
- Un `settings.json` estropeado ya no impide arrancar, y se ignoran las rutas XDG relativas.
- El registro de auditoría se escribe sin releer el archivo entero cada vez.
- El texto del sello se limpia de saltos de línea y caracteres de control.
- Se limpia el entorno al relanzar el intérprete (`LD_PRELOAD`, `QT_PLUGIN_PATH`, `PYTHON*` y similares).
- Pillow sube a 13.0.0, que corrige 39 avisos de seguridad.

## [1.1.0] - 2026-11-09

### Novedades
- La aplicación pasa a llamarse **TuxSign**.
- Interfaz en inglés (por defecto), español, francés, alemán y portugués.
- El bloque "Firmado digitalmente por" se puede mover y redimensionar. La firma manuscrita es opcional y viene desactivada.
- Filtro seccomp, intérprete aislado y comprobación de integridad con firma Ed25519.
- Compilación nativa con Nuitka, versionado con `./build.sh bump` y auditoría con `./build.sh audit`.

### Cambios
- Los errores ya no dependen del idioma y se silencian los logs de las librerías.

## [1.0.0] - 2026-11-09

- Primera versión: firma PAdES con `.p12`, visor de PDF, lienzo de firma, registro de auditoría con cadena de hashes y funciones de privacidad.

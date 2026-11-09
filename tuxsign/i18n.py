"""Internacionalización ligera (sin ficheros externos ni carga dinámica de código).

Idioma por defecto: inglés. Las claves ausentes caen a inglés. Añadir un idioma = añadir un dict
con las mismas claves (tests/test_core.py::test_i18n_complete lo verifica).
"""
from __future__ import annotations

DEFAULT = "en"
LANGUAGES = [("en", "English"), ("es", "Español"), ("fr", "Français"), ("de", "Deutsch"), ("pt", "Português")]
_current = DEFAULT


def set_language(code: str) -> str:
    global _current
    _current = code if code in S else DEFAULT
    return _current


def current() -> str:
    return _current


def tr(key: str, **kw) -> str:
    text = S.get(_current, {}).get(key) or S[DEFAULT].get(key) or key
    try:
        return text.format(**kw) if kw else text
    except (KeyError, IndexError, ValueError):
        return text


_NOTICE = {
    "en": """<h3>Your privacy</h3>
<p>TuxSign works <b>entirely on your computer</b>. It has no telemetry, makes no network connections and sends nothing to anyone.</p>
<p><b>What it handles:</b></p><ul>
<li>Your PDF and your .p12 certificate stay in memory while you use the app.</li>
<li>Your handwritten signature, if you add one, is kept in memory and embedded in the signed PDF. It is never saved on its own.</li>
<li>An optional local activity log with the date, the type of event and a short fingerprint of the document. It never contains names, paths, passwords or content.</li></ul>
<p><b>Why:</b> to do what you ask (sign a document) and to keep the app secure (the log). The log is purged automatically after the period you choose.</p>
<p><b>Your rights:</b> you can see, export and delete everything under "Privacy and data".</p>
<p>One thing to keep in mind: a signed PDF carries the certificate holder's name and, if you used one, the signature image. Whoever shares that file is responsible for who receives it.</p>""",
    "es": """<h3>Tu privacidad</h3>
<p>TuxSign funciona <b>por completo en tu equipo</b>. No tiene telemetría, no hace conexiones de red y no envía nada a nadie.</p>
<p><b>Qué trata:</b></p><ul>
<li>Tu PDF y tu certificado .p12 se quedan en memoria mientras usas la aplicación.</li>
<li>Tu firma manuscrita, si la añades, se queda en memoria y se incrusta en el PDF firmado. Nunca se guarda por separado.</li>
<li>Un registro de actividad local opcional con la fecha, el tipo de evento y una huella corta del documento. Nunca contiene nombres, rutas, contraseñas ni contenido.</li></ul>
<p><b>Para qué:</b> para hacer lo que le pides (firmar un documento) y para mantener la aplicación segura (el registro). El registro se borra solo pasado el plazo que elijas.</p>
<p><b>Tus derechos:</b> puedes ver, exportar y borrar todo desde "Privacidad y datos".</p>
<p>Algo que conviene tener presente: un PDF firmado lleva el nombre de quien posee el certificado y, si la usaste, la imagen de la firma. Quien comparte ese archivo es responsable de quién lo recibe.</p>""",
    "fr": """<h3>Votre vie privée</h3>
<p>TuxSign fonctionne <b>entièrement sur votre ordinateur</b>. Il n'a aucune télémétrie, n'établit aucune connexion réseau et n'envoie rien à personne.</p>
<p><b>Ce qu'il traite :</b></p><ul>
<li>Votre PDF et votre certificat .p12 restent en mémoire pendant que vous utilisez l'application.</li>
<li>Votre signature manuscrite, si vous en ajoutez une, reste en mémoire et s'intègre au PDF signé. Elle n'est jamais enregistrée à part.</li>
<li>Un journal d'activité local facultatif avec la date, le type d'événement et une courte empreinte du document. Jamais de noms, de chemins, de mots de passe ni de contenu.</li></ul>
<p><b>Pourquoi :</b> pour faire ce que vous demandez (signer un document) et pour garder l'application sûre (le journal). Le journal est purgé automatiquement après la durée que vous choisissez.</p>
<p><b>Vos droits :</b> vous pouvez tout consulter, exporter et supprimer dans "Confidentialité et données".</p>
<p>À garder en tête : un PDF signé contient le nom du titulaire du certificat et, le cas échéant, l'image de la signature. Celui qui partage ce fichier est responsable de qui le reçoit.</p>""",
    "de": """<h3>Dein Datenschutz</h3>
<p>TuxSign arbeitet <b>komplett auf deinem Computer</b>. Es gibt keine Telemetrie, keine Netzwerkverbindungen und nichts wird an Dritte gesendet.</p>
<p><b>Was verarbeitet wird:</b></p><ul>
<li>Dein PDF und dein .p12-Zertifikat bleiben nur im Arbeitsspeicher, solange du die App nutzt.</li>
<li>Deine handschriftliche Unterschrift, falls du eine hinzufügst, bleibt im Arbeitsspeicher und wird in das signierte PDF eingebettet. Sie wird nie separat gespeichert.</li>
<li>Ein optionales lokales Aktivitätsprotokoll mit Datum, Ereignistyp und einem kurzen Fingerabdruck des Dokuments. Es enthält nie Namen, Pfade, Passwörter oder Inhalte.</li></ul>
<p><b>Wozu:</b> um zu tun, was du verlangst (ein Dokument signieren), und um die App sicher zu halten (das Protokoll). Das Protokoll wird nach der von dir gewählten Frist automatisch gelöscht.</p>
<p><b>Deine Rechte:</b> Unter "Datenschutz und Daten" kannst du alles einsehen, exportieren und löschen.</p>
<p>Gut zu wissen: Ein signiertes PDF enthält den Namen des Zertifikatsinhabers und, falls verwendet, das Unterschriftsbild. Wer die Datei weitergibt, ist dafür verantwortlich, wer sie erhält.</p>""",
    "pt": """<h3>A sua privacidade</h3>
<p>O TuxSign funciona <b>inteiramente no seu computador</b>. Não tem telemetria, não faz ligações de rede e não envia nada a ninguém.</p>
<p><b>O que trata:</b></p><ul>
<li>O seu PDF e o seu certificado .p12 ficam apenas em memória enquanto usa a aplicação.</li>
<li>A sua assinatura manuscrita, se a adicionar, fica em memória e é incorporada no PDF assinado. Nunca é guardada à parte.</li>
<li>Um registo de atividade local opcional com a data, o tipo de evento e uma impressão digital curta do documento. Nunca contém nomes, caminhos, palavras-passe nem conteúdo.</li></ul>
<p><b>Porquê:</b> para fazer o que pede (assinar um documento) e para manter a aplicação segura (o registo). O registo é apagado automaticamente após o prazo que escolher.</p>
<p><b>Os seus direitos:</b> pode ver, exportar e apagar tudo em "Privacidade e dados".</p>
<p>Para ter em conta: um PDF assinado inclui o nome do titular do certificado e, se a usou, a imagem da assinatura. Quem partilha esse ficheiro é responsável por quem o recebe.</p>""",
}

S: dict[str, dict[str, str]] = {
    "en": {
        "err_sandbox_file": "TuxSign runs in a sandbox and can't see that file. Use Open PDF instead, or give it access to the folder.",
        "pages_many": "{n} pages",
        "pages_one": "1 page",
        "err_render": "Couldn't display this PDF.",
        "tip_close_doc": "Close document",
        "no_doc": "No document", "btn_open": "Open PDF", "tip_sigs": "See the signatures in this document",
        "tip_privacy": "Privacy & data", "tip_theme": "Toggle theme", "tip_lang": "Language", "tip_about": "About TuxSign",
        "drop_title": "Drop a PDF here", "drop_sub": "or click to pick one",
        "drop_foot": "Everything stays on your computer. No network, no telemetry.",
        "tip_prev": "Previous page", "tip_next": "Next page", "tip_zoom_out": "Zoom out", "tip_zoom_in": "Zoom in", "tip_fit": "Fit to width",
        
        "c1_title": "Your certificate (.p12 / .pfx)", "c1_none": "No certificate chosen yet", "c1_pick": "Choose certificate",
        "c1_pw": "Certificate password", "c1_unlock": "Unlock", "c1_lock": "Lock certificate",
        "c1_issuer": "Issued by {issuer}", "c1_valid": "Valid until {date}", "c1_expired": "Expired on {date}",
        "c2_title": "Signature block", "c2_desc": "Shows who signed and when. Drag it where you want it and pull the corner to resize.",
        "sw_hand": "Add a handwritten signature", "pad_hint": "Draw with your mouse, trackpad or pen", "pad_line": "✕  Sign on the line",
        "tip_undo": "Undo stroke", "tip_clear": "Clear signature",
        "btn_place": "Place signature block", "btn_replace": "Update signature block",
        "stamp_signed_by": "Digitally signed by:", "stamp_placeholder": "Your name",
        "c3_title": "Sign and save", "reason_ph": "Reason (optional), e.g. Approval", "btn_sign": "Sign document", "signing": "Signing…",
        "status_missing": "Still missing: {items}.", "status_ready": "Ready. Check the position and sign.",
        "miss_pdf": "open a PDF", "miss_cert": "unlock your certificate", "miss_stamp": "place the signature block",
        "miss_ink": "draw your signature",
       
        "toast_pick_p12": "Choose a .p12 certificate first.", "toast_wait": "Too many attempts. Try again in {s} s.",
        "toast_unlocked": "Certificate unlocked.", "toast_expired": "This certificate has expired, so the signature won't be valid.",
        "toast_idle": "Certificate locked after 5 minutes without activity.", "toast_open_first": "Open a PDF first.",
        "toast_existing": "This document already has {n} signature(s). Use the eye icon to see them.",
        "toast_place_page": "Drop the block onto a page.", "toast_overwrite": "You can't overwrite the original document.",
        "toast_save_fail": "Couldn't save the file.", "toast_signed": "Signed: {name}",
        "err_open": "Couldn't open that file.", "err_not_regular": "Only regular files are accepted.",
        "err_size": "That file is empty or too large (max. {mb} MiB).", "err_format": "That doesn't look like a valid file.",
        "err_pdf_invalid": "This PDF is damaged or not valid.", "err_pdf_encrypted": "Encrypted PDFs aren't supported yet.",
        "err_pdf_pages": "This PDF has too many pages.", "err_cert": "Couldn't open the certificate. Check the file and the password.",
        "err_cert_nokey": "That file has no private key or certificate.",
        "err_sign": "Couldn't sign the document ({code}).", "err_unexpected": "Something went wrong while signing.",
        "dlg_open_pdf": "Open PDF", "filter_pdf": "PDF documents (*.pdf)", "dlg_pick_p12": "Choose certificate",
        "filter_p12": "Certificates (*.p12 *.pfx)", "dlg_save": "Save signed document", "dlg_export": "Export log",
        "consent_welcome": "Welcome to TuxSign", "consent_audit": "Keep a local activity log with no personal data (recommended)",
        "consent_ack": "I have read the privacy notice", "btn_exit": "Exit", "btn_continue": "Continue",
        "priv_title": "Privacy and data", "priv_audit_on": "Keep a local activity log", "priv_retention": "Keep the log for (days):",
        "priv_verify": "Check log integrity", "priv_export": "Export log", "priv_erase": "Delete all my data", "priv_save": "Save and close",
        "priv_chain_ok": "The log is intact ({n} entries)", "priv_chain_bad": "The log has been tampered with ({n} entries)",
        "priv_exported": "Log exported.", "priv_erase_title": "Delete data",
        "priv_erase_text": "This permanently deletes your settings, consent and activity log.\nContinue?",
        "priv_erased": "{n} files deleted. TuxSign will close.",
        "ver_title": "Signatures in this document", "ver_none": "This document has no digital signatures.",
        "ver_ok": "Signature intact", "ver_modified": "Document was modified", "ver_later": " · changed after signing",
        "ver_trust": "Whether you trust the certificate issuer is something to check separately.", "btn_close": "Close",
        "about_title": "About TuxSign", "about_version": "Version", "about_build": "Build",
        "about_integrity": "Integrity check", "integ_ok": "Verified", "integ_dev": "Development build (unsigned)",
        "integ_fail": "Failed", "btn_yes": "Yes", "btn_no": "No",
        "integrity_abort": "TuxSign's files have been changed, so it won't start. Reinstall it from a source you trust.",
        "privacy_notice": _NOTICE["en"],
    },
    "es": {
        "err_sandbox_file": "TuxSign se ejecuta aislado y no puede ver ese archivo. Usa Abrir PDF, o dale acceso a la carpeta.",
        "pages_many": "{n} páginas",
        "pages_one": "1 página",
        "err_render": "No se ha podido mostrar este PDF.",
        "tip_close_doc": "Cerrar documento",
        "no_doc": "Ningún documento", "btn_open": "Abrir PDF", "tip_sigs": "Ver las firmas del documento",
        "tip_privacy": "Privacidad y datos", "tip_theme": "Cambiar tema", "tip_lang": "Idioma", "tip_about": "Acerca de TuxSign",
        "drop_title": "Suelta aquí tu PDF", "drop_sub": "o haz clic para elegir uno",
        "drop_foot": "Todo se queda en tu equipo. Sin red y sin telemetría.",
        "tip_prev": "Página anterior", "tip_next": "Página siguiente", "tip_zoom_out": "Alejar", "tip_zoom_in": "Acercar", "tip_fit": "Ajustar al ancho",
        
        "c1_title": "Tu certificado (.p12 / .pfx)", "c1_none": "Aún no has elegido certificado", "c1_pick": "Elegir certificado",
        "c1_pw": "Contraseña del certificado", "c1_unlock": "Desbloquear", "c1_lock": "Bloquear certificado",
        "c1_issuer": "Emitido por {issuer}", "c1_valid": "Válido hasta {date}", "c1_expired": "Caducó el {date}",
        "c2_title": "Bloque de firma", "c2_desc": "Muestra quién ha firmado y cuándo. Arrástralo donde quieras y tira de la esquina para cambiarle el tamaño.",
        "sw_hand": "Añadir firma manuscrita", "pad_hint": "Dibuja con el ratón, el trackpad o un lápiz", "pad_line": "✕  Firma sobre la línea",
        "tip_undo": "Deshacer trazo", "tip_clear": "Borrar firma",
        "btn_place": "Colocar bloque de firma", "btn_replace": "Actualizar bloque de firma",
        "stamp_signed_by": "Firmado digitalmente por:", "stamp_placeholder": "Tu nombre",
        "c3_title": "Firmar y guardar", "reason_ph": "Motivo (opcional), p. ej. Aprobación", "btn_sign": "Firmar documento", "signing": "Firmando…",
        "status_missing": "Todavía falta: {items}.", "status_ready": "Todo listo. Revisa la posición y firma.",
        "miss_pdf": "abrir un PDF", "miss_cert": "desbloquear tu certificado", "miss_stamp": "colocar el bloque de firma",
        "miss_ink": "dibujar tu firma",
       
        "toast_pick_p12": "Primero elige un certificado .p12.", "toast_wait": "Demasiados intentos. Prueba de nuevo en {s} s.",
        "toast_unlocked": "Certificado desbloqueado.", "toast_expired": "El certificado ha caducado, así que la firma no será válida.",
        "toast_idle": "Certificado bloqueado tras 5 minutos sin actividad.", "toast_open_first": "Abre primero un PDF.",
        "toast_existing": "Este documento ya tiene {n} firma(s). Pulsa el icono del ojo para verlas.",
        "toast_place_page": "Coloca el bloque sobre una página.", "toast_overwrite": "No se puede sobrescribir el documento original.",
        "toast_save_fail": "No se ha podido guardar el archivo.", "toast_signed": "Firmado: {name}",
        "err_open": "No se ha podido abrir ese archivo.", "err_not_regular": "Solo se admiten archivos normales.",
        "err_size": "El archivo está vacío o es demasiado grande (máx. {mb} MiB).", "err_format": "Ese archivo no tiene un formato válido.",
        "err_pdf_invalid": "Este PDF está dañado o no es válido.", "err_pdf_encrypted": "Todavía no se admiten PDF cifrados.",
        "err_pdf_pages": "Este PDF tiene demasiadas páginas.", "err_cert": "No se ha podido abrir el certificado. Revisa el archivo y la contraseña.",
        "err_cert_nokey": "Ese archivo no contiene clave privada ni certificado.",
        "err_sign": "No se ha podido firmar el documento ({code}).", "err_unexpected": "Algo ha ido mal al firmar.",
        "dlg_open_pdf": "Abrir PDF", "filter_pdf": "Documentos PDF (*.pdf)", "dlg_pick_p12": "Elegir certificado",
        "filter_p12": "Certificados (*.p12 *.pfx)", "dlg_save": "Guardar documento firmado", "dlg_export": "Exportar registro",
        "consent_welcome": "Te damos la bienvenida a TuxSign", "consent_audit": "Guardar un registro de actividad local, sin datos personales (recomendado)",
        "consent_ack": "He leído el aviso de privacidad", "btn_exit": "Salir", "btn_continue": "Continuar",
        "priv_title": "Privacidad y datos", "priv_audit_on": "Guardar registro de actividad local", "priv_retention": "Conservar el registro (días):",
        "priv_verify": "Comprobar integridad", "priv_export": "Exportar registro", "priv_erase": "Borrar todos mis datos", "priv_save": "Guardar y cerrar",
        "priv_chain_ok": "El registro está intacto ({n} entradas)", "priv_chain_bad": "El registro ha sido manipulado ({n} entradas)",
        "priv_exported": "Registro exportado.", "priv_erase_title": "Borrar datos",
        "priv_erase_text": "Se borrarán para siempre tus ajustes, tu consentimiento y el registro de actividad.\n¿Quieres continuar?",
        "priv_erased": "Se han borrado {n} archivos. TuxSign se cerrará.",
        "ver_title": "Firmas del documento", "ver_none": "Este documento no tiene firmas digitales.",
        "ver_ok": "Firma íntegra", "ver_modified": "El documento se modificó", "ver_later": " · cambios posteriores a la firma",
        "ver_trust": "Si el emisor del certificado es de fiar es algo que debes comprobar aparte.", "btn_close": "Cerrar",
        "about_title": "Acerca de TuxSign", "about_version": "Versión", "about_build": "Compilación",
        "about_integrity": "Comprobación de integridad", "integ_ok": "Verificada", "integ_dev": "Compilación de desarrollo (sin firmar)",
        "integ_fail": "Fallida", "btn_yes": "Sí", "btn_no": "No",
        "integrity_abort": "Los archivos de TuxSign han cambiado, así que no se iniciará. Vuelve a instalarlo desde una fuente de confianza.",
        "privacy_notice": _NOTICE["es"],
    },
    "fr": {
        "err_sandbox_file": "TuxSign s'exécute isolé et ne peut pas voir ce fichier. Utilisez Ouvrir un PDF, ou donnez-lui accès au dossier.",
        "pages_many": "{n} pages",
        "pages_one": "1 page",
        "err_render": "Le PDF n'a pas pu être affiché.",
        "tip_close_doc": "Fermer le document",
        "no_doc": "Aucun document", "btn_open": "Ouvrir un PDF", "tip_sigs": "Voir les signatures existantes",
        "tip_privacy": "Confidentialité et données", "tip_theme": "Changer de thème", "tip_lang": "Langue", "tip_about": "À propos de TuxSign",
        "drop_title": "Déposez votre PDF ici", "drop_sub": "ou cliquez pour choisir un document",
        "drop_foot": "Tout est traité sur votre appareil · aucun réseau · aucune télémétrie",
        "tip_prev": "Page précédente", "tip_next": "Page suivante", "tip_zoom_out": "Réduire", "tip_zoom_in": "Agrandir", "tip_fit": "Ajuster à la largeur",
        
        "c1_title": "Certificat numérique (.p12 / .pfx)", "c1_none": "Aucun certificat sélectionné", "c1_pick": "Choisir un certificat",
        "c1_pw": "Mot de passe du certificat", "c1_unlock": "Déverrouiller", "c1_lock": "Verrouiller le certificat",
        "c1_issuer": "Émetteur : {issuer}", "c1_valid": "Valide jusqu'au {date}", "c1_expired": "EXPIRÉ le {date}",
        "c2_title": "Bloc de signature", "c2_desc": "Indique qui a signé et quand. Faites-le glisser pour le déplacer et tirez la poignée d'angle pour le redimensionner.",
        "sw_hand": "Ajouter une signature manuscrite", "pad_hint": "Dessinez à la souris, au pavé tactile ou au stylet", "pad_line": "✕  Signez sur la ligne",
        "tip_undo": "Annuler le trait", "tip_clear": "Effacer la signature",
        "btn_place": "Placer le bloc de signature", "btn_replace": "Mettre à jour le bloc de signature",
        "stamp_signed_by": "Signé numériquement par :", "stamp_placeholder": "Votre nom",
        "c3_title": "Signer et enregistrer", "reason_ph": "Motif (facultatif) · ex. Approbation", "btn_sign": "Signer le document", "signing": "Signature…",
        "status_missing": "Manquant : {items}.", "status_ready": "Tout est prêt. Vérifiez la position et signez.",
        "miss_pdf": "ouvrez un PDF", "miss_cert": "déverrouillez votre certificat", "miss_stamp": "placez le bloc de signature sur le document",
        "miss_ink": "dessinez votre signature manuscrite",
       
        "toast_pick_p12": "Choisissez d'abord un certificat .p12.", "toast_wait": "Trop de tentatives. Attendez {s} s.",
        "toast_unlocked": "Certificat déverrouillé.", "toast_expired": "Le certificat a expiré : la signature ne sera pas valide.",
        "toast_idle": "Certificat verrouillé après 5 minutes d'inactivité.", "toast_open_first": "Ouvrez d'abord un PDF.",
        "toast_existing": "Ce document contient déjà {n} signature(s). Utilisez l'icône en forme d'œil pour les voir.",
        "toast_place_page": "Placez le bloc sur une page.", "toast_overwrite": "Le document d'origine ne peut pas être écrasé.",
        "toast_save_fail": "Le fichier n'a pas pu être enregistré.", "toast_signed": "Document signé : {name}",
        "err_open": "Le fichier ne peut pas être ouvert.", "err_not_regular": "Seuls les fichiers ordinaires sont acceptés.",
        "err_size": "Taille non autorisée (max. {mb} Mio).", "err_format": "Le format du fichier n'est pas valide.",
        "err_pdf_invalid": "Le PDF est endommagé ou invalide.", "err_pdf_encrypted": "Les PDF chiffrés ne sont pas pris en charge.",
        "err_pdf_pages": "Nombre de pages non autorisé.", "err_cert": "Impossible d'ouvrir le certificat. Vérifiez le fichier et le mot de passe.",
        "err_cert_nokey": "Le fichier ne contient pas de clé privée ni de certificat.",
        "err_sign": "Le document n'a pas pu être signé ({code}).", "err_unexpected": "Erreur inattendue lors de la signature.",
        "dlg_open_pdf": "Ouvrir un PDF", "filter_pdf": "Documents PDF (*.pdf)", "dlg_pick_p12": "Choisir un certificat",
        "filter_p12": "Certificats (*.p12 *.pfx)", "dlg_save": "Enregistrer le document signé", "dlg_export": "Exporter le journal",
        "consent_welcome": "Bienvenue dans TuxSign", "consent_audit": "Activer le journal d'audit local sans données personnelles (recommandé)",
        "consent_ack": "J'ai lu et compris l'avis de confidentialité", "btn_exit": "Quitter", "btn_continue": "Continuer",
        "priv_title": "Confidentialité et données", "priv_audit_on": "Journal d'audit local activé", "priv_retention": "Conserver le journal (jours) :",
        "priv_verify": "Vérifier l'intégrité", "priv_export": "Exporter le journal", "priv_erase": "Effacer toutes mes données", "priv_save": "Enregistrer et fermer",
        "priv_chain_ok": "✔ Journal intact ({n} entrées)", "priv_chain_bad": "✖ Chaîne du journal altérée ! ({n} entrées)",
        "priv_exported": "Journal exporté.", "priv_erase_title": "Effacement des données (art. 17)",
        "priv_erase_text": "Les réglages, le consentement et le journal d'audit seront supprimés définitivement.\nContinuer ?",
        "priv_erased": "{n} fichiers supprimés. L'application va se fermer.",
        "ver_title": "Signatures du document", "ver_none": "Ce document ne contient aucune signature numérique.",
        "ver_ok": "Intégrité correcte", "ver_modified": "Document modifié", "ver_later": " · modifications postérieures à cette signature",
        "ver_trust": "La confiance dans l'émetteur du certificat doit être évaluée séparément.", "btn_close": "Fermer",
        "about_title": "À propos de TuxSign", "about_version": "Version", "about_build": "Build",
        "about_integrity": "Contrôle d'intégrité", "integ_ok": "Vérifié", "integ_dev": "Build de développement (non signé)",
        "integ_fail": "ÉCHEC", "btn_yes": "Oui", "btn_no": "Non",
        "integrity_abort": "Les fichiers de TuxSign ont été modifiés, donc l'application ne démarre pas. Réinstallez-la depuis une source de confiance.",
        "privacy_notice": _NOTICE["fr"],
    },
    "de": {
        "err_sandbox_file": "TuxSign läuft isoliert und kann diese Datei nicht sehen. Nutze PDF öffnen oder gib dem Programm Zugriff auf den Ordner.",
        "pages_many": "{n} Seiten",
        "pages_one": "1 Seite",
        "err_render": "Das PDF konnte nicht dargestellt werden.",
        "tip_close_doc": "Dokument schließen",
        "no_doc": "Kein Dokument", "btn_open": "PDF öffnen", "tip_sigs": "Vorhandene Signaturen anzeigen",
        "tip_privacy": "Datenschutz & Daten", "tip_theme": "Design wechseln", "tip_lang": "Sprache", "tip_about": "Über TuxSign",
        "drop_title": "PDF hier ablegen", "drop_sub": "oder klicken, um ein Dokument zu wählen",
        "drop_foot": "Alles wird auf Ihrem Gerät verarbeitet · kein Netzwerk · keine Telemetrie",
        "tip_prev": "Vorherige Seite", "tip_next": "Nächste Seite", "tip_zoom_out": "Verkleinern", "tip_zoom_in": "Vergrößern", "tip_fit": "Breite anpassen",
        
        "c1_title": "Digitales Zertifikat (.p12 / .pfx)", "c1_none": "Kein Zertifikat ausgewählt", "c1_pick": "Zertifikat wählen",
        "c1_pw": "Zertifikatspasswort", "c1_unlock": "Entsperren", "c1_lock": "Zertifikat sperren",
        "c1_issuer": "Aussteller: {issuer}", "c1_valid": "Gültig bis {date}", "c1_expired": "ABGELAUFEN am {date}",
        "c2_title": "Signaturblock", "c2_desc": "Zeigt, wer wann signiert hat. Zum Verschieben ziehen, am Eckgriff die Größe ändern.",
        "sw_hand": "Handschriftliche Unterschrift hinzufügen", "pad_hint": "Mit Maus, Touchpad oder Stift zeichnen", "pad_line": "✕  Auf der Linie unterschreiben",
        "tip_undo": "Strich rückgängig", "tip_clear": "Unterschrift löschen",
        "btn_place": "Signaturblock platzieren", "btn_replace": "Signaturblock aktualisieren",
        "stamp_signed_by": "Digital signiert von:", "stamp_placeholder": "Ihr Name",
        "c3_title": "Signieren & speichern", "reason_ph": "Grund (optional) · z. B. Freigabe", "btn_sign": "Dokument signieren", "signing": "Signiere…",
        "status_missing": "Es fehlt: {items}.", "status_ready": "Alles bereit. Position prüfen und signieren.",
        "miss_pdf": "ein PDF öffnen", "miss_cert": "Zertifikat entsperren", "miss_stamp": "den Signaturblock im Dokument platzieren",
        "miss_ink": "die handschriftliche Unterschrift zeichnen",
       
        "toast_pick_p12": "Wählen Sie zuerst ein .p12-Zertifikat.", "toast_wait": "Zu viele Versuche. Bitte {s} s warten.",
        "toast_unlocked": "Zertifikat entsperrt.", "toast_expired": "Das Zertifikat ist abgelaufen: Die Signatur wird nicht gültig sein.",
        "toast_idle": "Zertifikat nach 5 Minuten Inaktivität gesperrt.", "toast_open_first": "Öffnen Sie zuerst ein PDF.",
        "toast_existing": "Dieses Dokument enthält bereits {n} Signatur(en). Mit dem Augen-Symbol anzeigen.",
        "toast_place_page": "Platzieren Sie den Block auf einer Seite.", "toast_overwrite": "Das Originaldokument kann nicht überschrieben werden.",
        "toast_save_fail": "Die Datei konnte nicht gespeichert werden.", "toast_signed": "Dokument signiert: {name}",
        "err_open": "Die Datei kann nicht geöffnet werden.", "err_not_regular": "Nur reguläre Dateien werden akzeptiert.",
        "err_size": "Dateigröße nicht zulässig (max. {mb} MiB).", "err_format": "Das Dateiformat ist ungültig.",
        "err_pdf_invalid": "Das PDF ist beschädigt oder ungültig.", "err_pdf_encrypted": "Verschlüsselte PDFs werden nicht unterstützt.",
        "err_pdf_pages": "Seitenanzahl nicht zulässig.", "err_cert": "Das Zertifikat konnte nicht geöffnet werden. Datei und Passwort prüfen.",
        "err_cert_nokey": "Die Datei enthält keinen privaten Schlüssel und kein Zertifikat.",
        "err_sign": "Das Dokument konnte nicht signiert werden ({code}).", "err_unexpected": "Unerwarteter Fehler beim Signieren.",
        "dlg_open_pdf": "PDF öffnen", "filter_pdf": "PDF-Dokumente (*.pdf)", "dlg_pick_p12": "Zertifikat wählen",
        "filter_p12": "Zertifikate (*.p12 *.pfx)", "dlg_save": "Signiertes Dokument speichern", "dlg_export": "Protokoll exportieren",
        "consent_welcome": "Willkommen bei TuxSign", "consent_audit": "Lokales Audit-Protokoll ohne personenbezogene Daten aktivieren (empfohlen)",
        "consent_ack": "Ich habe den Datenschutzhinweis gelesen und verstanden", "btn_exit": "Beenden", "btn_continue": "Weiter",
        "priv_title": "Datenschutz & Daten", "priv_audit_on": "Lokales Audit-Protokoll aktiv", "priv_retention": "Protokoll aufbewahren (Tage):",
        "priv_verify": "Integrität prüfen", "priv_export": "Protokoll exportieren", "priv_erase": "Alle meine Daten löschen", "priv_save": "Speichern & schließen",
        "priv_chain_ok": "✔ Protokoll intakt ({n} Einträge)", "priv_chain_bad": "✖ Protokollkette manipuliert! ({n} Einträge)",
        "priv_exported": "Protokoll exportiert.", "priv_erase_title": "Datenlöschung (Art. 17)",
        "priv_erase_text": "Einstellungen, Einwilligung und Audit-Protokoll werden unwiderruflich gelöscht.\nFortfahren?",
        "priv_erased": "{n} Dateien gelöscht. Die Anwendung wird beendet.",
        "ver_title": "Signaturen des Dokuments", "ver_none": "Dieses Dokument enthält keine digitalen Signaturen.",
        "ver_ok": "Integrität in Ordnung", "ver_modified": "Dokument verändert", "ver_later": " · Änderungen nach dieser Signatur",
        "ver_trust": "Das Vertrauen in den Zertifikatsaussteller muss separat bewertet werden.", "btn_close": "Schließen",
        "about_title": "Über TuxSign", "about_version": "Version", "about_build": "Build",
        "about_integrity": "Integritätsprüfung", "integ_ok": "Verifiziert", "integ_dev": "Entwicklungs-Build (unsigniert)",
        "integ_fail": "FEHLGESCHLAGEN", "btn_yes": "Ja", "btn_no": "Nein",
        "integrity_abort": "Die Dateien von TuxSign wurden verändert, deshalb startet die Anwendung nicht. Installiere sie erneut aus einer vertrauenswürdigen Quelle.",
        "privacy_notice": _NOTICE["de"],
    },
    "pt": {
        "err_sandbox_file": "O TuxSign corre isolado e não consegue ver esse ficheiro. Use Abrir PDF ou dê-lhe acesso à pasta.",
        "pages_many": "{n} páginas",
        "pages_one": "1 página",
        "err_render": "Não foi possível apresentar o PDF.",
        "tip_close_doc": "Fechar documento",
        "no_doc": "Sem documento", "btn_open": "Abrir PDF", "tip_sigs": "Ver assinaturas existentes",
        "tip_privacy": "Privacidade e dados", "tip_theme": "Mudar tema", "tip_lang": "Idioma", "tip_about": "Sobre o TuxSign",
        "drop_title": "Largue aqui o seu PDF", "drop_sub": "ou clique para escolher um documento",
        "drop_foot": "Tudo é processado no seu dispositivo · sem rede · sem telemetria",
        "tip_prev": "Página anterior", "tip_next": "Página seguinte", "tip_zoom_out": "Reduzir", "tip_zoom_in": "Ampliar", "tip_fit": "Ajustar à largura",
        
        "c1_title": "Certificado digital (.p12 / .pfx)", "c1_none": "Nenhum certificado selecionado", "c1_pick": "Escolher certificado",
        "c1_pw": "Palavra-passe do certificado", "c1_unlock": "Desbloquear", "c1_lock": "Bloquear certificado",
        "c1_issuer": "Emissor: {issuer}", "c1_valid": "Válido até {date}", "c1_expired": "EXPIRADO em {date}",
        "c2_title": "Bloco de assinatura", "c2_desc": "Mostra quem assinou e quando. Arraste para mover e puxe o canto para redimensionar.",
        "sw_hand": "Adicionar assinatura manuscrita", "pad_hint": "Desenhe com rato, trackpad ou caneta", "pad_line": "✕  Assine sobre a linha",
        "tip_undo": "Desfazer traço", "tip_clear": "Apagar assinatura",
        "btn_place": "Colocar bloco de assinatura", "btn_replace": "Atualizar bloco de assinatura",
        "stamp_signed_by": "Assinado digitalmente por:", "stamp_placeholder": "O seu nome",
        "c3_title": "Assinar e guardar", "reason_ph": "Motivo (opcional) · ex. Aprovação", "btn_sign": "Assinar documento", "signing": "A assinar…",
        "status_missing": "Falta: {items}.", "status_ready": "Tudo pronto. Verifique a posição e assine.",
        "miss_pdf": "abra um PDF", "miss_cert": "desbloqueie o certificado", "miss_stamp": "coloque o bloco de assinatura no documento",
        "miss_ink": "desenhe a sua assinatura manuscrita",
       
        "toast_pick_p12": "Escolha primeiro um certificado .p12.", "toast_wait": "Demasiadas tentativas. Aguarde {s} s.",
        "toast_unlocked": "Certificado desbloqueado.", "toast_expired": "O certificado expirou: a assinatura não será válida.",
        "toast_idle": "Certificado bloqueado após 5 minutos de inatividade.", "toast_open_first": "Abra primeiro um PDF.",
        "toast_existing": "Este documento já contém {n} assinatura(s). Use o ícone do olho para as ver.",
        "toast_place_page": "Coloque o bloco sobre uma página.", "toast_overwrite": "Não é possível substituir o documento original.",
        "toast_save_fail": "Não foi possível guardar o ficheiro.", "toast_signed": "Documento assinado: {name}",
        "err_open": "Não é possível abrir o ficheiro.", "err_not_regular": "Apenas são aceites ficheiros regulares.",
        "err_size": "Tamanho não permitido (máx. {mb} MiB).", "err_format": "O formato do ficheiro não é válido.",
        "err_pdf_invalid": "O PDF está danificado ou não é válido.", "err_pdf_encrypted": "Os PDF cifrados não são suportados.",
        "err_pdf_pages": "Número de páginas não permitido.", "err_cert": "Não foi possível abrir o certificado. Verifique o ficheiro e a palavra-passe.",
        "err_cert_nokey": "O ficheiro não contém chave privada e certificado.",
        "err_sign": "Não foi possível assinar o documento ({code}).", "err_unexpected": "Erro inesperado ao assinar.",
        "dlg_open_pdf": "Abrir PDF", "filter_pdf": "Documentos PDF (*.pdf)", "dlg_pick_p12": "Escolher certificado",
        "filter_p12": "Certificados (*.p12 *.pfx)", "dlg_save": "Guardar documento assinado", "dlg_export": "Exportar registo",
        "consent_welcome": "Bem-vindo ao TuxSign", "consent_audit": "Ativar registo de auditoria local sem dados pessoais (recomendado)",
        "consent_ack": "Li e compreendo o aviso de privacidade", "btn_exit": "Sair", "btn_continue": "Continuar",
        "priv_title": "Privacidade e dados", "priv_audit_on": "Registo de auditoria local ativo", "priv_retention": "Conservar registo (dias):",
        "priv_verify": "Verificar integridade", "priv_export": "Exportar registo", "priv_erase": "Apagar todos os meus dados", "priv_save": "Guardar e fechar",
        "priv_chain_ok": "✔ Registo íntegro ({n} entradas)", "priv_chain_bad": "✖ Cadeia do registo alterada! ({n} entradas)",
        "priv_exported": "Registo exportado.", "priv_erase_title": "Eliminação de dados (art. 17)",
        "priv_erase_text": "Serão eliminados, de forma irreversível, as definições, o consentimento e o registo de auditoria.\nContinuar?",
        "priv_erased": "{n} ficheiros eliminados. A aplicação vai fechar.",
        "ver_title": "Assinaturas do documento", "ver_none": "Este documento não contém assinaturas digitais.",
        "ver_ok": "Integridade correta", "ver_modified": "Documento modificado", "ver_later": " · alterações posteriores a esta assinatura",
        "ver_trust": "A confiança no emissor do certificado deve ser avaliada separadamente.", "btn_close": "Fechar",
        "about_title": "Sobre o TuxSign", "about_version": "Versão", "about_build": "Compilação",
        "about_integrity": "Verificação de integridade", "integ_ok": "Verificada", "integ_dev": "Compilação de desenvolvimento (não assinada)",
        "integ_fail": "FALHOU", "btn_yes": "Sim", "btn_no": "Não",
        "integrity_abort": "Os ficheiros do TuxSign foram alterados, por isso a aplicação não arranca. Reinstale-a a partir de uma fonte de confiança.",
        "privacy_notice": _NOTICE["pt"],
    },
}

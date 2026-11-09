(function () {
  "use strict";

  /* Español es el idioma del HTML. Aquí solo va la traducción al inglés. */
  var EN = {
    skip: "Skip to content", nav_features: "Features", nav_security: "Security", nav_install: "Install", nav_faq: "FAQ",
    aria_theme: "Toggle theme", eyebrow: "Free software for Linux",
    h1a: "Sign your PDFs with your certificate.", h1b: "Without anything leaving your computer.",
    lead: "TuxSign signs documents with your .p12 certificate and leaves the original untouched. No cloud, no network and no telemetry. You, your certificate and your PDF, and nobody else.",
    cta_download: "Download", cta_code: "View the code",
    fine: "Free and open source (MIT). Available as a Flatpak, a Python package and a native binary.",
    alt_hero: "TuxSign signing an agreement with a handwritten signature",
    feat_kicker: "What it does", feat_title: "Just what you need to sign well, and nothing more",
    feat_sub: "A small, carefully made tool. It opens fast, makes sense at first glance and asks for nothing it doesn't need.",
    f1t: "A real PAdES signature", f1p: "Signs the whole document with SHA-256 using your .p12 or .pfx certificate. You can sign several times and check the signatures it already has.",
    f2t: "Your signature, your way", f2p: "A block with your name and the date that you move and resize by hand. If you want, add your handwritten signature. It is off by default.",
    f3t: "A viewer you'll appreciate", f3p: "Smooth zoom, pages, drag and drop, and light or dark themes. With gentle animations that help instead of getting in the way.",
    f4t: "All on your computer", f4p: "No Internet connection, no accounts and no telemetry. Your document and your certificate never leave your machine.",
    f5t: "Security in layers", f5p: "The PDF opens in a process with no permissions, the code is verified at startup and the system forbids it from using the network.",
    f6t: "In your language", f6p: "Available in English, Spanish, French, German and Portuguese. Adding another language is a small change.",
    how_kicker: "How to use it", how_title: "Five steps and you're done",
    how_sub: "Open the PDF, unlock your certificate, place the signature block, adjust it and sign. A new copy is saved and the original is never touched.",
    tab_block: "Signature block", tab_hand: "Handwritten signature", tab_home: "Home screen",
    cap_block: "The block with your name and the date is dragged into place and resized from the corner.",
    cap_handwritten: "Turn on the switch and the canvas unfolds. Your drawing goes on top of the signature block.",
    cap_home: "Drop a PDF on the window or click to pick one. Everything stays on your computer.",
    sec_kicker: "Security", sec_title: "Security you can check",
    sec_sub: "We don't ask you to take our word for it. The code is open, there are tests for every protection and the design document also says what TuxSign doesn't achieve.",
    l1t: "No network", l1p: "A system filter (seccomp and Landlock) stops it from opening connections, and the Flatpak doesn't even have network access.",
    l2t: "Isolated PDF reader", l2p: "The PDF opens in a separate process with no access to files or programs. Your certificate lives in a different process.",
    l3t: "Verified code", l3p: "At startup it checks an Ed25519 signature over all the files. If anything changed, it won't start.",
    l4t: "Clean environment", l4p: "It ignores PYTHONPATH, LD_PRELOAD and other variables used to sneak in foreign code.",
    l5t: "Minimal data", l5p: "An optional log with no names or paths, which you can export or delete entirely whenever you like.",
    h_title: "What TuxSign doesn't do",
    h1: "It doesn't add a timestamp, because that needs an Internet connection.",
    h2: "It doesn't replace a token or an HSM if your key is very valuable.",
    h3: "Its signature is worth legally whatever your certificate is worth in your country.",
    h4: "The password goes through Python memory, which can't be fully wiped.",
    h_link: "Read the full design",
    ins_kicker: "Install", ins_title: "Install it in a minute",
    ins_sub: "With Flatpak you get the sandbox out of the box. From source is ideal if you want to poke around or contribute.",
    ins1t: "With Flatpak (recommended)", ins1p: "Download the bundle from the releases page and run:", ins_rel: "Go to releases", ins_dl: "Download Flatpak 1.2.0",
    ins2t: "From source", ins2p: "You need Python 3.10 or newer and Wayland or X11:", ins2n: "The script sets up the environment and installs the pinned dependencies.",
    faq_kicker: "FAQ", faq_title: "What people usually ask",
    q1: "Is the signature legally valid?", a1: "It depends on your certificate and your country's rules. TuxSign produces a standard PAdES signature with your certificate, but it is not a certified tool. If you need it for something official, check what the recipient requires.",
    q2: "Does my document get uploaded anywhere?", a2: "No. TuxSign doesn't use the network: the system prevents it and the Flatpak doesn't even have one. You can check in the code, which is open.",
    q3: "Does it work on Wayland and X11?", a3: "Yes, on both. One exception: an X11 DISPLAY over TCP, like the one from ssh -X, won't work because the app can't open network connections.",
    q4: "Can I use a token or a smart card?", a4: "Not yet. For now it only supports certificates in a .p12 or .pfx file. Supporting PKCS#11 would be a great contribution.",
    q5: "What license does it have?", a5: "The code is MIT. Binary packages bundle other libraries with their own licenses, such as PyMuPDF (AGPL-3.0) and Qt (LGPL-3.0), which you must respect if you redistribute them.",
    foot: "TuxSign is free software under the MIT license. Made with care for Linux.",
    foot_changes: "Changes", foot_sec: "Report a security issue", foot_lic: "License"
  };

  var FR = {
    skip: "Aller au contenu", nav_features: "Fonctions", nav_security: "Sécurité", nav_install: "Installer", nav_faq: "FAQ",
    aria_theme: "Changer le thème", eyebrow: "Logiciel libre pour Linux",
    h1a: "Signez vos PDF avec votre certificat.", h1b: "Sans que rien ne quitte votre ordinateur.",
    lead: "TuxSign signe vos documents avec votre certificat .p12 et laisse l'original intact. Sans cloud, sans réseau et sans télémétrie. Vous, votre certificat et votre PDF, et personne d'autre.",
    cta_download: "Télécharger", cta_code: "Voir le code",
    fine: "Libre et open source (MIT). Disponible en Flatpak, en paquet Python et en binaire natif.",
    alt_hero: "TuxSign signant un accord avec une signature manuscrite",
    feat_kicker: "Ce qu'il fait", feat_title: "Juste ce qu'il faut pour bien signer, rien de plus",
    feat_sub: "Un petit outil soigné. Il s'ouvre vite, se comprend au premier regard et ne demande rien d'inutile.",
    f1t: "Une vraie signature PAdES", f1p: "Signe tout le document avec SHA-256 grâce à votre certificat .p12 ou .pfx. Vous pouvez signer plusieurs fois et vérifier les signatures existantes.",
    f2t: "Votre signature, à votre façon", f2p: "Un bloc avec votre nom et la date que vous déplacez et redimensionnez à la main. Si vous le souhaitez, ajoutez votre signature manuscrite. Elle est désactivée par défaut.",
    f3t: "Une visionneuse agréable", f3p: "Zoom fluide, pages, glisser-déposer et thèmes clair ou sombre. Avec des animations discrètes qui aident au lieu de gêner.",
    f4t: "Tout sur votre ordinateur", f4p: "Sans connexion Internet, sans compte et sans télémétrie. Votre document et votre certificat ne quittent jamais votre machine.",
    f5t: "Une sécurité en couches", f5p: "Le PDF s'ouvre dans un processus sans permissions, le code est vérifié au démarrage et le système lui interdit d'utiliser le réseau.",
    f6t: "Dans votre langue", f6p: "Disponible en anglais, espagnol, français, allemand et portugais. Ajouter une autre langue est une petite modification.",
    how_kicker: "Comment l'utiliser", how_title: "Cinq étapes et c'est fait",
    how_sub: "Ouvrez le PDF, déverrouillez votre certificat, placez le bloc de signature, ajustez-le et signez. Une nouvelle copie est enregistrée et l'original n'est jamais touché.",
    tab_block: "Bloc de signature", tab_hand: "Signature manuscrite", tab_home: "Écran d'accueil",
    cap_block: "Le bloc avec votre nom et la date se déplace et se redimensionne depuis le coin.",
    cap_handwritten: "Activez l'interrupteur et la zone de dessin se déploie. Votre tracé se place par-dessus le bloc de signature.",
    cap_home: "Déposez un PDF sur la fenêtre ou cliquez pour en choisir un. Tout reste sur votre ordinateur.",
    sec_kicker: "Sécurité", sec_title: "Une sécurité vérifiable",
    sec_sub: "Nous ne vous demandons pas de nous croire sur parole. Le code est ouvert, chaque protection a ses tests et le document de conception indique aussi ce que TuxSign n'accomplit pas.",
    l1t: "Pas de réseau", l1p: "Un filtre système (seccomp et Landlock) l'empêche d'ouvrir des connexions, et le Flatpak n'a même pas accès au réseau.",
    l2t: "Lecteur de PDF isolé", l2p: "Le PDF s'ouvre dans un processus séparé, sans accès aux fichiers ni aux programmes. Votre certificat vit dans un autre processus.",
    l3t: "Code vérifié", l3p: "Au démarrage, il vérifie une signature Ed25519 sur tous les fichiers. Si quelque chose a changé, il ne démarre pas.",
    l4t: "Environnement propre", l4p: "Il ignore PYTHONPATH, LD_PRELOAD et d'autres variables servant à introduire du code étranger.",
    l5t: "Données minimales", l5p: "Un journal facultatif sans noms ni chemins, que vous pouvez exporter ou supprimer entièrement à tout moment.",
    h_title: "Ce que TuxSign ne fait pas",
    h1: "Il n'ajoute pas d'horodatage, car cela exige une connexion Internet.",
    h2: "Il ne remplace pas un token ou un HSM si votre clé a une grande valeur.",
    h3: "Sa signature vaut juridiquement ce que vaut votre certificat dans votre pays.",
    h4: "Le mot de passe passe par la mémoire de Python, qui ne peut pas être entièrement effacée.",
    h_link: "Lire la conception complète",
    ins_kicker: "Installer", ins_title: "Installez-le en une minute",
    ins_sub: "Avec Flatpak, vous avez le bac à sable d'office. Depuis les sources, c'est idéal pour fouiller ou contribuer.",
    ins1t: "Avec Flatpak (recommandé)", ins1p: "Téléchargez le paquet depuis la page des versions et lancez :", ins_rel: "Aller aux versions", ins_dl: "Télécharger Flatpak 1.2.0",
    ins2t: "Depuis les sources", ins2p: "Il faut Python 3.10 ou plus récent et Wayland ou X11 :", ins2n: "Le script prépare l'environnement et installe les dépendances figées.",
    faq_kicker: "FAQ", faq_title: "Ce qu'on demande souvent",
    q1: "La signature a-t-elle une valeur légale ?", a1: "Cela dépend de votre certificat et des règles de votre pays. TuxSign produit une signature PAdES standard avec votre certificat, mais ce n'est pas un outil certifié. Si vous en avez besoin pour une démarche officielle, vérifiez ce qu'exige le destinataire.",
    q2: "Mon document est-il envoyé quelque part ?", a2: "Non. TuxSign n'utilise pas le réseau : le système l'en empêche et le Flatpak n'en a même pas. Vous pouvez le vérifier dans le code, qui est ouvert.",
    q3: "Fonctionne-t-il sous Wayland et X11 ?", a3: "Oui, sur les deux. Une exception : un DISPLAY X11 par TCP, comme celui de ssh -X, ne fonctionnera pas car l'application ne peut pas ouvrir de connexions réseau.",
    q4: "Puis-je utiliser un token ou une carte à puce ?", a4: "Pas encore. Pour l'instant, seuls les certificats dans un fichier .p12 ou .pfx sont pris en charge. Gérer PKCS#11 serait une excellente contribution.",
    q5: "Quelle licence a-t-il ?", a5: "Le code est sous licence MIT. Les paquets binaires embarquent d'autres bibliothèques avec leurs propres licences, comme PyMuPDF (AGPL-3.0) et Qt (LGPL-3.0), que vous devez respecter si vous les redistribuez.",
    foot: "TuxSign est un logiciel libre sous licence MIT. Fait avec soin pour Linux.",
    foot_changes: "Changements", foot_sec: "Signaler un problème de sécurité", foot_lic: "Licence"
  };
  var DE = {
    skip: "Zum Inhalt springen", nav_features: "Funktionen", nav_security: "Sicherheit", nav_install: "Installation", nav_faq: "FAQ",
    aria_theme: "Design wechseln", eyebrow: "Freie Software für Linux",
    h1a: "Signieren Sie Ihre PDFs mit Ihrem Zertifikat.", h1b: "Ohne dass etwas Ihren Rechner verlässt.",
    lead: "TuxSign signiert Dokumente mit Ihrem .p12-Zertifikat und lässt das Original unangetastet. Ohne Cloud, ohne Netzwerk und ohne Telemetrie. Sie, Ihr Zertifikat und Ihr PDF, sonst niemand.",
    cta_download: "Herunterladen", cta_code: "Code ansehen",
    fine: "Frei und quelloffen (MIT). Verfügbar als Flatpak, Python-Paket und natives Programm.",
    alt_hero: "TuxSign unterzeichnet eine Vereinbarung mit einer handschriftlichen Unterschrift",
    feat_kicker: "Was es kann", feat_title: "Genau das, was man zum guten Signieren braucht, und nicht mehr",
    feat_sub: "Ein kleines, sorgfältig gemachtes Werkzeug. Es startet schnell, ist auf den ersten Blick verständlich und verlangt nichts Unnötiges.",
    f1t: "Eine echte PAdES-Signatur", f1p: "Signiert das gesamte Dokument mit SHA-256 und Ihrem .p12- oder .pfx-Zertifikat. Sie können mehrfach signieren und vorhandene Signaturen prüfen.",
    f2t: "Ihre Signatur, auf Ihre Art", f2p: "Ein Block mit Ihrem Namen und dem Datum, den Sie von Hand verschieben und in der Größe ändern. Auf Wunsch fügen Sie Ihre handschriftliche Unterschrift hinzu. Standardmäßig ist sie aus.",
    f3t: "Ein Betrachter, der Freude macht", f3p: "Flüssiger Zoom, Seiten, Drag-and-drop sowie helles oder dunkles Design. Mit dezenten Animationen, die helfen statt zu stören.",
    f4t: "Alles auf Ihrem Rechner", f4p: "Keine Internetverbindung, keine Konten und keine Telemetrie. Ihr Dokument und Ihr Zertifikat verlassen Ihren Rechner nie.",
    f5t: "Sicherheit in Schichten", f5p: "Das PDF wird in einem Prozess ohne Berechtigungen geöffnet, der Code wird beim Start geprüft und das System verbietet die Netzwerknutzung.",
    f6t: "In Ihrer Sprache", f6p: "Verfügbar auf Englisch, Spanisch, Französisch, Deutsch und Portugiesisch. Eine weitere Sprache hinzuzufügen ist eine kleine Änderung.",
    how_kicker: "So geht's", how_title: "Fünf Schritte und fertig",
    how_sub: "PDF öffnen, Zertifikat entsperren, Signaturblock platzieren, anpassen und signieren. Es wird eine neue Kopie gespeichert, das Original bleibt unberührt.",
    tab_block: "Signaturblock", tab_hand: "Handschriftliche Unterschrift", tab_home: "Startbildschirm",
    cap_block: "Der Block mit Ihrem Namen und dem Datum wird verschoben und an der Ecke in der Größe geändert.",
    cap_handwritten: "Schalter aktivieren und die Zeichenfläche klappt auf. Ihre Zeichnung liegt über dem Signaturblock.",
    cap_home: "Ziehen Sie ein PDF auf das Fenster oder klicken Sie, um eines zu wählen. Alles bleibt auf Ihrem Rechner.",
    sec_kicker: "Sicherheit", sec_title: "Sicherheit zum Nachprüfen",
    sec_sub: "Wir bitten Sie nicht, uns einfach zu glauben. Der Code ist offen, jeder Schutz hat Tests und das Entwurfsdokument nennt auch, was TuxSign nicht leistet.",
    l1t: "Kein Netzwerk", l1p: "Ein Systemfilter (seccomp und Landlock) verhindert Verbindungen, und das Flatpak hat nicht einmal Netzwerkzugriff.",
    l2t: "Isolierter PDF-Leser", l2p: "Das PDF wird in einem separaten Prozess ohne Zugriff auf Dateien oder Programme geöffnet. Ihr Zertifikat liegt in einem anderen Prozess.",
    l3t: "Geprüfter Code", l3p: "Beim Start wird eine Ed25519-Signatur über alle Dateien geprüft. Hat sich etwas geändert, startet es nicht.",
    l4t: "Saubere Umgebung", l4p: "Es ignoriert PYTHONPATH, LD_PRELOAD und andere Variablen, mit denen fremder Code eingeschleust wird.",
    l5t: "Minimale Daten", l5p: "Ein optionales Protokoll ohne Namen oder Pfade, das Sie jederzeit exportieren oder vollständig löschen können.",
    h_title: "Was TuxSign nicht tut",
    h1: "Es fügt keinen Zeitstempel hinzu, da dafür eine Internetverbindung nötig ist.",
    h2: "Es ersetzt keinen Token oder HSM, wenn Ihr Schlüssel sehr wertvoll ist.",
    h3: "Die Signatur ist rechtlich so viel wert, wie Ihr Zertifikat in Ihrem Land wert ist.",
    h4: "Das Passwort läuft durch den Python-Speicher, der sich nicht vollständig löschen lässt.",
    h_link: "Den ganzen Entwurf lesen",
    ins_kicker: "Installation", ins_title: "In einer Minute installiert",
    ins_sub: "Mit Flatpak ist die Sandbox gleich dabei. Aus dem Quellcode ist ideal, wenn Sie stöbern oder mitarbeiten wollen.",
    ins1t: "Mit Flatpak (empfohlen)", ins1p: "Laden Sie das Paket von der Release-Seite herunter und führen Sie aus:", ins_rel: "Zu den Releases", ins_dl: "Flatpak 1.2.0 herunterladen",
    ins2t: "Aus dem Quellcode", ins2p: "Sie brauchen Python 3.10 oder neuer und Wayland oder X11:", ins2n: "Das Skript richtet die Umgebung ein und installiert die festgelegten Abhängigkeiten.",
    faq_kicker: "FAQ", faq_title: "Was oft gefragt wird",
    q1: "Ist die Signatur rechtlich gültig?", a1: "Das hängt von Ihrem Zertifikat und den Regeln Ihres Landes ab. TuxSign erzeugt mit Ihrem Zertifikat eine standardkonforme PAdES-Signatur, ist aber kein zertifiziertes Werkzeug. Brauchen Sie sie für etwas Offizielles, klären Sie, was der Empfänger verlangt.",
    q2: "Wird mein Dokument irgendwohin hochgeladen?", a2: "Nein. TuxSign nutzt das Netzwerk nicht: Das System verhindert es und das Flatpak hat keines. Sie können es im offenen Code nachprüfen.",
    q3: "Läuft es unter Wayland und X11?", a3: "Ja, unter beiden. Eine Ausnahme: Ein X11-DISPLAY über TCP, wie bei ssh -X, funktioniert nicht, weil die App keine Netzwerkverbindungen öffnen kann.",
    q4: "Kann ich einen Token oder eine Smartcard nutzen?", a4: "Noch nicht. Derzeit werden nur Zertifikate in einer .p12- oder .pfx-Datei unterstützt. PKCS#11 zu unterstützen wäre ein toller Beitrag.",
    q5: "Welche Lizenz hat es?", a5: "Der Code steht unter MIT. Binärpakete enthalten andere Bibliotheken mit eigenen Lizenzen, etwa PyMuPDF (AGPL-3.0) und Qt (LGPL-3.0), die Sie bei der Weitergabe beachten müssen.",
    foot: "TuxSign ist freie Software unter der MIT-Lizenz. Mit Sorgfalt für Linux gemacht.",
    foot_changes: "Änderungen", foot_sec: "Sicherheitsproblem melden", foot_lic: "Lizenz"
  };
  var PT = {
    skip: "Ir para o conteúdo", nav_features: "Funções", nav_security: "Segurança", nav_install: "Instalar", nav_faq: "Perguntas",
    aria_theme: "Alternar tema", eyebrow: "Software livre para Linux",
    h1a: "Assine seus PDFs com seu certificado.", h1b: "Sem que nada saia do seu computador.",
    lead: "O TuxSign assina documentos com seu certificado .p12 e deixa o original intacto. Sem nuvem, sem rede e sem telemetria. Você, seu certificado e seu PDF, e mais ninguém.",
    cta_download: "Baixar", cta_code: "Ver o código",
    fine: "Livre e de código aberto (MIT). Disponível como Flatpak, pacote Python e binário nativo.",
    alt_hero: "TuxSign assinando um acordo com uma assinatura manuscrita",
    feat_kicker: "O que faz", feat_title: "Só o que você precisa para assinar bem, e nada mais",
    feat_sub: "Uma ferramenta pequena e bem cuidada. Abre rápido, faz sentido à primeira vista e não pede nada que não precise.",
    f1t: "Uma assinatura PAdES de verdade", f1p: "Assina o documento inteiro com SHA-256 usando seu certificado .p12 ou .pfx. Você pode assinar várias vezes e verificar as assinaturas existentes.",
    f2t: "Sua assinatura, do seu jeito", f2p: "Um bloco com seu nome e a data que você move e redimensiona à mão. Se quiser, adicione sua assinatura manuscrita. Ela vem desativada por padrão.",
    f3t: "Um visualizador agradável", f3p: "Zoom suave, páginas, arrastar e soltar e temas claro ou escuro. Com animações discretas que ajudam em vez de atrapalhar.",
    f4t: "Tudo no seu computador", f4p: "Sem conexão com a Internet, sem contas e sem telemetria. Seu documento e seu certificado nunca saem da sua máquina.",
    f5t: "Segurança em camadas", f5p: "O PDF abre em um processo sem permissões, o código é verificado ao iniciar e o sistema proíbe o uso da rede.",
    f6t: "No seu idioma", f6p: "Disponível em inglês, espanhol, francês, alemão e português. Adicionar outro idioma é uma pequena mudança.",
    how_kicker: "Como usar", how_title: "Cinco passos e pronto",
    how_sub: "Abra o PDF, desbloqueie seu certificado, posicione o bloco de assinatura, ajuste e assine. Uma nova cópia é salva e o original nunca é tocado.",
    tab_block: "Bloco de assinatura", tab_hand: "Assinatura manuscrita", tab_home: "Tela inicial",
    cap_block: "O bloco com seu nome e a data é arrastado até o lugar e redimensionado pelo canto.",
    cap_handwritten: "Ative o interruptor e a tela de desenho se abre. Seu traço fica sobre o bloco de assinatura.",
    cap_home: "Solte um PDF na janela ou clique para escolher um. Tudo fica no seu computador.",
    sec_kicker: "Segurança", sec_title: "Segurança que você pode verificar",
    sec_sub: "Não pedimos que você acredite na nossa palavra. O código é aberto, cada proteção tem testes e o documento de projeto também diz o que o TuxSign não consegue.",
    l1t: "Sem rede", l1p: "Um filtro do sistema (seccomp e Landlock) impede que abra conexões, e o Flatpak nem tem acesso à rede.",
    l2t: "Leitor de PDF isolado", l2p: "O PDF abre em um processo separado, sem acesso a arquivos nem programas. Seu certificado fica em outro processo.",
    l3t: "Código verificado", l3p: "Ao iniciar, verifica uma assinatura Ed25519 sobre todos os arquivos. Se algo mudou, não inicia.",
    l4t: "Ambiente limpo", l4p: "Ignora PYTHONPATH, LD_PRELOAD e outras variáveis usadas para introduzir código alheio.",
    l5t: "Dados mínimos", l5p: "Um registro opcional sem nomes nem caminhos, que você pode exportar ou apagar por completo quando quiser.",
    h_title: "O que o TuxSign não faz",
    h1: "Não adiciona carimbo de tempo, porque isso exige conexão com a Internet.",
    h2: "Não substitui um token ou HSM se sua chave tiver muito valor.",
    h3: "Sua assinatura vale legalmente o que vale o seu certificado no seu país.",
    h4: "A senha passa pela memória do Python, que não pode ser totalmente apagada.",
    h_link: "Ler o projeto completo",
    ins_kicker: "Instalar", ins_title: "Instale em um minuto",
    ins_sub: "Com Flatpak você já tem o sandbox. A partir do código-fonte é ideal se quiser explorar ou contribuir.",
    ins1t: "Com Flatpak (recomendado)", ins1p: "Baixe o pacote na página de lançamentos e execute:", ins_rel: "Ir aos lançamentos", ins_dl: "Baixar Flatpak 1.2.0",
    ins2t: "A partir do código-fonte", ins2p: "Você precisa de Python 3.10 ou mais recente e Wayland ou X11:", ins2n: "O script prepara o ambiente e instala as dependências fixadas.",
    faq_kicker: "Perguntas", faq_title: "O que costumam perguntar",
    q1: "A assinatura tem validade legal?", a1: "Depende do seu certificado e das regras do seu país. O TuxSign gera uma assinatura PAdES padrão com seu certificado, mas não é uma ferramenta certificada. Se precisar dela para algo oficial, verifique o que o destinatário exige.",
    q2: "Meu documento é enviado para algum lugar?", a2: "Não. O TuxSign não usa a rede: o sistema impede e o Flatpak nem tem uma. Você pode conferir no código, que é aberto.",
    q3: "Funciona em Wayland e X11?", a3: "Sim, em ambos. Uma exceção: um DISPLAY X11 via TCP, como o de ssh -X, não funciona porque o app não pode abrir conexões de rede.",
    q4: "Posso usar um token ou smart card?", a4: "Ainda não. Por enquanto só aceita certificados em um arquivo .p12 ou .pfx. Dar suporte a PKCS#11 seria uma ótima contribuição.",
    q5: "Qual é a licença?", a5: "O código é MIT. Os pacotes binários incluem outras bibliotecas com licenças próprias, como PyMuPDF (AGPL-3.0) e Qt (LGPL-3.0), que você deve respeitar se redistribuí-los.",
    foot: "O TuxSign é software livre sob a licença MIT. Feito com carinho para Linux.",
    foot_changes: "Alterações", foot_sec: "Relatar um problema de segurança", foot_lic: "Licença"
  };
  var DICT = { en: EN, fr: FR, de: DE, pt: PT };
  var NAMES = { es: "Español", en: "English", fr: "Français", de: "Deutsch", pt: "Português" };
  var TITLES = {
    es: "TuxSign: firma PDF con tu certificado, todo en local",
    en: "TuxSign: sign PDFs with your certificate, all local",
    fr: "TuxSign : signez vos PDF avec votre certificat, tout en local",
    de: "TuxSign: PDFs mit Ihrem Zertifikat signieren, alles lokal",
    pt: "TuxSign: assine PDFs com seu certificado, tudo local"
  };

  var root = document.documentElement;
  var CAP = { block: "cap_block", handwritten: "cap_handwritten", home: "cap_home" };
  var ES_CAP = {
    cap_handwritten: "Activa el interruptor y se despliega el lienzo. Tu dibujo se coloca sobre el bloque de firma.",
    cap_home: "Suelta un PDF en la ventana o haz clic para elegir uno. Todo se queda en tu equipo."
  };
  var lang = "es";

  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* sin almacenamiento */ } }

  function theme() { return root.getAttribute("data-theme") === "light" ? "light" : "dark"; }

  function applyShots() {
    document.querySelectorAll("img[data-shot]").forEach(function (img) {
      img.src = "assets/" + img.getAttribute("data-shot") + "-" + (lang === "es" ? "es" : "en") + "-" + theme() + ".webp";
    });
  }

  function tr(key) {
    var d = DICT[lang];
    if (!d) { return null; }
    if (d[key] !== undefined) { return d[key]; }
    return EN[key] !== undefined ? EN[key] : null;
  }

  function applyLang() {
    root.setAttribute("lang", lang);
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      if (el.dataset.es === undefined) { el.dataset.es = el.textContent; }
      var t = tr(el.getAttribute("data-i18n"));
      el.textContent = t !== null ? t : el.dataset.es;
    });
    [["alt", "data-i18n-alt"], ["aria-label", "data-i18n-aria"]].forEach(function (pair) {
      document.querySelectorAll("[" + pair[1] + "]").forEach(function (el) {
        var store = "data-es-" + pair[0];
        if (!el.hasAttribute(store)) { el.setAttribute(store, el.getAttribute(pair[0]) || ""); }
        var t = tr(el.getAttribute(pair[1]));
        el.setAttribute(pair[0], t !== null ? t : el.getAttribute(store));
      });
    });
    document.getElementById("lang-label").textContent = NAMES[lang];
    document.getElementById("lang-flag").src = "assets/flags/" + lang + ".svg";
    document.querySelectorAll("#lang-menu [role=option]").forEach(function (o) {
      o.setAttribute("aria-selected", o.getAttribute("data-lang") === lang ? "true" : "false");
    });
    document.title = TITLES[lang];
    updateCaption();
    applyShots();
  }

  function updateCaption() {
    var active = document.querySelector(".tab[aria-selected='true']");
    var cap = document.getElementById("caption");
    if (!active || !cap) { return; }
    var key = CAP[active.getAttribute("data-tab")];
    cap.setAttribute("data-i18n", key);
    var es = ES_CAP[key];
    if (lang !== "es") { cap.textContent = tr(key); }
    else if (es) { cap.textContent = es; }
    else { cap.textContent = cap.dataset.esblock || cap.textContent; }
  }

  /* pestañas del escaparate */
  var caption = document.getElementById("caption");
  if (caption) { caption.dataset.esblock = caption.textContent; }
  document.querySelectorAll(".tab").forEach(function (tab) {
    tab.addEventListener("click", function () {
      document.querySelectorAll(".tab").forEach(function (t) { t.setAttribute("aria-selected", "false"); });
      tab.setAttribute("aria-selected", "true");
      var img = document.getElementById("showcase-img");
      img.style.opacity = "0";
      setTimeout(function () {
        img.setAttribute("data-shot", tab.getAttribute("data-tab"));
        applyShots();
        updateCaption();
        img.style.opacity = "1";
      }, 180);
    });
  });

  /* tema */
  function setTheme(t) {
    root.setAttribute("data-theme", t);
    set("tuxsign-theme", t);
    document.getElementById("theme-icon").setAttribute("href", t === "dark" ? "#i-sun" : "#i-moon");
    applyShots();
  }
  document.getElementById("theme").addEventListener("click", function () {
    var next = theme() === "dark" ? "light" : "dark";
    var calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (calm || !document.startViewTransition) { setTheme(next); return; }
    /* Cortina de arriba a abajo: el navegador congela la página vieja y descubre la nueva. */
    root.setAttribute("data-curtain", next === "dark" ? "down" : "up");
    document.startViewTransition(function () {
      setTheme(next);
      var pending = [];
      document.querySelectorAll("img[data-shot]").forEach(function (img) {
        if (img.decode) { pending.push(img.decode().catch(function () { /* sigue sin la imagen */ })); }
      });
      return Promise.all(pending);
    });
  });
  document.getElementById("theme-icon").setAttribute("href", theme() === "dark" ? "#i-sun" : "#i-moon");

  /* idioma */
  var langBtn = document.getElementById("lang");
  var langMenu = document.getElementById("lang-menu");
  Object.keys(NAMES).forEach(function (code) {
    var li = document.createElement("li");
    li.setAttribute("role", "option");
    li.setAttribute("data-lang", code);
    li.setAttribute("tabindex", "-1");
    var fl = document.createElement("img");
    fl.src = "assets/flags/" + code + ".svg";
    fl.alt = "";
    fl.width = 20;
    fl.height = 14;
    li.appendChild(fl);
    li.appendChild(document.createTextNode(NAMES[code]));
    langMenu.appendChild(li);
  });
  function openMenu(open) {
    langMenu.hidden = !open;
    langBtn.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) {
      var sel = langMenu.querySelector("[aria-selected=true]");
      if (sel) { sel.focus(); }
    }
  }
  function chooseLang(code) {
    openMenu(false);
    langBtn.focus();
    if (code === lang || !NAMES[code]) { return; }
    lang = code;
    set("tuxsign-lang", lang);
    var calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (calm) { applyLang(); return; }
    root.classList.add("lang-out");
    setTimeout(function () {
      applyLang();
      root.classList.remove("lang-out");
    }, 240);
  }
  langBtn.addEventListener("click", function () { openMenu(langMenu.hidden); });
  langMenu.addEventListener("click", function (e) {
    var li = e.target.closest("[data-lang]");
    if (li) { chooseLang(li.getAttribute("data-lang")); }
  });
  langMenu.addEventListener("keydown", function (e) {
    var items = Array.prototype.slice.call(langMenu.querySelectorAll("[role=option]"));
    var i = items.indexOf(document.activeElement);
    if (e.key === "ArrowDown") { e.preventDefault(); items[(i + 1) % items.length].focus(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
    else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); if (i >= 0) { chooseLang(items[i].getAttribute("data-lang")); } }
    else if (e.key === "Escape") { openMenu(false); langBtn.focus(); }
  });
  document.addEventListener("click", function (e) {
    if (!langMenu.hidden && !e.target.closest(".lang-dd")) { openMenu(false); }
  });
  var saved = get("tuxsign-lang");
  var nav = (navigator.language || "es").toLowerCase();
  lang = NAMES[saved] ? saved : (NAMES[nav.slice(0, 2)] ? nav.slice(0, 2) : "es");
  applyLang();

  /* botones de copiar */
  document.querySelectorAll(".copy").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var text = btn.getAttribute("data-copy");
      var done = function () {
        btn.classList.add("done");
        btn.querySelector("use").setAttribute("href", "#i-check");
        setTimeout(function () { btn.classList.remove("done"); btn.querySelector("use").setAttribute("href", "#i-copy"); }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(text).then(done); }
    });
  });

  /* animación de entrada al hacer scroll */
  var items = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add("in"); });
  }
})();

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
      img.src = "assets/" + img.getAttribute("data-shot") + "-" + lang + "-" + theme() + ".webp";
    });
  }

  function tr(key) {
    if (lang === "en" && EN[key] !== undefined) { return EN[key]; }
    return null;
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
    document.getElementById("lang-label").textContent = lang === "es" ? "EN" : "ES";
    var title = lang === "es" ? "TuxSign: firma PDF con tu certificado, todo en local" : "TuxSign: sign PDFs with your certificate, all local";
    document.title = title;
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
    if (lang === "en") { cap.textContent = EN[key]; }
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
  document.getElementById("lang").addEventListener("click", function () {
    lang = lang === "es" ? "en" : "es";
    set("tuxsign-lang", lang);
    var calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (calm) { applyLang(); return; }
    root.classList.add("lang-out");
    setTimeout(function () {
      applyLang();
      root.classList.remove("lang-out");
    }, 240);
  });
  var saved = get("tuxsign-lang");
  var nav = (navigator.language || "es").toLowerCase();
  lang = saved || (nav.indexOf("es") === 0 ? "es" : (nav.indexOf("en") === 0 ? "en" : "es"));
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

/* CABRU — componente contatti condiviso (modale + invio via Google Apps Script).
   Self-contained: inietta stile + markup, si aggancia a qualunque
   elemento con classe .js-contact o link verso la vecchia pagina contatti.
   Il messaggio viene registrato nel Google Sheet privato e inoltrato a
   info@cabru.it, con email di conferma al mittente (stesso backend del catalogo). */
(function () {
  "use strict";
  var ENDPOINT = "https://script.google.com/macros/s/AKfycbxFIOSOQAUYItZ3p7jrT3twEtVousUhwBWJyMgU0ZLjMttBUoa-uiCRRTEzrzSOtuk3/exec";

  var EN = (document.documentElement.lang || "it").toLowerCase().indexOf("en") === 0
        || location.pathname.indexOf("/en/") !== -1;

  var T = EN ? {
    title: "Contact us",
    sub: "Send a message to CABRU. We reply as soon as possible.",
    name: "Full name", email: "Email", tel: "Phone",
    company: "Company / Institution", dept: "Department", msg: "Message",
    send: "Send message", sending: "Sending…",
    ok: "Message sent. Thank you, we will get back to you shortly.",
    err: "Sending failed. Please try again or write to info@cabru.it.",
    reqmail: "Please enter a valid email address.",
    reqmsg: "Please enter a message.", close: "Close"
  } : {
    title: "Contattaci",
    sub: "Invia un messaggio a CABRU. Rispondiamo nel più breve tempo possibile.",
    name: "Nome e cognome", email: "Email", tel: "Telefono",
    company: "Azienda / Ente", dept: "Reparto", msg: "Messaggio",
    send: "Invia messaggio", sending: "Invio in corso…",
    ok: "Messaggio inviato. Grazie, ti risponderemo a breve.",
    err: "Invio non riuscito. Riprova o scrivi a info@cabru.it.",
    reqmail: "Inserisci un indirizzo email valido.",
    reqmsg: "Inserisci un messaggio.", close: "Chiudi"
  };

  /* ---- stile iniettato (indipendente dai CSS di pagina) ---- */
  var css = ''
    + '.cmodal{position:fixed;inset:0;z-index:9999;display:none;align-items:flex-start;justify-content:center;padding:24px 16px;overflow:auto}'
    + '.cmodal.open{display:flex}'
    + '.cmodal__bg{position:fixed;inset:0;background:rgba(20,28,32,.55)}'
    + '.cmodal__box{position:relative;background:#fff;color:#2b2b30;width:100%;max-width:560px;border-radius:14px;padding:28px 26px 26px;box-shadow:0 24px 60px rgba(0,0,0,.28);margin:auto}'
    + '.cmodal__x{position:absolute;top:12px;right:14px;border:0;background:transparent;font-size:26px;line-height:1;color:#8a9199;cursor:pointer}'
    + '.cmodal h2{margin:0 0 4px;font-size:1.5rem;color:#0f80a8}'
    + '.cmodal .cm-sub{margin:0 0 18px;color:#5b636b;font-size:.95rem}'
    + '.cm-form{display:grid;grid-template-columns:1fr 1fr;gap:12px 14px}'
    + '.cm-form .full{grid-column:1/-1}'
    + '.cm-form label{display:block;font-size:.8rem;font-weight:600;color:#40474e;margin-bottom:4px}'
    + '.cm-form .req{color:#0f80a8}'
    + '.cm-form input,.cm-form textarea{width:100%;box-sizing:border-box;border:1px solid #d5dbe0;border-radius:8px;padding:9px 11px;font:inherit;font-size:.95rem;color:#2b2b30;background:#fff}'
    + '.cm-form input:focus,.cm-form textarea:focus{outline:none;border-color:#0f80a8;box-shadow:0 0 0 3px rgba(15,128,168,.14)}'
    + '.cm-form textarea{resize:vertical;min-height:76px}'
    + '.cm-btn{width:100%;border:0;border-radius:9px;background:#0f80a8;color:#fff;font:inherit;font-weight:600;font-size:1rem;padding:12px;cursor:pointer;transition:.15s}'
    + '.cm-btn:hover{background:#0a6485}'
    + '.cm-btn[disabled]{opacity:.6;cursor:default}'
    + '.cm-note{grid-column:1/-1;margin:2px 0 0;font-size:.9rem;border-radius:8px;padding:10px 12px;display:none}'
    + '.cm-note.ok{display:block;background:#e4f0f5;color:#0a6485}'
    + '.cm-note.ko{display:block;background:#fbe7e6;color:#b02a24}'
    + '@media(max-width:520px){.cm-form{grid-template-columns:1fr}}';
  var st = document.createElement("style");
  st.textContent = css;
  document.head.appendChild(st);

  /* ---- markup modale ---- */
  var wrap = document.createElement("div");
  wrap.className = "cmodal";
  wrap.setAttribute("aria-hidden", "true");
  wrap.innerHTML = ''
    + '<div class="cmodal__bg" data-cx></div>'
    + '<div class="cmodal__box" role="dialog" aria-modal="true" aria-label="' + T.title + '">'
    + '<button class="cmodal__x" type="button" data-cx aria-label="' + T.close + '">&times;</button>'
    + '<h2>' + T.title + '</h2><p class="cm-sub">' + T.sub + '</p>'
    + '<form class="cm-form" novalidate>'
    + '<div class="full"><label>' + T.name + '</label><input name="name" type="text" autocomplete="name"></div>'
    + '<div><label>' + T.email + ' <span class="req">*</span></label><input name="email" type="email" required autocomplete="email"></div>'
    + '<div><label>' + T.tel + '</label><input name="telefono" type="text" autocomplete="tel"></div>'
    + '<div><label>' + T.company + '</label><input name="azienda" type="text" autocomplete="organization"></div>'
    + '<div><label>' + T.dept + '</label><input name="reparto" type="text"></div>'
    + '<div class="full"><label>' + T.msg + ' <span class="req">*</span></label><textarea name="messaggio" rows="3" required></textarea></div>'
    + '<input type="checkbox" name="botcheck" style="display:none" tabindex="-1" autocomplete="off">'
    + '<p class="cm-note"></p>'
    + '<div class="full"><button class="cm-btn" type="submit">' + T.send + '</button></div>'
    + '</form></div>';
  document.addEventListener("DOMContentLoaded", function () { document.body.appendChild(wrap); });

  var form = wrap.querySelector(".cm-form");
  var note = wrap.querySelector(".cm-note");
  var btn = wrap.querySelector(".cm-btn");

  function open() { wrap.classList.add("open"); wrap.setAttribute("aria-hidden", "false"); setTimeout(function () { var f = form.querySelector('input[name=name]'); if (f) f.focus(); }, 30); }
  function close() { wrap.classList.remove("open"); wrap.setAttribute("aria-hidden", "true"); }
  function setNote(cls, txt) { note.className = "cm-note " + cls; note.textContent = txt; }

  wrap.addEventListener("click", function (e) { if (e.target.hasAttribute("data-cx")) close(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });

  /* aggancio: qualunque .js-contact o link alla vecchia pagina contatti */
  document.addEventListener("click", function (e) {
    var a = e.target.closest("a,button");
    if (!a) return;
    var href = (a.getAttribute("href") || "");
    var hit = a.classList.contains("js-contact")
           || /\/(contatti|en\/contact)\/?$/.test(href);
    if (hit) { e.preventDefault(); open(); }
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var email = form.email.value.trim();
    var msg = form.messaggio.value.trim();
    if (!email || email.indexOf("@") < 1) { setNote("ko", T.reqmail); form.email.focus(); return; }
    if (!msg) { setNote("ko", T.reqmsg); form.messaggio.focus(); return; }
    if (form.botcheck.checked) return;

    var data = {
      tipo: "contatto",
      lingua: EN ? "en" : "it",
      nome: form.name.value.trim(),
      email: email,
      telefono: form.telefono.value.trim(),
      azienda: form.azienda.value.trim(),
      reparto: form.reparto.value.trim(),
      messaggio: msg
    };

    btn.disabled = true; btn.textContent = T.sending; setNote("", "");
    fetch(ENDPOINT, {
      method: "POST", mode: "no-cors",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify(data)
    }).then(function () {
      btn.disabled = false; btn.textContent = T.send;
      form.reset(); setNote("ok", T.ok);
    }).catch(function () {
      btn.disabled = false; btn.textContent = T.send; setNote("ko", T.err);
    });
  });
})();

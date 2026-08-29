var CABRU_EMAIL = 'info@cabru.it';
var CABRU_NAME = 'CABRU s.a.s.';
var CABRU_FROM = 'clienti@cabru.it';
// Logo SENZA payoff: sotto, in testo, il payoff c'e' gia'.
// Il file e' 696x120 e viene dichiarato a 232x40 (3x, per gli schermi ad alta densita').
// Da cambiare quando il sito passa sul dominio: https://www.cabru.it/img/logo-cabru-nopayoff.png
var LOGO_URL = 'https://tdrdgit.github.io/cabru.it_website/img/logo-cabru-nopayoff.png';
var LOGO_W = 232, LOGO_H = 40;

function doPost(e) {
  try {
    var d = JSON.parse(e.postData.contents);
    if (d.tipo === 'contatto') return handleContact_(d);
    return handleQuote_(d);
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

function json_(o){ return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function esc_(s){ return String(s == null ? '' : s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function nowStr_(){ return Utilities.formatDate(new Date(), 'Europe/Rome', 'yyyy-MM-dd HH:mm'); }
function newId_(p){ return p + Utilities.formatDate(new Date(), 'Europe/Rome', 'yyyyMMdd-HHmmss'); }
function send_(to, subject, html, replyTo){
  try {
    GmailApp.sendEmail(to, subject, '', { from: CABRU_FROM, name: CABRU_NAME, htmlBody: html, replyTo: replyTo || CABRU_EMAIL });
  } catch (e) {
    MailApp.sendEmail({ to: to, name: CABRU_NAME, subject: subject, htmlBody: html, replyTo: replyTo || CABRU_EMAIL });
  }
}

function shell_(inner, en){
  // Larghezza E altezza vanno dichiarate tutte e due, in attributo e in stile:
  // con la sola altezza Apple Mail allarga l'immagine a tutta la colonna e la deforma.
  var payoff = en ? 'Laboratory, industry and research products'
                  : 'Prodotti per laboratorio, industria e ricerca';
  return '<div style="font-family:Arial,Helvetica,sans-serif;max-width:600px;margin:0 auto;color:#23262b;border:1px solid #e6eaed;border-radius:12px;overflow:hidden">'+
    '<div style="background:#ffffff;padding:20px 24px;border-bottom:2px solid #0f80a8;text-align:center">'+
    '<img src="'+LOGO_URL+'" alt="CABRU s.a.s." width="'+LOGO_W+'" height="'+LOGO_H+'" '+
    'style="width:'+LOGO_W+'px;height:'+LOGO_H+'px;display:block;margin:0 auto;border:0;outline:none;text-decoration:none">'+
    '<div style="font-size:11px;letter-spacing:1px;color:#6b7178;margin-top:8px">'+payoff+'</div></div>'+
    '<div style="padding:22px 24px">'+ inner +'</div>'+
    '<div style="background:#f5f7f8;padding:14px 24px;font-size:11px;color:#6b7178;line-height:1.6;border-top:1px solid #e6eaed">'+
    '<b style="color:#23262b">CABRU s.a.s.</b> · Via Enrico Forlanini 52, 20862 Arcore (MB)<br>Tel. 039 6013988 · info@cabru.it · www.cabru.it</div></div>';
}
function kicker_(txt){ return '<div style="font-size:11px;font-weight:bold;letter-spacing:1px;text-transform:uppercase;color:#0f80a8;margin:18px 0 8px">'+txt+'</div>'; }
function dataTable_(pairs){
  var r='';
  for (var i=0;i<pairs.length;i++){ if(!pairs[i][1]) continue;
    r += '<tr><td style="padding:3px 0;width:140px;color:#6b7178">'+pairs[i][0]+'</td><td style="padding:3px 0;color:#42474d">'+esc_(pairs[i][1])+'</td></tr>'; }
  return '<table style="width:100%;border-collapse:collapse;font-size:13px">'+r+'</table>';
}

function prodTable_(d, en) {
  if (!d.items || !d.items.length) {
    return '<table style="width:100%;border-collapse:collapse;font-size:13px"><tr><td style="padding:8px;white-space:pre-line">'+esc_(d.prodotti)+'</td></tr></table>';
  }
  var rows = '';
  for (var i=0;i<d.items.length;i++){ var it=d.items[i];
    var l1 = '<b style="font-family:monospace;color:#23262b">'+esc_(it.code)+'</b> &nbsp; <b style="color:#23262b">'+esc_(it.name)+'</b>'+
      (it.company ? ' <span style="color:#6b7178">&middot; '+esc_(it.company)+'</span>' : '')+
      (it.pkg ? ' <span style="color:#6b7178">&middot; '+(en?'Pack':'Conf.')+': '+esc_(it.pkg)+'</span>' : '');
    var l2 = '<span style="color:#42474d">'+(en?'Qty':'Q.ta richiesta')+': <b style="color:#23262b">'+esc_(it.qty)+'</b></span>'+
      (it.desc ? ' <span style="color:#6b7178">&middot; '+esc_(it.desc)+'</span>' : '');
    rows += '<tr><td style="padding:10px 4px;border-bottom:1px solid #eef1f3">'+
      '<div style="font-size:14px;line-height:1.4">'+l1+'</div>'+
      '<div style="font-size:12px;line-height:1.4;margin-top:4px">'+l2+'</div></td></tr>';
  }
  return '<table style="width:100%;border-collapse:collapse">'+rows+'</table>';
}

function handleQuote_(d) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName('Richieste') || ss.getSheets()[0];
  var id = newId_('CB-');
  var en = String(d.lingua || '').toLowerCase().indexOf('en') === 0;
  sh.appendRow([ id, nowStr_(), d.lingua||'', d.nome||'', d.email||'', d.telefono||'',
    d.azienda||'', d.reparto||'', d.numProdotti||'', d.prodotti||'', d.note||'', 'New' ]);

  var contact = [['Nome',d.nome],['Email',d.email],['Telefono',d.telefono],['Azienda / Ente',d.azienda],['Reparto',d.reparto],['Note',d.note]];
  var contactEn = [['Name',d.nome],['Email',d.email],['Phone',d.telefono],['Company / Institution',d.azienda],['Department',d.reparto]];

  send_(CABRU_EMAIL, 'Nuova richiesta di quotazione — ' + id,
    shell_(kicker_('Richiesta di quotazione — '+id)+prodTable_(d,false)+kicker_('Contatto')+dataTable_(contact)),
    d.email || CABRU_EMAIL);

  if (d.email && d.email.indexOf('@') > 0) {
    var t = en ? {subj:'CABRU — Your quotation request', greet:'Dear', fb:'Customer',
      intro:'we have received your quotation request. Thank you: we will get back to you with availability, lead times and a quote as soon as possible, through a single point of contact. A summary of your request is below.',
      prod:'Requested products', your:'Your details',
      note:'This is an automatic acknowledgement of receipt (ref. '+id+'). To add products or change the request, simply reply to this email or write to info@cabru.it.'}
    : {subj:'CABRU — Conferma della richiesta di quotazione', greet:'Gentile', fb:'Cliente',
      intro:'abbiamo ricevuto la sua richiesta di quotazione. La ringraziamo: verrà riscontrata con disponibilità, tempi e preventivo nel più breve tempo possibile, con un unico referente. Di seguito il riepilogo di quanto richiesto.',
      prod:'Prodotti richiesti', your:'I suoi dati',
      note:'Questa è una conferma automatica dell\'avvenuta ricezione (rif. '+id+'). Per aggiungere prodotti o modificare la richiesta è sufficiente rispondere a questa email o scrivere a info@cabru.it.'};
    var inner = '<p style="margin:0 0 12px;font-size:15px">'+t.greet+' '+esc_(d.nome||t.fb)+',</p>'+
      '<p style="margin:0 0 18px;font-size:14px;line-height:1.6;color:#42474d">'+t.intro+'</p>'+
      kicker_(t.prod)+prodTable_(d,en)+
      kicker_(t.your)+dataTable_(en?contactEn:contact.slice(0,5))+
      '<p style="margin:20px 0 0;font-size:12px;line-height:1.6;color:#6b7178;border-top:1px solid #eef1f3;padding-top:14px">'+t.note+'</p>';
    send_(d.email, t.subj, shell_(inner, en), CABRU_EMAIL);
  }
  return json_({ ok: true, id: id });
}

function handleContact_(d) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName('Contatti');
  if (!sh) { sh = ss.insertSheet('Contatti'); sh.appendRow(['Request ID','Date/Time (Europe/Rome)','Language','Name','Email','Phone','Company / Institution','Department','Message','Status']); }
  var id = newId_('CT-');
  var en = String(d.lingua || '').toLowerCase().indexOf('en') === 0;
  sh.appendRow([ id, nowStr_(), d.lingua||'', d.nome||'', d.email||'', d.telefono||'', d.azienda||'', d.reparto||'', d.messaggio||'', 'New' ]);

  var contact = [['Nome',d.nome],['Email',d.email],['Telefono',d.telefono],['Azienda / Ente',d.azienda],['Reparto',d.reparto]];
  var contactEn = [['Name',d.nome],['Email',d.email],['Phone',d.telefono],['Company / Institution',d.azienda],['Department',d.reparto]];
  var msgHtml = '<div style="background:#f5f8fa;border-radius:8px;padding:12px 14px;font-size:14px;color:#23262b;white-space:pre-line">'+esc_(d.messaggio)+'</div>';

  send_(CABRU_EMAIL, 'Nuovo messaggio dal sito — ' + id,
    shell_(kicker_('Messaggio dal sito — '+id)+msgHtml+kicker_('Contatto')+dataTable_(contact)),
    d.email || CABRU_EMAIL);

  if (d.email && d.email.indexOf('@') > 0) {
    var t = en ? {subj:'CABRU — We received your message', greet:'Dear', fb:'Customer',
      intro:'thank you for contacting us. We have received your message and will get back to you as soon as possible.',
      msg:'Your message', your:'Your details',
      note:'This is an automatic acknowledgement of receipt (ref. '+id+'). You can reply to this email to add anything.'}
    : {subj:'CABRU — Abbiamo ricevuto il suo messaggio', greet:'Gentile', fb:'Cliente',
      intro:'grazie per averci contattato. Abbiamo ricevuto il suo messaggio e le risponderemo nel più breve tempo possibile.',
      msg:'Il suo messaggio', your:'I suoi dati',
      note:'Questa è una conferma automatica dell\'avvenuta ricezione (rif. '+id+'). Può rispondere a questa email per aggiungere altro.'};
    var inner = '<p style="margin:0 0 12px;font-size:15px">'+t.greet+' '+esc_(d.nome||t.fb)+',</p>'+
      '<p style="margin:0 0 18px;font-size:14px;line-height:1.6;color:#42474d">'+t.intro+'</p>'+
      kicker_(t.msg)+msgHtml+
      kicker_(t.your)+dataTable_(en?contactEn:contact)+
      '<p style="margin:20px 0 0;font-size:12px;line-height:1.6;color:#6b7178;border-top:1px solid #eef1f3;padding-top:14px">'+t.note+'</p>';
    send_(d.email, t.subj, shell_(inner, en), CABRU_EMAIL);
  }
  return json_({ ok: true, id: id });
}

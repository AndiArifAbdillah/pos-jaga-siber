// Dashboard operator Pos Jaga Siber.
// Setiap 2 detik meminta /api/status ke kotak, lalu menggambar ulang layar.
// Tombol mengirim POST ke /api/insiden/<id>/<aksi> dengan kepala X-PJS: 1.
"use strict";

const state = { data: null, selected: null, detailKey: "", operator: "", busy: false };
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const SEV = { kritis: "Kritis", tinggi: "Tinggi", sedang: "Sedang", rendah: "Rendah" };
const SEV_ORDER = { kritis: 0, tinggi: 1, sedang: 2, rendah: 3 };
const ZONE = { ot: "Peralatan", it: "Kantor", other: "Internal lain" };

function hhmm(ts) {
  if (!ts) return "-";
  return new Date(ts * 1000).toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" });
}

function dateTime(ts) {
  if (!ts) return "-";
  return new Date(ts * 1000).toLocaleString("id-ID", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

// --- nama operator (diingat di browser ini saja) ---------------------------
function loadOperator(fallback) {
  let saved = "";
  try { saved = localStorage.getItem("pjs-operator") || ""; } catch (e) { /* penyimpanan browser tidak tersedia */ }
  state.operator = saved || fallback;
  $("operator").value = state.operator;
}

$("operator").addEventListener("input", (ev) => {
  state.operator = ev.target.value.trim();
  try { localStorage.setItem("pjs-operator", state.operator); } catch (e) { /* abaikan */ }
});

// --- mengambil data --------------------------------------------------------
async function load() {
  try {
    const res = await fetch("/api/status", { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    const first = state.data === null;
    state.data = await res.json();
    if (first) loadOperator(state.data.box.operator);
    state.offline = false;
    render();
  } catch (e) {
    state.offline = true;
    renderBanner();
  }
}

async function post(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-PJS": "1" },
    body: JSON.stringify({ ...body, operator: state.operator }),
  });
  return res.json();
}

async function act(id, action, body = {}) {
  if (state.busy) return;
  state.busy = true;
  try {
    const result = await post(`/api/insiden/${encodeURIComponent(id)}/${action}`, body);
    toast(result.message || (result.ok ? "Selesai." : "Gagal."));
  } catch (e) {
    toast("Kotak tidak bisa dihubungi.");
  } finally {
    state.busy = false;
    state.detailKey = "";
    await load();
  }
}

let toastTimer = null;
function toast(text) {
  const el = $("toast");
  el.textContent = text;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 3500);
}

// --- menggambar ------------------------------------------------------------
function sortIncidents(list) {
  const open = (i) => (i.status === "menunggu" ? 0 : i.status === "diisolasi" ? 1 : 2);
  return [...list].sort((a, b) =>
    open(a) - open(b) || SEV_ORDER[a.severity] - SEV_ORDER[b.severity] || b.last_seen - a.last_seen);
}

function render() {
  const d = state.data;
  $("unit").textContent = `${d.box.name} · ${d.box.unit}`;
  renderBanner();
  renderChips();
  renderTiles();
  renderList();
  renderDetail();
  renderDevices();
  renderEvidence();
}

function renderBanner() {
  const banner = $("banner");
  const integrity = state.data && state.data.evidence.integrity;
  if (state.offline) {
    banner.textContent = "Dashboard terputus dari kotak. Mencoba menyambung lagi...";
    banner.hidden = false;
  } else if (integrity && !integrity.ok) {
    banner.textContent = `Catatan bukti rusak: ${integrity.message} Jangan matikan kotak dan segera laporkan ke atasan.`;
    banner.hidden = false;
  } else {
    banner.hidden = true;
  }
  const learning = $("learning");
  if (state.data && state.data.learning.active) {
    learning.textContent = `Masa belajar sampai ${dateTime(state.data.learning.until)}: kotak sedang mengenali perangkat yang normal. Perangkat baru dicatat diam-diam dan belum dilaporkan.`;
    learning.hidden = false;
  } else {
    learning.hidden = true;
  }
}

function setChip(id, text, kind) {
  const el = $(id);
  el.textContent = text;
  el.className = "chip" + (kind ? ` chip-${kind}` : "");
}

function renderChips() {
  const d = state.data;
  const integrity = d.evidence.integrity;
  setChip("chip-bukti", integrity.ok ? "Catatan bukti utuh" : "Catatan bukti PUTUS", integrity.ok ? "ok" : "crit");
  setChip("chip-blokir", d.links.blokir === "mikrotik" ? "Blokir: MikroTik" : "Blokir: mode uji", d.links.blokir === "mikrotik" ? "ok" : "warn");
  const ai = {
    siap: [`AI lokal: siap (${d.links.ai_model})`, "ok"],
    mati: ["AI: penjelasan bawaan", ""],
    tidak_tersambung: ["AI lokal: tidak tersambung", "warn"],
    memeriksa: ["AI lokal: memeriksa", ""],
  }[d.links.ai] || [`AI: ${d.links.ai}`, ""];
  setChip("chip-ai", ai[0], ai[1]);

  const p = d.links.perilaku || { state: "mati" };
  const zones = (p.zones || []).map((z) => (z === "ot" ? "peralatan" : "kantor")).join(", ");
  const samples = p.samples ? (p.samples.ot || 0) + (p.samples.it || 0) : 0;
  const perilaku = {
    aktif: [`AI perilaku: aktif (${zones})`, "ok"],
    belajar: [`AI perilaku: belajar (${samples} contoh)`, ""],
    kurang_data: ["AI perilaku: contoh normal belum cukup", "warn"],
    mati: ["AI perilaku: mati", ""],
  }[p.state] || ["AI perilaku: -", ""];
  setChip("chip-perilaku", perilaku[0], perilaku[1]);
  $("asst-mode").textContent = d.links.ai === "siap" ? `model ${d.links.ai_model}` : "tanpa AI: mode pencarian";
}

function renderTiles() {
  const d = state.data;
  const waiting = d.incidents.filter((i) => i.status === "menunggu");
  const crit = waiting.filter((i) => i.severity === "kritis").length;
  const high = waiting.filter((i) => i.severity === "tinggi").length;
  $("need-count").textContent = waiting.length;
  $("need-sub").textContent = waiting.length ? `${crit} kritis · ${high} tinggi · ${waiting.length - crit - high} lainnya` : "Tidak ada yang menunggu";
  $("tile-need").className = "tile" + (crit ? " hot-crit" : waiting.length ? " hot-high" : "");

  const isolated = d.incidents.filter((i) => i.status === "diisolasi");
  const auto = isolated.filter((i) => i.isolated_by === "otomatis").length;
  $("iso-count").textContent = isolated.length;
  $("iso-sub").textContent = isolated.length ? `${auto} otomatis · ${isolated.length - auto} oleh operator` : "Tidak ada";

  const ot = d.devices.filter((x) => x.zone === "ot").length;
  const fresh = d.devices.filter((x) => x.source === "baru").length;
  $("dev-count").textContent = d.devices.length;
  $("dev-sub").textContent = `${ot} peralatan · ${d.devices.length - ot} komputer` + (fresh ? ` · ${fresh} baru` : "");

  const ev = d.evidence;
  $("ev-count").textContent = ev.count;
  $("ev-sub").textContent = ev.integrity.ok ? "Rantai utuh" : `Rantai putus di #${ev.integrity.broken_at}`;
  $("tile-ev").className = "tile" + (ev.integrity.ok ? "" : " hot-crit");
}

function statusText(i) {
  if (i.status === "diisolasi") {
    const who = i.isolated_by === "otomatis" ? "otomatis" : "oleh operator";
    const mode = i.isolation_mode === "uji" ? " (mode uji)" : "";
    return `Diisolasi ${who} ${hhmm(i.isolated_at)}${mode}`;
  }
  return { menunggu: "Menunggu keputusan", dilepas: "Isolasi dilepas", bukan_ancaman: "Bukan ancaman" }[i.status] || i.status;
}

function renderList() {
  const list = sortIncidents(state.data.incidents);
  if (!state.selected || !list.some((i) => i.id === state.selected)) {
    state.selected = list.length ? list[0].id : null;
  }
  $("list-meta").textContent = list.length ? `${list.length} tercatat` : "";
  if (!list.length) {
    $("incident-list").innerHTML = `<div class="empty">Belum ada kejadian.<br>Kotak sedang berjaga.</div>`;
    return;
  }
  $("incident-list").innerHTML = list.map((i) => `
    <button type="button" class="inc sev-${esc(i.severity)}${i.id === state.selected ? " selected" : ""}${["dilepas", "bukan_ancaman"].includes(i.status) ? " done" : ""}" data-id="${esc(i.id)}">
      <span class="inc-top"><span>${esc(i.id)} · ${esc(SEV[i.severity] || i.severity)}</span><span>${hhmm(i.last_seen)}${i.count > 1 ? ` · ${i.count}x` : ""}</span></span>
      <span class="inc-title">${esc(i.title)}</span>
      <span class="inc-status">${esc(statusText(i))}</span>
    </button>`).join("");
}

$("incident-list").addEventListener("click", (ev) => {
  const btn = ev.target.closest(".inc");
  if (!btn) return;
  state.selected = btn.dataset.id;
  state.detailKey = "";
  renderList();
  renderDetail();
});

function party(label, p) {
  if (!p || !p.ip) {
    return `<div class="party"><div class="p-label">${label}</div><div class="p-name">-</div></div>`;
  }
  const zone = ZONE[p.zone] || "Luar markas";
  return `<div class="party${p.isolated ? " iso" : ""}">
    <div class="p-label">${label}</div>
    <div class="p-name">${esc(p.name)}</div>
    <div class="p-meta">${esc(p.ip)} · ${esc(zone)}${p.isolated ? " · DIISOLASI" : ""}</div>
  </div>`;
}

function explanationSource(exp) {
  if (exp.source === "ai") return [`Disusun AI lokal (${esc(exp.model)})`, "ai"];
  if (exp.pending) return ["AI sedang menyusun penjelasan...", "pending"];
  if (exp.error) return ["Penjelasan bawaan (AI tidak tersedia)", ""];
  return ["Penjelasan bawaan", ""];
}

function renderDetail() {
  const el = $("detail");
  const inc = state.data.incidents.find((i) => i.id === state.selected);
  if (!inc) {
    el.innerHTML = `<div class="empty">Pilih kejadian di daftar untuk melihat penjelasannya.</div>`;
    state.detailKey = "";
    return;
  }
  const key = JSON.stringify(inc);
  if (key === state.detailKey) return;  // tidak berubah: jangan ganggu petugas yang sedang membaca
  state.detailKey = key;

  const exp = inc.explanation || {};
  const [srcText, srcClass] = explanationSource(exp);
  const steps = inc.steps.map((s, n) => `
    <li><label><input type="checkbox" data-step="${n}"${s.checked ? " checked" : ""}>
    <span class="${s.checked ? "done-step" : ""}">${esc(s.text)}</span></label></li>`).join("");

  const buttons = [];
  if (inc.status === "menunggu" || inc.status === "dilepas") {
    buttons.push(`<button class="btn btn-danger" data-act="isolasi" type="button">Isolasi perangkat</button>`);
    buttons.push(`<button class="btn" data-act="bukan-ancaman" type="button">Bukan ancaman</button>`);
  }
  if (inc.status === "diisolasi") {
    buttons.push(`<button class="btn" data-act="lepas" type="button">Batalkan isolasi</button>`);
  }
  if (inc.status === "bukan_ancaman") {
    buttons.push(`<button class="btn" data-act="buka-lagi" type="button">Buka lagi</button>`);
  }
  const reportUrl = `/laporan/${encodeURIComponent(inc.id)}?operator=${encodeURIComponent(state.operator)}`;
  buttons.push(`<a class="btn btn-primary" href="${reportUrl}" target="_blank" rel="noopener">Buat laporan</a>`);

  const facts = [`Terjadi ${inc.count} kali`, `pertama ${hhmm(inc.first_seen)}`, `terakhir ${hhmm(inc.last_seen)}`];
  if (inc.facts && inc.facts.interval_s) facts.push(`jarak rata-rata ${inc.facts.interval_s} detik`);

  let ml = "";
  if (inc.facts && inc.facts.ml_score != null) {
    const score = Number(inc.facts.ml_score);
    ml = `<div class="ml">
      <div class="ml-head"><span>AI deteksi perilaku</span><span>skor keanehan ${esc(score.toFixed(2).replace(".", ","))} dari 1</span></div>
      <div class="ml-bar"><span class="${score >= 0.72 ? "hot" : ""}" style="width:${Math.round(Math.min(score, 1) * 100)}%"></span></div>
      <div class="ml-text">Perangkat ${esc(inc.facts.ml_reason)}.</div>
    </div>`;
  }

  el.innerHTML = `
    <div class="d-head">
      <span class="pill sev-${esc(inc.severity)}">${esc(SEV[inc.severity] || inc.severity)}</span>
      <span class="d-id">${esc(inc.id)}</span>
      <span class="d-status${inc.status === "diisolasi" ? " is-iso" : ""}">${esc(statusText(inc))}</span>
    </div>
    <h3 class="d-title">${esc(inc.title)}</h3>
    <div class="route">${party("DARI", inc.src)}<div class="arrow" aria-hidden="true">&rarr;</div>${party("KE", inc.dst)}</div>
    <div class="facts">${esc(facts.join(" · "))}</div>
    ${inc.note ? `<div class="note">${esc(inc.note)}</div>` : ""}
    ${ml}
    <div class="ai-card">
      <div class="ai-head"><h2>Penjelasan</h2><span class="ai-src ${srcClass}">${srcText}</span></div>
      <div class="ai-block"><div class="ai-label">Apa yang terjadi</div><div>${esc(exp.what)}</div></div>
      <div class="ai-block"><div class="ai-label">Kenapa berbahaya</div><div>${esc(exp.why)}</div></div>
      <div class="ai-block"><div class="ai-label">Langkah (SOP)</div><ul class="steps">${steps}</ul></div>
    </div>
    <div class="actions">${buttons.join("")}</div>`;
}

$("detail").addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-act]");
  if (!btn || !state.selected) return;
  const inc = state.data.incidents.find((i) => i.id === state.selected);
  if (btn.dataset.act === "isolasi" && inc) {
    const ok = window.confirm(`Isolasi ${inc.src.name}?\nPerangkat ini tidak bisa memakai jaringan sampai isolasi dibatalkan atau batas waktunya habis.`);
    if (!ok) return;
  }
  btn.disabled = true;
  act(state.selected, btn.dataset.act);
});

$("detail").addEventListener("change", (ev) => {
  const box = ev.target.closest("input[data-step]");
  if (!box || !state.selected) return;
  act(state.selected, "langkah", { index: Number(box.dataset.step), checked: box.checked });
});

function renderDevices() {
  const devices = state.data.devices;
  const row = (x) => {
    const dot = x.isolated ? "dot-iso" : x.source === "baru" ? "dot-new" : !x.last_seen ? "dot-idle" : "";
    const seen = x.last_seen ? `terlihat ${hhmm(x.last_seen)}` : "belum terlihat";
    const meta = [x.ip, x.vendor, seen].filter(Boolean).join(" · ");
    const tag = x.isolated ? `<span class="tag">DIISOLASI</span>` : x.source === "baru" ? `<span class="tag tag-new">BARU</span>` : "";
    return `<li class="dev"><span class="dot ${dot}"></span><div class="dev-body"><div class="dev-name">${esc(x.name)}</div><div class="dev-meta">${esc(meta)}</div></div>${tag}</li>`;
  };
  const ot = devices.filter((x) => x.zone === "ot");
  const it = devices.filter((x) => x.zone !== "ot");
  $("dev-ot").innerHTML = ot.map(row).join("") || `<li class="muted">Belum ada.</li>`;
  $("dev-it").innerHTML = it.map(row).join("") || `<li class="muted">Belum ada.</li>`;
  $("ot-meta").textContent = `${ot.length} perangkat`;
  $("it-meta").textContent = `${it.length} perangkat`;
}

function renderEvidence() {
  const ev = state.data.evidence;
  $("book-code").textContent = ev.code;
  const integrity = $("integrity");
  const checked = ev.integrity.checked_at ? ` Diperiksa ${hhmm(ev.integrity.checked_at)}.` : "";
  integrity.textContent = ev.integrity.message + checked;
  integrity.className = "integrity " + (ev.integrity.ok ? "ok" : "broken");
  $("entries").innerHTML = ev.recent.map((e) => {
    const time = (e.time || "").slice(11, 16);
    return `<li><span class="seq">#${e.seq}</span><span>${esc(time)} ${esc(e.text)}</span></li>`;
  }).join("");
}

$("btn-check").addEventListener("click", async () => {
  const btn = $("btn-check");
  btn.disabled = true;
  try {
    const result = await post("/api/bukti/periksa", {});
    toast(result.integrity.ok ? "Rantai utuh. Tidak ada catatan yang diubah." : `Rantai PUTUS: ${result.integrity.message}`);
  } catch (e) {
    toast("Kotak tidak bisa dihubungi.");
  } finally {
    btn.disabled = false;
    await load();
  }
});

// --- asisten piket --------------------------------------------------------
async function askAssistant(question) {
  const btn = $("ask-btn");
  const box = $("ask-answer");
  btn.disabled = true;
  box.hidden = false;
  box.innerHTML = `<div class="mode">Asisten sedang mencari jawaban di catatan kotak...</div>`;
  try {
    const r = await post("/api/asisten/tanya", { pertanyaan: question });
    if (!r.ok) {
      box.innerHTML = `<div class="mode">${esc(r.message)}</div>`;
      return;
    }
    const mode = r.mode === "ai"
      ? `Dijawab AI lokal (${esc(r.model)}) hanya dari catatan kotak`
      : "AI lokal belum tersambung: ini hasil pencarian di catatan kotak";
    const src = r.sources.length
      ? `<div class="src">Sumber: ${r.sources.map((s) => `<button type="button" data-id="${esc(s)}">${esc(s)}</button>`).join("")}</div>`
      : "";
    box.innerHTML = `<div class="mode">${mode}</div><div>${esc(r.answer)}</div>${src}`;
  } catch (e) {
    box.innerHTML = `<div class="mode">Kotak tidak bisa dihubungi.</div>`;
  } finally {
    btn.disabled = false;
  }
}

$("ask-form").addEventListener("submit", (ev) => {
  ev.preventDefault();
  const question = $("ask-input").value.trim();
  if (question) askAssistant(question);
});

$("ask-examples").addEventListener("click", (ev) => {
  const btn = ev.target.closest(".example");
  if (!btn) return;
  $("ask-input").value = btn.textContent;
  askAssistant(btn.textContent);
});

$("ask-answer").addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-id]");
  if (!btn) return;
  state.selected = btn.dataset.id;
  state.detailKey = "";
  renderList();
  renderDetail();
  $("detail").scrollIntoView({ behavior: "smooth", block: "start" });
});

$("btn-report").addEventListener("click", async () => {
  const btn = $("btn-report");
  btn.disabled = true;
  btn.textContent = "Menyusun...";
  try {
    const r = await post("/api/asisten/laporan-piket", { jam: Number($("report-hours").value) });
    $("report-text").textContent = r.text;
    $("report-text").hidden = false;
    $("btn-copy").hidden = false;
    toast(r.mode === "ai" ? "Laporan selesai. Ringkasan disusun AI lokal." : "Laporan selesai (ringkasan bawaan).");
  } catch (e) {
    toast("Kotak tidak bisa dihubungi.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Buat laporan";
    load();
  }
});

$("btn-copy").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText($("report-text").textContent);
    toast("Laporan disalin. Tempel ke buku jaga atau pesan.");
  } catch (e) {
    const range = document.createRange();
    range.selectNodeContents($("report-text"));
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    toast("Teks sudah dipilih. Tekan Ctrl+C untuk menyalin.");
  }
});

function tick() {
  $("clock").textContent = new Date().toLocaleString("id-ID", {
    weekday: "short", day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

tick();
setInterval(tick, 1000);
load();
setInterval(load, 2000);

/* Adjudicaciones Secundaria Canarias 2026/27 — buscador de destinos provisionales */
"use strict";

const PER_PAGE = 50;
const ISLA_NOMBRE = { TF: "Tenerife", GC: "Gran Canaria", LZ: "Lanzarote", FU: "Fuerteventura", LP: "La Palma", GO: "La Gomera", HI: "El Hierro" };

let DATOS = [];
let filtrados = [];
let pagina = 1;

const $ = (id) => document.getElementById(id);
const elQ = $("q"), elClear = $("clearBtn");
const elEsp = $("fEspecialidad"), elIsla = $("fIsla"), elCat = $("fCategoria");
const elConDestino = $("fConDestino"), elNoObtiene = $("fNoObtiene");
const elStats = $("stats"), elLoading = $("loading"), elResults = $("results"), elPaginacion = $("pagination");

function normaliza(s) {
  return (s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/* ---------- carga de datos ---------- */
async function cargarDatos() {
  elLoading.hidden = false;
  elLoading.innerHTML = 'Cargando datos… <span class="bar"><i id="barFill"></i></span>';
  const bar = document.getElementById("barFill");
  try {
    const res = await fetch("data/registros.json");
    if (!res.ok) throw new Error("HTTP " + res.status);
    const reader = res.body.getReader();
    const len = Number(res.headers.get("Content-Length")) || 0;
    const chunks = [];
    let recibido = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      recibido += value.length;
      if (len && bar) bar.style.width = Math.min(100, (recibido / len) * 100) + "%";
    }
    const blob = new Blob(chunks, { type: "application/json" });
    DATOS = JSON.parse(await blob.text());
  } catch (e) {
    elLoading.innerHTML = "No se pudieron cargar los datos (" + esc(e.message) + "). Comprueba que data/registros.json existe.";
    return;
  }
  elLoading.hidden = true;
  rellenarFiltros();
  aplicar();
}

/* ---------- filtros ---------- */
function rellenarFiltros() {
  const esp = new Set(), isla = new Set(), cat = new Set();
  for (const r of DATOS) {
    if (r.especialidad) esp.add(r.especialidad);
    const d = r.destino;
    if (d && d.isla) isla.add(d.isla);
    if (r.categoria) cat.add(r.categoria);
  }
  for (const [sel, set] of [[elEsp, esp], [elIsla, isla], [elCat, cat]]) {
    for (const v of [...set].sort((a, b) => a.localeCompare(b, "es"))) {
      const opt = document.createElement("option");
      opt.value = v;
      opt.textContent = sel === elIsla && ISLA_NOMBRE[v] ? v + " — " + ISLA_NOMBRE[v] : v;
      sel.appendChild(opt);
    }
  }
}

function filtrar() {
  const q = normaliza(elQ.value);
  const esp = elEsp.value, isla = elIsla.value, cat = elCat.value;
  const soloDestino = elConDestino.checked, soloNoObtiene = elNoObtiene.checked;
  filtrados = DATOS.filter((r) => {
    if (q && !r._q.includes(q)) return false;
    if (esp && r.especialidad !== esp) return false;
    if (cat && r.categoria !== cat) return false;
    if (isla) {
      const di = (r.destino && r.destino.isla) || "";
      const ev = r.ext_vigencia && r.ext_vigencia.isla ? r.ext_vigencia.isla : "";
      if (di !== isla && ev !== isla) return false;
    }
    if (soloDestino && (!r.destino || !r.destino.codigo_centro)) return false;
    if (soloNoObtiene && !r.no_obtiene) return false;
    return true;
  });
  pagina = 1;
  render();
}

function aplicar() {
  filtrar();
  elStats.innerHTML = "<b>" + filtrados.length.toLocaleString("es-ES") + "</b> resultado(s) de " + DATOS.length.toLocaleString("es-ES") + " registros";
}

/* ---------- render ---------- */
function tarjeta(r) {
  const d = r.destino || {};
  const clase = r.no_obtiene ? "card no-obtiene" : (d && d.codigo_centro) ? "card" : "card no-destino";
  const badges = [];
  if (r.no_obtiene) badges.push('<span class="badge no-obtiene">Sin vacante</span>');
  if (d.programas) badges.push('<span class="badge programa">' + esc(d.programas) + "</span>");
  if (r.comparte_con && r.comparte_con.length) badges.push('<span class="badge comparte">Comparte destino</span>');
  if (r.articulo) badges.push('<span class="badge articulo">Art. 13.3</span>');

  const meta = [];
  if (r.categoria) meta.push("<span><b>Categoría:</b> " + esc(r.categoria) + "</span>");
  if (r.ambito) meta.push("<span><b>Ámbito:</b> " + esc(r.ambito) + (r.ambito_preferente ? " · pref. " + esc(r.ambito_preferente) : "") + "</span>");
  if (r.tipos_plaza && r.tipos_plaza.length) meta.push("<span><b>Participa:</b> " + esc(r.tipos_plaza.join(", ")) + "</span>");
  if (r.tipo_comision) meta.push("<span><b>Comisión:</b> " + esc(r.tipo_comision.replace("Tipo comisión: ", "")) + "</span>");
  meta.push("<span><b>Orden:</b> " + r.orden + "</span>");

  let destinoHtml = "";
  if (r.no_obtiene) {
    destinoHtml = '<div class="destino-block sin-vacante">No obtiene por no existir vacante en los centros solicitados</div>';
  } else if (d.codigo_centro) {
    const origen = d.colectivo_origen ? " · obtenido vía colectivo " + d.colectivo_origen : "";
    destinoHtml = '<div class="destino-block"><span class="centro">' + esc(d.centro) + "</span>" +
      '<span class="badge programa">' + esc(d.codigo_centro) + "</span>" +
      '<div class="detalle">' + esc(d.municipio) + " (" + esc(ISLA_NOMBRE[d.isla] || d.isla) + ")" +
      " · " + esc(d.codigo_especialidad) + " " + esc(d.especialidad) + origen + "</div></div>";
  } else {
    destinoHtml = '<div class="destino-block sin-vacante">Sin destino asignado</div>';
  }

  let extHtml = "";
  if (r.ext_vigencia && r.ext_vigencia.codigo_centro) {
    extHtml = '<div class="destino-block" style="background:#f8fafc"><b>Ext. vigencia:</b> ' + esc(r.ext_vigencia.centro) +
      " (" + esc(r.ext_vigencia.municipio) + ", " + esc(r.ext_vigencia.isla) + ") — " + esc(r.ext_vigencia.especialidad) + "</div>";
  }

  let comparteHtml = "";
  if (r.comparte_con && r.comparte_con.length) {
    comparteHtml = '<div class="destino-block" style="background:#f8fafc"><b>Comparte con:</b> ' +
      r.comparte_con.map((c) => esc(c.centro || c.completo || "")).join(" · ") + "</div>";
  }

  return '<article class="' + clase + '">' +
    '<div class="head"><span class="nombre">' + esc(r.nombre) + "</span>" +
    '<span class="dni">' + esc(r.dni) + "</span>" + badges.join("") +
    '<span class="especialidad">' + esc(r.especialidad) + "</span></div>" +
    '<div class="meta">' + meta.join("") + "</div>" +
    destinoHtml + extHtml + comparteHtml +
    "</article>";
}

function render() {
  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / PER_PAGE));
  if (pagina > totalPaginas) pagina = totalPaginas;
  const desde = (pagina - 1) * PER_PAGE;
  const trozo = filtrados.slice(desde, desde + PER_PAGE);
  if (!filtrados.length) {
    elResults.hidden = false;
    elResults.innerHTML = '<div class="empty">Sin resultados. Prueba con otros términos o quita filtros.</div>';
  } else {
    elResults.hidden = false;
    elResults.innerHTML = trozo.map(tarjeta).join("");
  }
  renderPaginacion(totalPaginas);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function renderPaginacion(totalPaginas) {
  if (totalPaginas <= 1) { elPaginacion.hidden = true; elPaginacion.innerHTML = ""; return; }
  elPaginacion.hidden = false;
  const btns = [];
  btns.push('<button data-p="' + (pagina - 1) + '" ' + (pagina === 1 ? "disabled" : "") + ">‹ Anterior</button>");
  const ventana = [];
  for (let p = 1; p <= totalPaginas; p++) {
    if (p === 1 || p === totalPaginas || Math.abs(p - pagina) <= 2) ventana.push(p);
  }
  let prev = 0;
  for (const p of ventana) {
    if (p - prev > 1) btns.push("<span>…</span>");
    btns.push('<button data-p="' + p + '" class="' + (p === pagina ? "active" : "") + '">' + p + "</button>");
    prev = p;
  }
  btns.push('<button data-p="' + (pagina + 1) + '" ' + (pagina === totalPaginas ? "disabled" : "") + ">Siguiente ›</button>");
  elPaginacion.innerHTML = btns.join("");
}

/* ---------- eventos ---------- */
let timer = null;
elQ.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(aplicar, 120); });
elClear.addEventListener("click", () => { elQ.value = ""; aplicar(); elQ.focus(); });
elEsp.addEventListener("change", aplicar);
elIsla.addEventListener("change", aplicar);
elCat.addEventListener("change", aplicar);
elConDestino.addEventListener("change", aplicar);
elNoObtiene.addEventListener("change", aplicar);
elPaginacion.addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-p]");
  if (!btn || btn.disabled) return;
  pagina = Number(btn.dataset.p);
  render();
});

cargarDatos();

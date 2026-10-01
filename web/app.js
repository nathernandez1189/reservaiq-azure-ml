"use strict";
const $ = (id) => document.getElementById(id);
let summary,
  lastStay,
  lastResult,
  lastInputs,
  revealed = false;
let activeRecord = null,
  source = "manual",
  dirty = false,
  busy = false,
  requestId = crypto.randomUUID();
let savedRecords = [],
  savedPage = 0,
  listGeneration = 0;
let batchRows = null,
  batchResult = null,
  batchId = crypto.randomUUID(),
  batchBusy = false;
const names = {
  lead_time: "Anticipación (días)",
  arrival_month: "Mes de llegada",
  stays_in_weekend_nights: "Noches de fin de semana",
  stays_in_week_nights: "Noches entre semana",
  hotel: "Tipo de hotel",
  meal: "Alimentación",
  market_segment: "¿Cómo se originó la reserva?",
  distribution_channel: "Canal por el que se recibió",
  reserved_room_type: "Categoría de habitación",
  customer_type: "Tipo de reserva",
};
const numeric = {
  lead_time: [0, 60],
  arrival_month: [1, 12],
  stays_in_weekend_nights: [0, 15],
  stays_in_week_nights: [0, 30],
};
const categories = {
  hotel: ["City Hotel", "Resort Hotel"],
  meal: ["BB", "HB", "FB", "SC", "Undefined"],
  market_segment: [
    "Direct",
    "Corporate",
    "Online TA",
    "Offline TA/TO",
    "Complementary",
    "Groups",
    "Aviation",
  ],
  distribution_channel: ["Direct", "Corporate", "TA/TO", "GDS"],
  reserved_room_type: ["A", "B", "C", "D", "E", "F", "G", "H", "L", "P"],
  customer_type: ["Transient", "Transient-Party", "Contract", "Group"],
};
const labels = {
  "City Hotel": "Urbano",
  "Resort Hotel": "Vacacional",
  BB: "Desayuno",
  HB: "Media pensión",
  FB: "Pensión completa",
  SC: "Sin comidas",
  Undefined: "No especificado",
  Direct: "Directo",
  Corporate: "Corporativo",
  "Online TA": "Agencia en línea",
  "Offline TA/TO": "Agencia tradicional",
  Complementary: "Cortesía",
  Groups: "Grupos",
  Aviation: "Aerolínea",
  "TA/TO": "Agencia / operador",
  GDS: "Distribución global",
  Transient: "Individual",
  "Transient-Party": "Individual vinculada",
  Contract: "Contrato",
  Group: "Grupo",
};
const pct = (n) =>
  (n * 100).toLocaleString("es-CO", {
    maximumFractionDigits: 1,
    minimumFractionDigits: 1,
  }) + " %";
const number = (n) => n.toLocaleString("es-CO");
const help = {
  hotel: "Urbano: ciudad. Vacacional: resort o destino turístico.",
  meal: "BB: desayuno. HB: desayuno y otra comida. FB: tres comidas.",
  market_segment:
    "Cómo se originó la reserva: agencia, empresa, directo u otro.",
  distribution_channel:
    "Por qué canal se recibió: directo, agencia u operador.",
  reserved_room_type:
    "Código de la categoría reservada (A, B…). No es un número de habitación.",
  customer_type: "Individual, vinculada a otra reserva, grupo o contrato.",
  lead_time: "Días entre la creación de la reserva y la llegada. De 0 a 60.",
  arrival_month: "Mes previsto de llegada al hotel.",
  stays_in_weekend_nights:
    "Noches de sábado o domingo durante la estancia. De 0 a 15.",
  stays_in_week_nights:
    "Noches de lunes a viernes durante la estancia. De 0 a 30.",
};
const monthNames = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
];
const stateLabels = {
  pending: "Pendiente de revisión",
  reviewed: "Revisada",
  archived: "Archivada",
};
const sourceLabels = {
  manual: "Ingresada a mano",
  example: "Ejemplo de prueba",
  csv: "Importada de CSV",
};
const esc = (value) =>
  String(value).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
function go(id) {
  document.querySelectorAll(".view").forEach((v) => (v.hidden = v.id !== id));
  document
    .querySelectorAll("[data-view]")
    .forEach((b) =>
      b.setAttribute("aria-current", b.dataset.view === id ? "page" : "false"),
    );
  sessionStorage.setItem("reservaiq-view", id);
  window.scrollTo({ top: 0, behavior: "auto" });
  if (id === "saved") refreshSaved();
}
document
  .querySelectorAll("[data-view],[data-go]")
  .forEach((b) => (b.onclick = () => go(b.dataset.view || b.dataset.go)));
async function api(url, data) {
  let r;
  try {
    r = await fetch(
      url,
      data === undefined
        ? {}
        : {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
          },
    );
  } catch {
    throw Error(
      "No hay conexión con ReservaIQ. Mantén abierta la terminal de la aplicación y vuelve a intentar.",
    );
  }
  let d;
  try {
    d = await r.json();
  } catch {
    throw Error(
      "El servidor no devolvió una respuesta válida. Reinicia ReservaIQ.",
    );
  }
  if (!r.ok) throw Error(d.error || "No fue posible completar la operación.");
  return d;
}
const post = api;
function download(data, name) {
  const url = URL.createObjectURL(
      new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json;charset=utf-8",
      }),
    ),
    a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
const save = download;
function bars(rows, scale = 1) {
  return rows
    .map(
      (r) =>
        `<div class="barrow"><span>${esc(r.name)}</span><div class="track"><div class="fill" style="width:${Math.max(0, Math.min(1, r.value / scale)) * 100}%"></div></div><span>${(r.value * 100).toFixed(1)}</span></div>`,
    )
    .join("");
}
function inputs() {
  let d = {};
  Object.keys(names).forEach(
    (k) => (d[k] = k in numeric ? Number($(k).value) : $(k).value),
  );
  return d;
}
function buildForm() {
  let fields = "";
  for (const [k, values] of Object.entries(categories))
    fields += field(
      k,
      `<select id="${k}" aria-describedby="help-${k}">${values.map((v) => `<option value="${v}">${labels[v] || v}</option>`).join("")}</select>`,
    );
  $("form-fields").innerHTML = fields;
  $("numeric-fields").innerHTML = Object.entries(numeric)
    .map(([k, [min, max]]) =>
      field(
        k,
        k === "arrival_month"
          ? `<select id="${k}" aria-describedby="help-${k}">${monthNames.map((v, i) => `<option value="${i + 1}">${v}</option>`).join("")}</select>`
          : `<input id="${k}" type="number" min="${min}" max="${max}" step="1" required aria-describedby="help-${k}">`,
      ),
    )
    .join("");
  Object.keys(names).forEach((k) => ($(k).oninput = edited));
  $("reference").oninput = edited;
  Booking.init({ names, labels, inputs, edited });
}
function field(k, control) {
  return `<div class="field"><label for="${k}">${names[k]}</label>${control}<small id="help-${k}">${help[k]}</small></div>`;
}
function stayTotal() {
  Booking.refresh();
}
function resetResult(message = "Lista para analizar") {
  lastResult = null;
  lastInputs = null;
  lastStay = null;
  $("result-ready").hidden = true;
  $("result-empty").hidden = false;
  $("after-save").hidden = true;
  $("score").textContent = "—";
  $("decision").textContent = message;
  $("decision").style.color = "var(--text)";
  $("dial").style.background = "#283943";
  $("threshold").textContent = "";
  $("next-action").textContent =
    "Analiza la reserva para obtener una sugerencia de revisión.";
  $("export").disabled = true;
}
function edited() {
  dirty = true;
  requestId = crypto.randomUUID();
  resetResult("Cambios pendientes de analizar");
  $("save-state").textContent = activeRecord
    ? "Cambios sin guardar"
    : "Sin guardar";
  $("save-state").className = "pill amber";
  $("case-truth").textContent =
    "Escenario editado · resultado real desconocido";
  $("save-feedback").hidden = true;
  $("error").textContent = "";
  $("calculate").disabled = false;
  stayTotal();
}
function mayReplace() {
  return (
    !dirty ||
    confirm(
      "Hay cambios sin guardar. ¿Quieres descartarlos y abrir otra reserva?",
    )
  );
}
function newReservation(navigate = true) {
  if (busy || (navigate && !mayReplace())) return;
  activeRecord = null;
  source = "manual";
  dirty = false;
  requestId = crypto.randomUUID();
  const defaults = {
    hotel: "City Hotel",
    meal: "BB",
    market_segment: "Online TA",
    distribution_channel: "TA/TO",
    reserved_room_type: "A",
    customer_type: "Transient",
    lead_time: 7,
    arrival_month: new Date().getMonth() + 1,
    stays_in_weekend_nights: 0,
    stays_in_week_nights: 2,
  };
  Object.keys(names).forEach((k) => ($(k).value = defaults[k]));
  $("reference").value = "";
  $("case-truth").textContent =
    "Nueva reserva · ajusta los valores sugeridos a tu caso";
  $("save-state").textContent = "Sin guardar";
  $("save-state").className = "pill amber";
  $("calculate").textContent = "Analizar y guardar";
  $("calculate").disabled = false;
  $("save-feedback").hidden = true;
  $("error").textContent = "";
  Booking.reset();
  resetResult();
  stayTotal();
  if (navigate) go("lab");
}
function loadInputs(d, description, ref = "Ejemplo histórico") {
  if (busy || !mayReplace()) return;
  activeRecord = null;
  source = "example";
  dirty = false;
  requestId = crypto.randomUUID();
  Object.keys(names).forEach((k) => ($(k).value = d[k]));
  $("reference").value = ref;
  $("case-truth").textContent = description;
  $("calculate").textContent = "Analizar y guardar";
  $("calculate").disabled = false;
  $("save-state").textContent = "Sin guardar";
  $("save-state").className = "pill amber";
  $("save-feedback").hidden = true;
  $("error").textContent = "";
  Booking.reset(null, true);
  resetResult();
  stayTotal();
  go("lab");
}
function loadCase(i) {
  const c = summary.examples[i];
  loadInputs(
    c.inputs,
    `Ejemplo histórico ${c.row_id} · ${c.label} · resultado conocido: ${c.actual ? "canceló" : "no canceló"}`,
    `Ejemplo ${c.row_id}`,
  );
}
function loadExample() {
  const c =
    summary.examples.find((x) => x.row_id === 12301) || summary.examples[0];
  loadInputs(
    c.inputs,
    `Ejemplo histórico ${c.row_id} · resultado conocido: canceló. Guardarlo creará una copia de prueba.`,
    "Prueba de guardado",
  );
}
function showResult(result, values) {
  $("result-ready").hidden = false;
  $("result-empty").hidden = true;
  lastResult = result;
  try {
    lastStay = Booking.getStay();
  } catch {
    lastStay = null;
  }
  lastInputs = structuredClone(values);
  $("score").textContent = (result.score * 100).toLocaleString("es-CO", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
  $("decision").textContent = result.decision;
  const color = result.flagged ? "var(--amber)" : "var(--aqua)";
  $("decision").style.color = color;
  $("dial").style.background =
    `conic-gradient(${color} ${result.score * 360}deg,#283943 0deg)`;
  $("threshold").textContent =
    `Umbral de revisión: ${(result.threshold * 100).toFixed(0)} / 100`;
  $("next-action").textContent = result.flagged
    ? "Siguiente paso: revisa los datos y confirma las necesidades de la reserva según el protocolo del hotel. El modelo no contacta al huésped ni cancela o cobra."
    : "Siguiente paso: mantén el seguimiento habitual. Una señal baja no garantiza que la reserva se mantenga; también pueden ocurrir cancelaciones.";
  $("export").disabled = false;
}
function lockForm(value) {
  busy = value;
  $("predict-form")
    .querySelectorAll("input,select,button")
    .forEach((el) => (el.disabled = value));
  $("new-reservation").disabled = value;
  $("example-reservation").disabled = value;
  Booking.setBusy(value);
}
async function calculate(persist) {
  if (busy || !Booking.validate()) return;
  Booking.refresh();
  const stay = Booking.getStay();
  const values = inputs();
  if (
    values.stays_in_weekend_nights + values.stays_in_week_nights < 1 ||
    values.stays_in_weekend_nights + values.stays_in_week_nights > 30
  ) {
    $("error").textContent =
      "La estancia total debe sumar entre 1 y 30 noches. Corrige las noches antes de continuar.";
    return;
  }
  lockForm(true);
  $("error").textContent = "";
  $("save-feedback").hidden = true;
  $("calculate").textContent = persist ? "Guardando…" : "Analizando…";
  try {
    if (persist) {
      const payload = {
        inputs: values,
        stay,
        reference: $("reference").value,
        source,
        request_id: requestId,
      };
      if (activeRecord) {
        payload.id = activeRecord.id;
        payload.revision = activeRecord.revision;
      }
      const data = await api(
        activeRecord ? "/api/reservations/update" : "/api/reservations",
        payload,
      );
      activeRecord = data.reservation;
      dirty = false;
      $("reference").value = activeRecord.reference;
      showResult(activeRecord.result, activeRecord.inputs);
      $("save-state").textContent = "Guardada en este computador";
      $("save-state").className = "pill verified";
      $("save-feedback").textContent =
        `Guardada · ${activeRecord.id}. Puedes recuperarla en Mis reservas, incluso después de reiniciar la aplicación.`;
      $("save-feedback").hidden = false;
      $("after-save").hidden = false;
      $("save-feedback").focus({ preventScroll: true });
      $("save-feedback").scrollIntoView?.({
        block: "nearest",
        behavior: "smooth",
      });
    } else {
      showResult(await api("/api/predict", { inputs: values, stay }), values);
      $("save-state").textContent = activeRecord
        ? dirty
          ? "Cambios sin guardar"
          : "Guardada en este computador"
        : "Analizada · sin guardar";
    }
  } catch (e) {
    $("error").textContent = e.message;
  } finally {
    lockForm(false);
    $("calculate").textContent = activeRecord
      ? "Guardar cambios"
      : "Analizar y guardar";
    $("calculate").disabled = Boolean(activeRecord && !dirty);
  }
}
$("predict-form").onsubmit = (e) => {
  e.preventDefault();
  if (Booking.getStep() < 3) Booking.showStep(Booking.getStep() + 1);
  else calculate(true);
};
$("analyze-only").onclick = () => calculate(false);
$("new-reservation").onclick = () => newReservation();
$("another-reservation").onclick = () => newReservation();
$("saved-new").onclick = () => newReservation();
$("example-reservation").onclick = loadExample;
$("guide-example").onclick = loadExample;
$("export").onclick = () =>
  download(
    {
      reservation_id: activeRecord?.id || null,
      inputs: lastInputs,
      stay: lastStay,
      result: lastResult,
      generated_at: new Date().toISOString(),
    },
    "reservaiq-resultado.json",
  );
window.addEventListener("beforeunload", (e) => {
  if (dirty || busy || batchBusy) {
    e.preventDefault();
    e.returnValue = "";
  }
});
function renderQueue() {
  const k = Number($("capacity").value),
    rows = summary.queue.slice(0, k);
  $("capacity-label").textContent = k;
  $("capacity-info").textContent =
    `${Math.round((k / summary.queue.length) * 100)} % de la cohorte`;
  $("queue").innerHTML = rows
    .slice(0, 8)
    .map(
      (r, i) =>
        `<tr><td>${r.id}</td><td>${labels[r.hotel]}<br><span class="small muted">${labels[r.segment] || r.segment}</span></td><td>${r.lead_time} días</td><td>${r.nights}</td><td>${(r.score * 100).toFixed(1)}<div class="risk ${r.score >= summary.threshold ? "high" : ""}"><i style="width:${r.score * 100}%"></i></div></td><td><button data-row="${i}">Explorar ↗</button></td></tr>`,
    )
    .join("");
  $("queue-foot").textContent =
    `Se muestran ${Math.min(k, 8)} de ${k} reservas seleccionadas; la descarga incluye todas. Son ejemplos históricos, independientes de Mis reservas.`;
  document.querySelectorAll("[data-row]").forEach(
    (b) =>
      (b.onclick = () => {
        const r = summary.queue[Number(b.dataset.row)];
        loadInputs(r.inputs, `${r.id} · ejemplo histórico de prueba`, r.id);
      }),
  );
  $("queue-truth").textContent = revealed
    ? `En esta selección histórica: ${rows.reduce((a, r) => a + r.actual, 0)} de ${k} cancelaron (${pct(rows.reduce((a, r) => a + r.actual, 0) / k)}). Concentración histórica, no cancelaciones evitadas.`
    : "";
}
$("capacity").oninput = renderQueue;
$("reveal").onclick = () => {
  revealed = !revealed;
  $("reveal").textContent = revealed
    ? "Ocultar resultados históricos"
    : "Revelar resultados históricos";
  renderQueue();
};
$("export-queue").onclick = () =>
  download(
    {
      scope: "Cohorte histórica ilustrativa. No contactar huéspedes reales.",
      model: summary.version,
      capacity: Number($("capacity").value),
      reservations: summary.queue
        .slice(0, Number($("capacity").value))
        .map(({ actual, ...r }) => r),
    },
    "reservaiq-prioridades-historicas.json",
  );
function message(id, text, error = false) {
  $(id).textContent = text;
  $(id).hidden = false;
  $(id).classList.toggle("error", error);
}
async function refreshSaved() {
  const generation = ++listGeneration;
  $("saved-refresh").disabled = true;
  try {
    const data = await api("/api/reservations");
    if (generation !== listGeneration) return;
    savedRecords = data.reservations;
    renderSaved();
  } catch (e) {
    message("saved-message", e.message, true);
  } finally {
    if (generation === listGeneration) $("saved-refresh").disabled = false;
  }
}
function renderSaved() {
  const counts = { pending: 0, reviewed: 0, archived: 0 };
  savedRecords.forEach((r) => counts[r.status]++);
  const filterNames = {
    all: "Todas las guardadas",
    active: "Reservas activas",
    pending: "Reservas pendientes",
    reviewed: "Reservas revisadas",
    archived: "Reservas archivadas",
  };
  const countFilters = [
    ["all", "Guardadas", savedRecords.length],
    ["pending", "Pendientes", counts.pending],
    ["reviewed", "Revisadas", counts.reviewed],
    ["archived", "Archivadas", counts.archived],
  ];
  $("saved-counts").innerHTML = countFilters
    .map(
      ([key, label, count]) =>
        `<button type="button" class="count-filter" data-count-filter="${key}" aria-pressed="${$("saved-filter").value === key}" aria-controls="saved-list" aria-label="Ver ${label.toLowerCase()}: ${count}"><b>${count}</b><span>${label}</span><small>Ver registros →</small></button>`,
    )
    .join("");
  $("saved-counts")
    .querySelectorAll("[data-count-filter]")
    .forEach((button) => {
      button.onclick = () => {
        const value = button.dataset.countFilter;
        $("saved-filter").value = value;
        $("saved-search").value = "";
        savedPage = 0;
        renderSaved();
        $("saved-counts")
          .querySelector(`[data-count-filter="${value}"]`)
          .focus({ preventScroll: true });
        $("saved-results-title").scrollIntoView({ block: "nearest" });
      };
    });
  const capacity = Math.max(
    1,
    Math.min(500, Number($("saved-capacity").value) || 1),
  );
  const pending = savedRecords
    .filter((r) => r.status === "pending")
    .sort(
      (a, b) => b.result.score - a.result.score || a.id.localeCompare(b.id),
    );
  const priority = new Set(pending.slice(0, capacity).map((r) => r.id));
  $("saved-priority").textContent =
    `Puedes empezar por ${priority.size} de ${pending.length} pendientes, ordenadas por su índice. La marca “Prioritaria” respeta tu capacidad; no es una predicción de cancelación segura.`;
  const filter = $("saved-filter").value,
    search = $("saved-search").value.trim().toLocaleLowerCase("es");
  const filtered = savedRecords
    .filter(
      (r) =>
        (filter === "all" ||
          (filter === "active"
            ? r.status !== "archived"
            : r.status === filter)) &&
        `${r.reference} ${r.id}`.toLocaleLowerCase("es").includes(search),
    )
    .sort(
      (a, b) => b.result.score - a.result.score || a.id.localeCompare(b.id),
    );
  $("saved-results-title").textContent =
    `${filterNames[filter]} · ${filtered.length} ${filtered.length === 1 ? "registro" : "registros"}${search ? " encontrados" : ""}`;
  const pages = Math.max(1, Math.ceil(filtered.length / 20));
  savedPage = Math.min(savedPage, pages - 1);
  $("saved-page").textContent =
    `Página ${savedPage + 1} de ${pages} · ${filtered.length} reservas`;
  $("saved-prev").disabled = savedPage === 0;
  $("saved-next").disabled = savedPage >= pages - 1;
  $("saved-export").disabled = savedRecords.length === 0;
  if (!filtered.length) {
    $("saved-list").innerHTML =
      `<div class="empty"><h3>${!savedRecords.length ? "Todavía no has guardado reservas" : search ? "No hay coincidencias con esa búsqueda" : filter === "pending" ? "No tienes reservas pendientes" : filter === "reviewed" ? "Todavía no has marcado reservas como revisadas" : filter === "archived" ? "No tienes reservas archivadas" : "No hay reservas en esta categoría"}</h3><p>${savedRecords.length ? "Pulsa Guardadas para ver todos los registros o elige otra categoría." : "Crea una reserva y pulsa Analizar y guardar. Después aparecerá aquí."}</p></div>`;
    return;
  }
  $("saved-list").innerHTML = filtered
    .slice(savedPage * 20, savedPage * 20 + 20)
    .map(
      (r) =>
        `<article class="saved-card ${priority.has(r.id) ? "priority" : ""}"><div><h3>${esc(r.reference)}</h3><p class="small muted">${esc(r.id)} · ${sourceLabels[r.source]} · ${new Date(r.updated_at).toLocaleString("es-CO")}</p><span class="badge ${r.status}">${stateLabels[r.status]}</span>${priority.has(r.id) ? '<span class="badge reviewed">Prioritaria</span>' : ""}<p class="small muted">${r.stay ? `${ReservaDates.format(r.stay.check_in)} → ${ReservaDates.format(r.stay.check_out)}<br>` : "Fechas no registradas · "}${labels[r.inputs.hotel]} · ${r.inputs.lead_time} días de anticipación · ${r.inputs.stays_in_weekend_nights + r.inputs.stays_in_week_nights} noches</p><div class="actions">${r.status === "archived" ? `<button class="linkbutton" data-status="pending" data-id="${r.id}">Restaurar</button>` : `<button class="linkbutton" data-open="${r.id}">Abrir</button><button class="linkbutton" data-status="${r.status === "pending" ? "reviewed" : "pending"}" data-id="${r.id}">${r.status === "pending" ? "Marcar revisada" : "Volver a pendiente"}</button><button class="linkbutton" data-status="archived" data-id="${r.id}">Archivar</button>`}</div></div><div class="saved-score"><strong>${(r.result.score * 100).toFixed(1)}</strong><span class="small muted">índice / 100</span></div></article>`,
    )
    .join("");
  document
    .querySelectorAll("[data-open]")
    .forEach((b) => (b.onclick = () => openSaved(b.dataset.open)));
  document
    .querySelectorAll("[data-status]")
    .forEach(
      (b) => (b.onclick = () => changeStatus(b.dataset.id, b.dataset.status)),
    );
}
async function openSaved(id) {
  if (busy || !mayReplace()) return;
  try {
    const data = await api("/api/reservations");
    const r = data.reservations.find((x) => x.id === id);
    if (!r || r.status === "archived")
      throw Error("La reserva ya no está activa. Actualiza la lista.");
    activeRecord = r;
    source = r.source;
    dirty = false;
    requestId = crypto.randomUUID();
    Object.keys(names).forEach((k) => ($(k).value = r.inputs[k]));
    $("reference").value = r.reference;
    $("case-truth").textContent =
      `Copia guardada · ${r.id} · ${sourceLabels[r.source]} · resultado real desconocido`;
    $("save-state").textContent = "Guardada en este computador";
    $("save-state").className = "pill verified";
    $("calculate").textContent = "Guardar cambios";
    $("calculate").disabled = true;
    $("error").textContent = "";
    $("save-feedback").hidden = true;
    Booking.reset(r.stay || null, !r.stay);
    showResult(r.result, r.inputs);
    stayTotal();
    go("lab");
  } catch (e) {
    message("saved-message", e.message, true);
  }
}
async function changeStatus(id, status) {
  const r = savedRecords.find((x) => x.id === id);
  $("saved-list")
    .querySelectorAll("button")
    .forEach((b) => (b.disabled = true));
  try {
    await api("/api/reservations/status", { id, revision: r.revision, status });
    message(
      "saved-message",
      status === "archived"
        ? "Reserva archivada. Puedes recuperarla con el filtro Archivadas."
        : status === "reviewed"
          ? "Reserva marcada como revisada. No se realizó ninguna acción sobre el huésped."
          : "Reserva disponible de nuevo como pendiente.",
    );
  } catch (e) {
    message("saved-message", e.message, true);
  } finally {
    await refreshSaved();
  }
}
$("saved-refresh").onclick = () => {
  $("saved-message").hidden = true;
  refreshSaved();
};
["saved-search", "saved-filter", "saved-capacity"].forEach(
  (id) =>
    ($(id).oninput = () => {
      savedPage = 0;
      renderSaved();
    }),
);
$("saved-prev").onclick = () => {
  savedPage--;
  renderSaved();
};
$("saved-next").onclick = () => {
  savedPage++;
  renderSaved();
};
$("saved-export").onclick = async () => {
  try {
    const data = await api("/api/reservations");
    download(
      {
        format: "reservaiq-reservations-v2",
        exported_at: new Date().toISOString(),
        ...data,
      },
      "reservaiq-mis-reservas.json",
    );
  } catch (e) {
    message("saved-message", e.message, true);
  }
};
function resetBatch() {
  batchRows = null;
  batchResult = null;
  batchId = crypto.randomUUID();
  $("batch-save").disabled = true;
  $("batch-export").disabled = true;
  $("batch-preview").textContent = "";
  $("batch-result").textContent =
    "Archivo seleccionado. Analízalo para ver los resultados antes de guardarlo.";
}
function lockBatch(value) {
  batchBusy = value;
  $("csv").disabled = value;
  $("batch-button").disabled = value;
  $("batch-save").disabled = value || !batchResult;
}
$("csv").onchange = resetBatch;
$("batch-button").onclick = async () => {
  if (batchBusy) return;
  resetBatch();
  lockBatch(true);
  try {
    const f = $("csv").files[0];
    if (!f)
      throw Error("Selecciona primero un archivo CSV o descarga el ejemplo.");
    if (f.size > 150000)
      throw Error(
        "El archivo supera 150 KB. Divide el lote en archivos más pequeños.",
      );
    const rows = ReservaCSV.parse(await f.text());
    const result = await api("/api/batch", rows);
    batchRows = rows;
    batchResult = result;
    $("batch-result").textContent =
      `${result.count} reservas analizadas · ${result.flagged} superan el umbral. Aún no están guardadas. Revisa la vista previa y pulsa Guardar lote.`;
    $("batch-preview").innerHTML =
      "<table><thead><tr><th>Fila</th><th>Hotel</th><th>Anticipación</th><th>Índice / 100</th><th>Sugerencia</th></tr></thead><tbody>" +
      result.results
        .slice(0, 8)
        .map(
          (r, i) =>
            `<tr><td>${i + 1}</td><td>${labels[rows[i].hotel]}</td><td>${rows[i].lead_time} días</td><td>${(r.score * 100).toFixed(1)}</td><td>${esc(r.decision)}</td></tr>`,
        )
        .join("") +
      `</tbody></table><p class="note">Vista previa: ${Math.min(8, result.count)} de ${result.count}. La descarga y el guardado incluyen todas las filas.</p>`;
    $("batch-export").disabled = false;
  } catch (e) {
    $("batch-result").textContent = e.message;
  } finally {
    lockBatch(false);
  }
};
$("batch-save").onclick = async () => {
  if (batchBusy || !batchRows) return;
  lockBatch(true);
  let complete = false;
  try {
    const data = await api("/api/reservations/batch", {
      rows: batchRows,
      request_id: batchId,
    });
    $("batch-result").textContent =
      `${data.count} reservas guardadas en este computador. Ya puedes abrirlas en Mis reservas. Volver a importar el archivo creará un lote nuevo.`;
    complete = true;
  } catch (e) {
    $("batch-result").textContent = e.message;
  } finally {
    lockBatch(false);
    if (complete) $("batch-save").disabled = true;
  }
};
$("batch-export").onclick = () =>
  download({ inputs: batchRows, ...batchResult }, "reservaiq-lote.json");
$("health-check").onclick = async () => {
  $("health-check").disabled = true;
  $("health-results").textContent = "Comprobando…";
  const checks = [
    ["Servidor y modelo", "/api/health"],
    ["Evidencias del entrenamiento", "/api/summary"],
    ["Acceso al guardado local", "/api/reservations"],
  ];
  const results = await Promise.all(
    checks.map(async ([label, url]) => {
      try {
        await api(url);
        return `<li>${label}<span>Disponible</span></li>`;
      } catch (e) {
        return `<li>${label}<span class="health-error">${esc(e.message)}</span></li>`;
      }
    }),
  );
  $("health-results").innerHTML = results.join("");
  $("health-check").disabled = false;
};
fetch("/api/summary")
  .then((r) => {
    if (!r.ok) throw Error("Faltan los resultados del entrenamiento.");
    return r.json();
  })
  .then((s) => {
    summary = s;
    let m = s.test;
    $("lift").textContent = m.top20.lift.toFixed(2) + "×";
    $("top-precision").textContent = pct(m.top20.precision);
    $("top-recall").textContent = pct(m.top20.recall);
    $("test-n").textContent = number(m.n);
    $("bars").innerHTML = bars(
      s.selection.candidates.map((c) => ({
        name: c.name,
        value: c.average_precision,
      })),
    );
    const caseHtml = s.examples
      .map(
        (c, i) =>
          `<button class="case" data-case="${i}"><span class="num">REGISTRO ${c.row_id}</span><span class="result"><span>${c.label}</span><span class="score">${(c.score * 100).toFixed(1)}</span></span></button>`,
      )
      .join("");
    $("cases").innerHTML = caseHtml;
    $("labcases").innerHTML = caseHtml;
    document
      .querySelectorAll("[data-case]")
      .forEach((b) => (b.onclick = () => loadCase(Number(b.dataset.case))));
    $("model-version").textContent = s.version;
    $("footmodel").textContent =
      s.model +
      (s.azure_verified ? " · entrenado en Azure ML" : " · evaluación local");
    renderDeployment(s);
    $("split").innerHTML = Object.entries(s.data.splits)
      .map(
        ([k, v]) =>
          `<div><strong>${number(v.n)}</strong>${{ train: "Entrenamiento", validation: "Validación", test: "Prueba" }[k]}<br>${v.booking_start} a ${v.booking_end_exclusive} (excl.)</div>`,
      )
      .join("");
    $("matrix").innerHTML =
      `<div><strong>${number(m.tp)}</strong><span>Cancelaciones detectadas · TP</span></div><div class="bad"><strong>${number(m.fn)}</strong><span>Cancelaciones omitidas · FN</span></div><div class="bad"><strong>${number(m.fp)}</strong><span>Falsas alertas · FP</span></div><div><strong>${number(m.tn)}</strong><span>Sin cancelación ni alerta · TN</span></div>`;
    $("thresholdmetrics").textContent =
      `Umbral ${(s.threshold * 100).toFixed(0)}/100 · detección ${pct(m.recall)} · precisión ${pct(m.precision)} · F1 ${m.f1.toFixed(3)}.`;
    $("roc").textContent = m.roc_auc.toFixed(3);
    $("ap").textContent = m.average_precision.toFixed(3);
    $("prevalence").textContent =
      `Frecuencia de cancelación en prueba: ${pct(m.positives / m.n)}. Revisar una selección aleatoria concentraría esa proporción en promedio.`;
    $("ci").textContent =
      `Detección al umbral: intervalo Wilson 95 % de ${pct(m.recall_wilson_95[0])} a ${pct(m.recall_wilson_95[1])}; aproximación que no corrige dependencia entre reservas.`;
    $("model-table").innerHTML = s.selection.candidates
      .map(
        (c) =>
          `<tr class="${c.name === s.model ? "selected" : ""}"><td>${c.name}</td><td>${c.average_precision.toFixed(3)}</td><td>${c.roc_auc.toFixed(3)}</td></tr>`,
      )
      .join("");
    $("importance").innerHTML = bars(
      s.importance_validation
        .slice(0, 6)
        .map((x) => ({ name: names[x.feature], value: x.mean })),
      Math.max(...s.importance_validation.map((x) => x.mean)),
    );
    $("importance-note").textContent =
      `Caída de AP en puntos porcentuales al permutar cada variable. Muestra fija de ${number(s.importance_sample_n)} reservas de validación, tres repeticiones. Importancia global, no explicación causal individual.`;
    renderQueue();
    buildForm();
    newReservation(false);
    $("loading").hidden = true;
    $("app").hidden = false;
    const previous = sessionStorage.getItem("reservaiq-view");
    if (
      ["overview", "lab", "saved", "guide", "model", "project"].includes(
        previous,
      )
    )
      go(previous);
  })
  .catch((e) => {
    $("loading").textContent =
      "No pudimos conectar con el modelo. Mantén abierta la terminal de ReservaIQ y vuelve a cargar esta página. Detalle: " +
      e.message;
  });

function renderDeployment(s) {
  const d = s.deployment || {},
    verified = s.azure_verified === true;
  $("cloud-status").textContent = verified
    ? "Modelo entrenado en Azure ML"
    : "Modelo local · procedencia documentada";
  $("architecture-status").textContent = verified
    ? "Trabajo completado y modelo descargado"
    : "Componentes configurados";
  $("execution-status").innerHTML = [
    ["Datos y particiones auditados", "VERIFICADO"],
    ["Modelo utilizado por la aplicación", verified ? "AZURE ML" : "LOCAL"],
    ["Estado del trabajo", d.job_status || "Sin ejecución"],
    ["Estado de cómputo", d.compute_state || "No creado"],
  ]
    .map(([a, b]) => `<li>${a}<span>${b}</span></li>`)
    .join("");
  $("execution-detail").textContent = verified
    ? `Trabajo ${d.job_name}. Modelo ${d.model_name}, versión ${d.model_version}. Huella SHA256 comprobada al iniciar la aplicación.`
    : "El modelo local permite comprobar la decisión y las métricas; la configuración de Azure se conserva en el repositorio.";
  $("execution-cost").textContent =
    d.cost_estimate_usd != null
      ? "≈ US$" + Number(d.cost_estimate_usd).toFixed(2)
      : "Por verificar";
  $("cost-detail").textContent =
    d.cost_note ||
    "Estimación basada en horas de cómputo y recursos asociados. No se presenta como factura consolidada.";
}

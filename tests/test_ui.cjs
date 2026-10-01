/* DOM component checks with an in-memory fake API. This is not browser E2E. */
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const { randomUUID } = require("node:crypto");
const { JSDOM } = require("jsdom");
const html = fs.readFileSync("web/index.html", "utf8");
const summary = JSON.parse(fs.readFileSync("artifacts/summary.json", "utf8"));
const flush = async () => {
  for (let i = 0; i < 6; i++)
    await new Promise((resolve) => setImmediate(resolve));
};
async function setup(t, cloud = false) {
  const dom = new JSDOM(html, {
    url: "http://127.0.0.1:8765",
    runScripts: "outside-only",
  });
  t.after(() => dom.window.close());
  const w = dom.window,
    records = [],
    calls = [];
  w.structuredClone = structuredClone;
  w.scrollTo = () => {};
  w.confirm = () => true;
  Object.defineProperty(w.crypto, "randomUUID", { value: randomUUID });
  const result = (inputs) => ({
    score: inputs.lead_time === 7 ? 0.136 : 0.398,
    threshold: 0.17,
    flagged: inputs.lead_time !== 7,
    decision:
      inputs.lead_time === 7 ? "Seguimiento habitual" : "Priorizar revisión",
  });
  w.fetch = async (url, options) => {
    const payload = options?.body ? JSON.parse(options.body) : undefined;
    calls.push({ url, payload });
    let body,
      ok = true;
    if (url === "/api/summary") body = { ...summary, application: { cloud } };
    else if (url === "/api/health") body = { status: "ok" };
    else if (url === "/api/reservations" && !payload)
      body = { reservations: records, count: records.length };
    else if (url === "/api/predict") body = result(payload.inputs || payload);
    else if (url === "/api/batch")
      body = {
        count: payload.length,
        flagged: 0,
        results: payload.map(result),
      };
    else if (url === "/api/reservations/batch") {
      const saved = payload.rows.map((inputs) => ({
        id: randomUUID(),
        inputs,
        result: result(inputs),
        source: "csv",
        status: "pending",
        revision: 1,
        reference: "CSV",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }));
      records.push(...saved);
      body = { count: saved.length, reservations: saved };
    } else if (url === "/api/reservations") {
      const record = {
        id: "RI-TEST",
        ...payload,
        result: result(payload.inputs),
        revision: 1,
        status: "pending",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      records.push(record);
      body = { reservation: record };
    } else if (url === "/api/reservations/update") {
      const r = records.find((x) => x.id === payload.id);
      Object.assign(r, {
        inputs: payload.inputs,
        reference: payload.reference,
        stay: payload.stay,
        result: result(payload.inputs),
        revision: r.revision + 1,
      });
      body = { reservation: r };
    } else if (url === "/api/reservations/status") {
      const r = records.find((x) => x.id === payload.id);
      r.status = payload.status;
      r.revision++;
      body = { reservation: r };
    } else {
      ok = false;
      body = { error: "Ruta desconocida en el simulador" };
    }
    return { ok, json: async () => structuredClone(body) };
  };
  w.HTMLElement.prototype.scrollIntoView = () => {};
  w.eval(fs.readFileSync("web/dates.js", "utf8"));
  w.eval(fs.readFileSync("web/booking.js", "utf8"));
  w.eval(fs.readFileSync("web/csv.js", "utf8"));
  w.eval(fs.readFileSync("web/app.js", "utf8"));
  await flush();
  const $ = (id) => w.document.getElementById(id);
  assert.equal($("app").hidden, false, $("loading").textContent);
  return {
    w,
    $,
    records,
    calls,
    click: async (id) => {
      $(id).click();
      await flush();
    },
    edit: (id, value) => {
      $(id).value = value;
      $(id).dispatchEvent(new w.Event("input", { bubbles: true }));
    },
  };
}
test("first load has six routes, helpful fields and no automatic save", async (t) => {
  const ui = await setup(t);
  assert.equal(ui.w.document.querySelectorAll(".view").length, 6);
  assert.equal(
    ui.w.document.querySelectorAll(
      "#form-fields [aria-describedby], #numeric-fields [aria-describedby]",
    ).length,
    10,
  );
  assert.equal(ui.$("save-state").textContent, "Sin guardar");
  assert.equal(ui.records.length, 0);
  assert.equal(ui.calls.filter((x) => x.payload).length, 0);
});
test("analysis and saving are distinct, edited record retains identity", async (t) => {
  const u = await setup(t);
  await u.click("example-reservation");
  await u.click("analyze-only");
  assert.equal(u.records.length, 0);
  assert.match(u.$("save-state").textContent, /sin guardar/);
  await u.click("calculate");
  assert.equal(u.records.length, 1);
  assert.match(u.$("save-feedback").textContent, /RI-TEST/);
  assert.equal(u.$("calculate").disabled, true);
  u.edit("lead_time", "7");
  assert.equal(u.$("score").textContent, "—");
  assert.equal(u.$("export").disabled, true);
  await u.click("analyze-only");
  assert.equal(u.records[0].inputs.lead_time, 28);
  assert.match(u.$("save-state").textContent, /Cambios sin guardar/);
  await u.click("calculate");
  assert.equal(u.records.length, 1);
  assert.equal(u.records[0].inputs.lead_time, 7);
  assert.equal(u.records[0].revision, 2);
  assert.equal(u.$("save-state").textContent, "Guardada en este computador");
});
test("saved references render as text and saved view restores from its API", async (t) => {
  const u = await setup(t);
  await u.click("example-reservation");
  u.edit("reference", "<img src=x onerror=alert(1)>");
  await u.click("calculate");
  u.w.document.querySelector('[data-view="saved"]').click();
  await flush();
  assert.equal(u.$("saved-list").querySelectorAll("img").length, 0);
  assert.match(u.$("saved-list").textContent, /<img src=x/);
  u.$("saved-list").querySelector("[data-open]").click();
  await flush();
  assert.equal(u.$("lab").hidden, false);
  assert.equal(u.$("reference").value, "<img src=x onerror=alert(1)>");
});
test("archive and restore remain reachable through the filters", async (t) => {
  const u = await setup(t);
  await u.click("example-reservation");
  await u.click("calculate");
  u.w.document.querySelector('[data-view="saved"]').click();
  await flush();
  u.$("saved-list").querySelector('[data-status="archived"]').click();
  await flush();
  assert.equal(u.records[0].status, "archived");
  assert.equal(u.$("saved-list").querySelectorAll(".saved-card").length, 0);
  u.edit("saved-filter", "archived");
  u.$("saved-list").querySelector('[data-status="pending"]').click();
  await flush();
  assert.equal(u.records[0].status, "pending");
  assert.match(u.$("saved-message").textContent, /pendiente/);
});
test("CSV preview does not save; explicit save stores all rows", async (t) => {
  const u = await setup(t);
  const text = fs.readFileSync("ejemplos-csv/reservas-listas.csv", "utf8");
  Object.defineProperty(u.$("csv"), "files", {
    value: [{ size: Buffer.byteLength(text), text: async () => text }],
  });
  await u.click("batch-button");
  assert.equal(u.records.length, 0);
  assert.match(u.$("batch-result").textContent, /8 reservas analizadas/);
  assert.equal(u.$("batch-preview").querySelectorAll("tbody tr").length, 8);
  await u.click("batch-save");
  assert.equal(u.records.length, 8);
  assert.equal(u.$("batch-save").disabled, true);
  await u.click("batch-save");
  assert.equal(u.records.length, 8);
});
test("network failures explain recovery and never claim a save", async (t) => {
  const u = await setup(t);
  await u.click("example-reservation");
  u.w.fetch = async () => {
    throw Error("offline");
  };
  await u.click("calculate");
  assert.match(u.$("error").textContent, /terminal de la aplicación/);
  assert.equal(u.$("save-state").textContent, "Sin guardar");
  assert.equal(u.$("calculate").disabled, false);
  assert.equal(u.records.length, 0);
});
test("zero-night reservations are rejected before any save request", async (t) => {
  const u = await setup(t);
  await u.click("example-reservation");
  u.edit("stays_in_weekend_nights", "0");
  u.edit("stays_in_week_nights", "0");
  await u.click("calculate");
  assert.match(u.$("error").textContent, /entre 1 y 30 noches/);
  assert.equal(u.calls.filter((x) => x.payload).length, 0);
});

test("calendar blocks incomplete dates and takes a new reservation through three steps", async (t) => {
  const u = await setup(t);
  await u.click("new-reservation");
  await u.click("step-next");
  assert.equal(u.w.Booking.getStep(), 1);
  assert.match(u.$("date-error").textContent, /llegada/);
  u.edit("booked-on", "2026-10-01");
  await u.click("date-select-check-in");
  u.$("calendar-months").querySelector('[data-date="2026-10-02"]').click();
  assert.equal(u.$("check-in").value, "2026-10-02");
  assert.match(u.$("calendar-prompt").textContent, /salida/);
  u.$("calendar-months").querySelector('[data-date="2026-10-05"]').click();
  assert.equal(u.$("check-out").value, "2026-10-05");
  assert.equal(u.$("lead_time").value, "1");
  assert.equal(u.$("arrival_month").value, "10");
  assert.equal(u.$("stays_in_weekend_nights").value, "2");
  assert.equal(u.$("stays_in_week_nights").value, "1");
  assert.match(u.$("stay-total").textContent, /3 noches/);
  await u.click("step-next");
  assert.equal(u.w.Booking.getStep(), 2);
  u.edit("reference", "Fin de semana");
  await u.click("step-next");
  assert.equal(u.w.Booking.getStep(), 3);
  assert.match(u.$("review-summary").textContent, /Fin de semana/);
  await u.click("calculate");
  assert.equal(u.records.length, 1);
  assert.deepEqual(u.records[0].stay, {
    booked_on: "2026-10-01",
    check_in: "2026-10-02",
    check_out: "2026-10-05",
  });
  assert.equal(u.$("after-save").hidden, false);
  assert.equal(u.$("result-ready").hidden, false);
  u.w.document.querySelector('[data-view="saved"]').click();
  await flush();
  assert.match(u.$("saved-list").textContent, /2026/);
  u.$("saved-list").querySelector("[data-open]").click();
  await flush();
  assert.equal(u.$("check-in").value, "2026-10-02");
  assert.equal(u.$("calendar-mode").hidden, false);
  u.edit("check-out", "2026-10-06");
  assert.equal(u.$("result-ready").hidden, true);
  await u.click("calculate");
  assert.equal(u.records.length, 1);
  assert.equal(u.records[0].stay.check_out, "2026-10-06");
  assert.equal(u.records[0].inputs.stays_in_week_nights, 2);
  await u.click("another-reservation");
  assert.equal(u.w.Booking.getStep(), 1);
  assert.equal(u.$("check-in").value, "");
});
test("calendar supports keyboard focus and a stay crossing into the next month", async (t) => {
  const u = await setup(t);
  await u.click("new-reservation");
  u.edit("booked-on", "2026-10-01");
  await u.click("date-select-check-in");
  const day = u.$("calendar-months").querySelector('[data-date="2026-10-01"]');
  day.focus();
  day.dispatchEvent(
    new u.w.KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }),
  );
  assert.equal(u.w.document.activeElement.dataset.date, "2026-10-02");
  u.$("calendar-months").querySelector('[data-date="2026-10-31"]').click();
  assert.equal(u.w.document.activeElement.dataset.date, "2026-11-01");
  u.$("calendar-months").querySelector('[data-date="2026-11-02"]').click();
  assert.equal(u.$("stays_in_weekend_nights").value, "2");
  assert.equal(u.$("stays_in_week_nights").value, "0");
});
test("historical examples keep their original numeric features and never invent dates", async (t) => {
  const u = await setup(t);
  await u.click("example-reservation");
  assert.equal(u.$("calendar-mode").hidden, true);
  assert.equal(u.$("historical-mode").hidden, false);
  assert.equal(u.$("check-in").value, "");
  assert.equal(u.w.Booking.getStay(), null);
  await u.click("calculate");
  assert.equal(u.records[0].stay, null);
  await u.click("use-calendar");
  assert.equal(u.$("calendar-mode").hidden, false);
  assert.equal(u.w.Booking.getStep(), 1);
  assert.equal(u.$("result-ready").hidden, true);
});
test("typed invalid dates and boundary years do not crash the calendar or save", async (t) => {
  const u = await setup(t);
  await u.click("new-reservation");
  const errors = [];
  u.w.addEventListener("error", (event) => errors.push(event.error));
  u.edit("booked-on", "0001-01-01");
  u.edit("check-in", "0001-01-02");
  u.edit("check-out", "0001-01-03");
  await u.click("step-next");
  assert.equal(u.w.Booking.getStep(), 1);
  u.edit("booked-on", "2100-12-01");
  u.edit("check-in", "2100-12-30");
  u.edit("check-out", "2100-12-31");
  assert.equal(
    u.$("calendar-months").querySelectorAll(".calendar-month").length,
    1,
  );
  assert.equal(u.$("stays_in_week_nights").value, "1");
  u.edit("booked-on", "1900-01-01");
  u.edit("check-in", "");
  u.edit("check-out", "");
  const first = u
    .$("calendar-months")
    .querySelector('[data-date="1900-01-01"]');
  first.dispatchEvent(
    new u.w.KeyboardEvent("keydown", { key: "PageUp", bubbles: true }),
  );
  assert.equal(u.w.document.activeElement.dataset.date, "1900-01-01");
  assert.deepEqual(errors, []);
  assert.equal(u.records.length, 0);
});

test("clickable counts reveal each category, clear searches and keep active state in sync", async (t) => {
  const u = await setup(t);
  await u.click("example-reservation");
  await u.click("calculate");
  const original = structuredClone(u.records[0]);
  u.records[0].status = "reviewed";
  u.w.document.querySelector('[data-view="saved"]').click();
  await flush();
  const category = async (key) => {
    u.$("saved-counts").querySelector(`[data-count-filter="${key}"]`).click();
    await flush();
  };
  await category("reviewed");
  assert.equal(u.$("saved-filter").value, "reviewed");
  assert.equal(u.$("saved-list").querySelectorAll(".saved-card").length, 1);
  assert.match(u.$("saved-results-title").textContent, /Revisadas|revisadas/);
  assert.equal(
    u
      .$("saved-counts")
      .querySelector('[data-count-filter="reviewed"]')
      .getAttribute("aria-pressed"),
    "true",
  );
  u.edit("saved-search", "no existe");
  assert.equal(u.$("saved-list").querySelectorAll(".saved-card").length, 0);
  await category("reviewed");
  assert.equal(u.$("saved-search").value, "");
  assert.equal(u.$("saved-list").querySelectorAll(".saved-card").length, 1);
  await category("pending");
  assert.match(u.$("saved-list").textContent, /No tienes reservas pendientes/);
  await category("archived");
  assert.match(u.$("saved-list").textContent, /No tienes reservas archivadas/);
  u.records.push(
    { ...original, id: "RI-ARCHIVED", status: "archived" },
    { ...original, id: "RI-PENDING", status: "pending" },
  );
  await u.click("saved-refresh");
  for (const [key, status] of [
    ["pending", "pending"],
    ["reviewed", "reviewed"],
    ["archived", "archived"],
  ]) {
    await category(key);
    assert.equal(u.$("saved-list").querySelectorAll(".saved-card").length, 1);
    assert.equal(
      u.$("saved-list").querySelector(`.badge.${status}`) !== null,
      true,
    );
  }
  await category("all");
  assert.equal(u.$("saved-list").querySelectorAll(".saved-card").length, 3);
  u.edit("saved-filter", "reviewed");
  assert.equal(
    u
      .$("saved-counts")
      .querySelector('[data-count-filter="reviewed"]')
      .getAttribute("aria-pressed"),
    "true",
  );
  // Changing a card must leave the pagination at the first page of its category.
  for (let i = 0; i < 22; i++)
    u.records.push({ ...original, id: "RI-MANY-" + i, status: "pending" });
  await u.click("saved-refresh");
  await category("all");
  await u.click("saved-next");
  assert.match(u.$("saved-page").textContent, /Página 2/);
  await category("reviewed");
  assert.match(u.$("saved-page").textContent, /Página 1 de 1/);
  assert.equal(u.w.document.activeElement.dataset.countFilter, "reviewed");
});

test("calendar can be hidden without losing dates or changing an existing result", async (t) => {
  const u = await setup(t);
  await u.click("new-reservation");
  assert.equal(u.$("calendar-board").hidden, false);
  u.edit("booked-on", "2026-10-01");
  await u.click("date-select-check-in");
  u.$("calendar-months").querySelector('[data-date="2026-10-02"]').click();
  u.$("calendar-months").querySelector('[data-date="2026-10-05"]').click();
  assert.equal(u.$("calendar-board").hidden, true);
  assert.equal(u.$("toggle-calendar").getAttribute("aria-expanded"), "false");
  assert.equal(u.$("toggle-calendar").textContent, "Mostrar calendario");
  const stay = JSON.stringify(u.w.Booking.getStay());
  await u.click("toggle-calendar");
  assert.equal(u.$("calendar-board").hidden, false);
  assert.equal(u.$("toggle-calendar").getAttribute("aria-expanded"), "true");
  await u.click("step-next");
  await u.click("step-next");
  await u.click("analyze-only");
  const score = u.$("score").textContent;
  await u.click("step-back");
  await u.click("step-back");
  await u.click("toggle-calendar");
  assert.equal(u.$("calendar-board").hidden, true);
  assert.equal(JSON.stringify(u.w.Booking.getStay()), stay);
  assert.equal(u.$("score").textContent, score);
  assert.equal(u.$("lead_time").value, "1");
  assert.equal(u.records.length, 0);
  // Calendar visibility is a UI preference, never an analysis or persistence action.
  await u.click("step-next");
  await u.click("step-next");
  await u.click("calculate");
  u.w.document.querySelector('[data-view="saved"]').click();
  await flush();
  u.$("saved-list").querySelector("[data-open]").click();
  await flush();
  assert.equal(u.$("calendar-board").hidden, true);
  assert.equal(JSON.stringify(u.w.Booking.getStay()), stay);
});
test("project view links the four rubric criteria to evidence and working demo navigation", async (t) => {
  const u = await setup(t);
  u.w.document.querySelector('[data-view="project"]').click();
  const project = u.$("project");
  assert.equal(project.hidden, false);
  assert.equal(project.querySelectorAll(".rubric-card").length, 4);
  assert.deepEqual(
    [...project.querySelectorAll(".rubric-weight")].map((x) => x.textContent),
    [
      "20 % · Análisis",
      "25 % · Diseño",
      "30 % · Implementación",
      "25 % · Presentación",
    ],
  );
  assert.match(project.textContent, /no asigna una calificación/);
  project.querySelector('[data-go="guide"]').click();
  assert.equal(u.$("guide").hidden, false);
  project.querySelector('[data-go="model"]').click();
  assert.equal(u.$("model").hidden, false);
  assert.equal(u.records.length, 0);
});

test("creation date is visible and editable in the same calendar with dates and saved records kept consistent", async (t) => {
  const u = await setup(t);
  await u.click("new-reservation");
  assert.equal(u.$("booked-on").closest("details"), null);
  assert.equal(u.$("booked-on").closest(".date-fields") !== null, true);
  u.edit("booked-on", "2026-10-01");
  await u.click("date-select-booked-on");
  assert.equal(
    u.$("date-select-booked-on").getAttribute("aria-pressed"),
    "true",
  );
  assert.match(u.$("calendar-prompt").textContent, /cuándo se creó/);
  await u.click("calendar-prev");
  u.$("calendar-months").querySelector('[data-date="2026-09-30"]').click();
  assert.equal(u.$("booked-on").value, "2026-09-30");
  assert.equal(
    u.$("date-select-check-in").getAttribute("aria-pressed"),
    "true",
  );
  u.$("calendar-months").querySelector('[data-date="2026-10-02"]').click();
  u.$("calendar-months").querySelector('[data-date="2026-10-05"]').click();
  assert.equal(u.$("lead_time").value, "2");
  assert.equal(u.$("stays_in_weekend_nights").value, "2");
  await u.click("step-next");
  await u.click("step-next");
  await u.click("calculate");
  assert.equal(u.records[0].stay.booked_on, "2026-09-30");
  await u.click("step-back");
  await u.click("step-back");
  u.$("booked-on").focus();
  assert.equal(u.$("calendar-board").hidden, false);
  assert.equal(
    u.$("date-select-booked-on").getAttribute("aria-pressed"),
    "true",
  );
  await u.click("calendar-next");
  u.$("calendar-months").querySelector('[data-date="2026-10-01"]').click();
  assert.equal(u.$("lead_time").value, "1");
  assert.equal(u.$("check-in").value, "2026-10-02");
  assert.equal(u.$("check-out").value, "2026-10-05");
  assert.equal(u.$("result-ready").hidden, true);
  await u.click("step-next");
  await u.click("step-next");
  await u.click("calculate");
  assert.equal(u.records.length, 1);
  assert.equal(u.records[0].revision, 2);
  assert.equal(u.records[0].stay.booked_on, "2026-10-01");
  await u.click("step-back");
  await u.click("step-back");
  await u.click("date-select-booked-on");
  u.$("calendar-months").querySelector('[data-date="2026-10-03"]').click();
  await u.click("step-next");
  assert.equal(u.w.Booking.getStep(), 1);
  assert.match(u.$("date-error").textContent, /60 días/);
  assert.equal(u.records[0].stay.booked_on, "2026-10-01");
  assert.equal(u.$("check-in").value, "2026-10-02");
});

test("cloud mode explains shared fictional data and saves without local-only claims", async (t) => {
  const u = await setup(t, true);
  assert.match(u.$("overview").textContent, /Demo académica compartida/);
  assert.match(u.$("saved").textContent, /Todos los que abran este enlace/);
  assert.doesNotMatch(
    u.$("project").textContent,
    /su grupo temporal fue cerrado/,
  );
  await u.click("example-reservation");
  await u.click("calculate");
  assert.equal(u.$("save-state").textContent, "Guardada en Azure");
  assert.equal(u.records.length, 1);
  u.w.document.querySelector('[data-view="saved"]').click();
  await flush();
  assert.equal(u.$("saved-list").querySelectorAll(".saved-card").length, 1);
});

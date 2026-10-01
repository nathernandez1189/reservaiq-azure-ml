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
async function setup(t) {
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
    if (url === "/api/summary") body = summary;
    else if (url === "/api/health") body = { status: "ok" };
    else if (url === "/api/reservations" && !payload)
      body = { reservations: records, count: records.length };
    else if (url === "/api/predict") body = result(payload);
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
    ui.w.document.querySelectorAll("#form-fields [aria-describedby]").length,
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
  u.edit("stays_in_weekend_nights", "0");
  u.edit("stays_in_week_nights", "0");
  await u.click("calculate");
  assert.match(u.$("error").textContent, /entre 1 y 30 noches/);
  assert.equal(u.calls.filter((x) => x.payload).length, 0);
});

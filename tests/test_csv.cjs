const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const { parse } = require("../web/csv.js");
const csv = fs.readFileSync("ejemplos-csv/reservas-listas.csv", "utf8");
test("real example has eight reservations and integer fields", () => {
  const rows = parse(csv);
  assert.equal(rows.length, 8);
  assert.equal(typeof rows[0].lead_time, "number");
  assert.equal(Object.keys(rows[0]).length, 10);
});
test("BOM, CRLF, blank trailing lines and semicolon exports", () => {
  assert.deepEqual(
    parse("\uFEFF" + csv.replace(/,/g, ";").replace(/\n/g, "\r\n") + "\r\n"),
    parse(csv),
  );
});
test("quoted fields work with both delimiters", () => {
  const quoted = csv
    .trim()
    .split(/\r?\n/)
    .map((line) =>
      line
        .split(",")
        .map((cell) => '"' + cell + '"')
        .join(";"),
    )
    .join("\n");
  assert.deepEqual(parse(quoted), parse(csv));
});
test("missing, duplicated or unknown columns fail", () => {
  assert.throws(() => parse(csv.replace("lead_time", "hotel")));
  assert.throws(() => parse(csv.replace("lead_time", "guest_name")));
  assert.throws(() => parse(csv.replace(",arrival_month", "")));
});
test("no partial acceptance of invalid rows", () => {
  const lines = csv.trim().split("\n");
  assert.throws(() =>
    parse(lines[0] + "\n" + lines[1] + "\n" + lines[2] + ",extra"),
  );
  assert.throws(() => parse(lines[0] + "\n" + lines[1].replace(/^\d+/, "")));
});
test("empty, oversized and malformed quoted files fail", () => {
  const [header, row] = csv.trim().split("\n");
  assert.throws(() => parse(header));
  assert.throws(() => parse(header + "\n" + Array(501).fill(row).join("\n")));
  assert.throws(() => parse(header + '\n"' + row));
  assert.equal(
    parse(header + "\n" + Array(500).fill(row).join("\n")).length,
    500,
  );
});
test("formula, fractional and nonfinite numeric values fail", () => {
  const [header, row] = csv.trim().split("\n");
  for (const bad of ["=1+1", "NaN", "Infinity", "2.5", "-1", "true"])
    assert.throws(() => parse(header + "\n" + row.replace(/^\d+/, bad)));
});

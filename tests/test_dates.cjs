/* Calendar arithmetic is tested as dates, independently of local time zones. */
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const D = require("../web/dates.js");
const fixtures = [
  ["2026-10-01", "2026-10-02", "2026-10-05", 1, 10, 2, 1],
  ["2026-12-01", "2026-12-31", "2027-01-04", 30, 12, 2, 2],
  ["2028-02-01", "2028-02-28", "2028-03-01", 27, 2, 0, 2],
  ["2026-03-01", "2026-03-07", "2026-03-09", 6, 3, 2, 0],
  ["2026-10-30", "2026-10-31", "2026-11-02", 1, 10, 2, 0],
];
test("date features count occupied nights and exclude checkout, including leap/year/DST boundaries", () => {
  for (const [
    booked_on,
    check_in,
    check_out,
    lead_time,
    arrival_month,
    stays_in_weekend_nights,
    stays_in_week_nights,
  ] of fixtures) {
    assert.deepEqual(D.features({ booked_on, check_in, check_out }), {
      lead_time,
      arrival_month,
      stays_in_weekend_nights,
      stays_in_week_nights,
    });
  }
});
test("invalid, missing, reversed and out-of-scope dates are rejected", () => {
  for (const value of [
    "2026-02-29",
    "2026-13-01",
    "0001-01-01",
    "2101-01-01",
    "2026-1-02",
    "",
    null,
  ])
    assert.throws(() => D.parse(value));
  for (const stay of [
    null,
    {},
    {
      booked_on: "2026-10-01",
      check_in: "2026-09-30",
      check_out: "2026-10-02",
    },
    {
      booked_on: "2026-10-01",
      check_in: "2026-12-01",
      check_out: "2026-12-02",
    },
    {
      booked_on: "2026-10-01",
      check_in: "2026-10-01",
      check_out: "2026-10-01",
    },
    {
      booked_on: "2026-10-01",
      check_in: "2026-10-01",
      check_out: "2026-11-01",
    },
  ])
    assert.throws(() => D.features(stay));
});
test("dates return identical values in Colombia and DST time zones", () => {
  const script = `const D=require('./web/dates.js');process.stdout.write(JSON.stringify(D.features({booked_on:'2026-03-01',check_in:'2026-03-07',check_out:'2026-03-09'})))`;
  const results = [
    "America/Bogota",
    "America/New_York",
    "Europe/Madrid",
    "Pacific/Auckland",
  ].map((TZ) =>
    execFileSync(process.execPath, ["-e", script], {
      env: { ...process.env, TZ },
      encoding: "utf8",
    }),
  );
  assert.equal(new Set(results).size, 1);
});

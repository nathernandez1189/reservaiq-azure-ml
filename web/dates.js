/* Calendar dates are evaluated at UTC midnight, never across local DST hours. */
(function (root) {
  "use strict";
  const DAY = 86400000;
  function parse(iso) {
    if (typeof iso !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(iso))
      throw Error("Elige una fecha válida.");
    const [year, month, day] = iso.split("-").map(Number),
      value = new Date(Date.UTC(year, month - 1, day));
    if (
      year < 1900 ||
      year > 2100 ||
      value.getUTCFullYear() !== year ||
      value.getUTCMonth() !== month - 1 ||
      value.getUTCDate() !== day
    )
      throw Error("Esa fecha no existe. Revisa el calendario.");
    return value;
  }
  const iso = (date) => date.toISOString().slice(0, 10);
  const add = (day, n) => iso(new Date(parse(day).getTime() + n * DAY));
  const difference = (first, last) => (parse(last) - parse(first)) / DAY;
  function today() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }
  function features(stay) {
    if (!stay || !stay.booked_on || !stay.check_in || !stay.check_out)
      throw Error("Elige primero la llegada y después la salida.");
    const lead = difference(stay.booked_on, stay.check_in),
      total = difference(stay.check_in, stay.check_out);
    if (lead < 0 || lead > 60)
      throw Error(
        "Elige una llegada entre 0 y 60 días después de crear la reserva.",
      );
    if (total < 1 || total > 30)
      throw Error(
        "La salida debe ser posterior a la llegada: de 1 a 30 noches.",
      );
    let weekend = 0;
    for (let i = 0; i < total; i++) {
      const day = parse(add(stay.check_in, i)).getUTCDay();
      if (day === 0 || day === 6) weekend++;
    }
    return {
      lead_time: lead,
      arrival_month: parse(stay.check_in).getUTCMonth() + 1,
      stays_in_weekend_nights: weekend,
      stays_in_week_nights: total - weekend,
    };
  }
  const format = (
    day,
    options = { day: "numeric", month: "short", year: "numeric" },
  ) => parse(day).toLocaleDateString("es-CO", { ...options, timeZone: "UTC" });
  const exports = { parse, iso, add, difference, today, features, format };
  if (typeof module !== "undefined" && module.exports) module.exports = exports;
  else root.ReservaDates = exports;
})(typeof globalThis !== "undefined" ? globalThis : this);

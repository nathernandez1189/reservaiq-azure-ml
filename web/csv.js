/* CSV is parsed as text. Never execute formula-looking cells. */
(function (root) {
  "use strict";
  const numeric = [
    "lead_time",
    "arrival_month",
    "stays_in_weekend_nights",
    "stays_in_week_nights",
  ];
  const required = [
    ...numeric,
    "hotel",
    "meal",
    "market_segment",
    "distribution_channel",
    "reserved_room_type",
    "customer_type",
  ];
  function records(text, delimiter) {
    let rows = [],
      row = [],
      field = "",
      quoted = false,
      closed = false;
    const cell = () => {
      row.push(field.trim());
      field = "";
      closed = false;
    };
    const line = () => {
      cell();
      if (row.some((v) => v !== "")) rows.push(row);
      row = [];
    };
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (quoted) {
        if (c === '"') {
          if (text[i + 1] === '"') {
            field += '"';
            i++;
          } else {
            quoted = false;
            closed = true;
          }
        } else field += c;
      } else if (c === delimiter) cell();
      else if (c === "\n" || c === "\r") {
        if (c === "\r" && text[i + 1] === "\n") i++;
        line();
      } else if (c === '"') {
        if (field.trim() || closed)
          throw Error("Hay comillas mal ubicadas en el CSV.");
        field = "";
        quoted = true;
      } else {
        if (closed && c.trim())
          throw Error("Hay texto después de una celda entre comillas.");
        field += c;
      }
    }
    if (quoted) throw Error("Hay una celda con comillas sin cerrar.");
    line();
    return rows;
  }
  function parse(text) {
    text = text.replace(/^\uFEFF/, "");
    let table;
    for (const delimiter of [",", ";"]) {
      let candidate;
      try {
        candidate = records(text, delimiter);
      } catch {
        continue;
      }
      const header = candidate[0] || [];
      if (
        header.length === 10 &&
        new Set(header).size === 10 &&
        required.every((k) => header.includes(k))
      ) {
        table = candidate;
        break;
      }
    }
    if (!table)
      throw Error(
        "El encabezado debe contener las diez columnas del ejemplo, separadas por comas o punto y coma.",
      );
    const header = table.shift();
    if (table.length < 1 || table.length > 500)
      throw Error("El archivo debe tener entre 1 y 500 reservas.");
    return table.map((values, index) => {
      if (values.length !== 10)
        throw Error(`Fila ${index + 1}: faltan o sobran columnas.`);
      const item = {};
      header.forEach((key, i) => {
        const value = values[i];
        if (!value) throw Error(`Fila ${index + 1}: falta ${key}.`);
        if (numeric.includes(key)) {
          if (!/^\d+$/.test(value))
            throw Error(`Fila ${index + 1}: ${key} debe ser un número entero.`);
          item[key] = Number(value);
        } else item[key] = value;
      });
      return item;
    });
  }
  if (typeof module !== "undefined" && module.exports)
    module.exports = { parse };
  else root.ReservaCSV = { parse };
})(typeof globalThis !== "undefined" ? globalThis : this);

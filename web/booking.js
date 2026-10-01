/* Small booking controller: calendar selection, progressive disclosure and review. */
(function (root) {
  "use strict";
  const D = root.ReservaDates,
    $ = (id) => document.getElementById(id);
  let mode = "calendar",
    step = 1,
    month = "",
    hooks = {},
    busy = false,
    focusDay = null;
  const numeric = [
    "lead_time",
    "arrival_month",
    "stays_in_weekend_nights",
    "stays_in_week_nights",
  ];
  const escape = (value) =>
    String(value).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const validDate = (value) => {
    try {
      D.parse(value);
      return true;
    } catch {
      return false;
    }
  };
  const safeDate = (value) => (validDate(value) ? value : "");
  const clampDate = (value) =>
    value < "1900-01-01"
      ? "1900-01-01"
      : value > "2100-12-31"
        ? "2100-12-31"
        : value;
  const monthStart = (day) => day.slice(0, 7) + "-01";
  function shiftMonth(day, n) {
    const date = D.parse(day);
    return D.iso(
      new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + n, 1)),
    );
  }
  function rawStay() {
    return {
      booked_on: $("booked-on").value,
      check_in: $("check-in").value,
      check_out: $("check-out").value,
    };
  }
  function getStay() {
    if (mode !== "calendar") return null;
    const stay = rawStay();
    D.features(stay);
    return stay;
  }
  function syncDates() {
    if (mode !== "calendar") return;
    try {
      const fields = D.features(rawStay());
      numeric.forEach((key) => ($(key).value = fields[key]));
    } catch {
      numeric.forEach((key) => ($(key).value = ""));
    }
  }
  function validateDates() {
    if (mode === "calendar") {
      D.features(rawStay());
      return;
    }
    const values = hooks.inputs();
    for (const key of numeric) {
      if (!$(key).value || !$(key).checkValidity())
        throw Error("Revisa el mes, la anticipación y las noches del ejemplo.");
    }
    const total = values.stays_in_weekend_nights + values.stays_in_week_nights;
    if (total < 1 || total > 30)
      throw Error("La estancia total debe sumar entre 1 y 30 noches.");
  }
  function validate() {
    try {
      validateDates();
      $("date-error").textContent = "";
      ["check-in", "check-out", "booked-on"].forEach((k) =>
        $(k).removeAttribute("aria-invalid"),
      );
      return true;
    } catch (error) {
      showStep(1, false);
      $("date-error").textContent = error.message;
      $("error").textContent = error.message;
      const target =
        mode === "calendar"
          ? !validDate($("booked-on").value)
            ? "booked-on"
            : !validDate($("check-in").value)
              ? "check-in"
              : "check-out"
          : "lead_time";
      $(target).setAttribute("aria-invalid", "true");
      $(target).focus();
      return false;
    }
  }
  function showStep(next, check = true) {
    if (busy) return;
    if (next > 1 && check && !validate()) return;
    step = next;
    for (let n = 1; n <= 3; n++) $("booking-step-" + n).hidden = n !== step;
    document.querySelectorAll("[data-step]").forEach((button) => {
      const n = Number(button.dataset.step);
      button.setAttribute("aria-current", n === step ? "step" : "false");
      button.classList.toggle("complete", n < step);
    });
    $("step-back").hidden = step === 1;
    $("step-next").hidden = step === 3;
    $("step-counter").textContent = `Paso ${step} de 3`;
    $("step-next").textContent =
      step === 1 ? "Continuar con los detalles →" : "Revisar mi reserva →";
    review();
    if (check)
      $("booking-step-" + step)
        .querySelector("h2")
        .focus({ preventScroll: true });
  }
  function bounds() {
    let booked = $("booked-on").value;
    try {
      D.parse(booked);
    } catch {
      booked = D.today();
    }
    const arrival = safeDate($("check-in").value);
    const choosingExit = arrival && !$("check-out").value;
    const min = choosingExit ? D.add(arrival, 1) : booked;
    const max = choosingExit ? D.add(arrival, 30) : D.add(booked, 60);
    return {
      min: clampDate(min),
      max: clampDate(max),
      booked,
      choosingExit,
    };
  }
  function renderCalendar() {
    const { min, max, booked, choosingExit } = bounds();
    $("check-in").min = booked;
    $("check-in").max = clampDate(D.add(booked, 60));
    $("check-out").min = safeDate($("check-in").value)
      ? clampDate(D.add($("check-in").value, 1))
      : booked;
    $("check-out").max = safeDate($("check-in").value)
      ? clampDate(D.add($("check-in").value, 30))
      : clampDate(D.add(booked, 90));
    $("calendar-prev").disabled = busy || month <= monthStart(booked);
    $("calendar-next").disabled =
      busy || shiftMonth(month, 1) > monthStart(max);
    $("calendar-prompt").textContent = choosingExit
      ? "Ahora elige el día de salida"
      : $("check-out").value
        ? "Tu estancia está seleccionada"
        : "Elige el día de llegada";
    const arrival = $("check-in").value,
      departure = $("check-out").value;
    let html = "";
    for (let i = 0; i < 2; i++) {
      const first = shiftMonth(month, i);
      if (!validDate(first)) break;
      const date = D.parse(first),
        offset = (date.getUTCDay() + 6) % 7;
      const count = new Date(
        Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 0),
      ).getUTCDate();
      let days = Array(offset)
        .fill('<span aria-hidden="true"></span>')
        .join("");
      for (let n = 1; n <= count; n++) {
        const day = first.slice(0, 8) + String(n).padStart(2, "0"),
          selected = day === arrival || day === departure;
        const disabled = busy || day < min || day > max;
        const label =
          D.format(day, {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric",
          }) +
          (day === arrival
            ? " · llegada seleccionada"
            : day === departure
              ? " · salida seleccionada"
              : "");
        days += `<button type="button" class="calendar-day ${selected ? "selected" : ""} ${arrival && departure && day > arrival && day < departure ? "in-range" : ""} ${day === D.today() ? "today" : ""}" data-date="${day}" aria-label="${label}" aria-pressed="${selected}" ${day === D.today() ? 'aria-current="date"' : ""} ${disabled ? "disabled" : ""} tabindex="-1">${n}</button>`;
      }
      html += `<div class="calendar-month" role="group" aria-label="${D.format(first, { month: "long", year: "numeric" })}"><h3>${D.format(first, { month: "long", year: "numeric" })}</h3><div class="calendar-week" aria-hidden="true">${["L", "M", "X", "J", "V", "S", "D"].map((d) => `<span>${d}</span>`).join("")}</div><div class="calendar-days">${days}</div></div>`;
    }
    $("calendar-months").innerHTML = html;
    const enabled = [
      ...$("calendar-months").querySelectorAll("button:not(:disabled)"),
    ];
    const tabStop =
      enabled.find((b) => b.dataset.date === focusDay) ||
      enabled.find((b) => b.dataset.date === arrival) ||
      enabled[0];
    if (tabStop) tabStop.tabIndex = 0;
    $("calendar-months")
      .querySelectorAll("[data-date]")
      .forEach((button) => {
        button.onclick = () => choose(button.dataset.date);
        button.onkeydown = (event) => navigateDay(event, button.dataset.date);
      });
  }
  function navigateDay(event, day) {
    const moves = {
      ArrowLeft: -1,
      ArrowRight: 1,
      ArrowUp: -7,
      ArrowDown: 7,
      Home: -((D.parse(day).getUTCDay() + 6) % 7),
      End: 6 - ((D.parse(day).getUTCDay() + 6) % 7),
    };
    let target;
    if (event.key in moves) target = D.add(day, moves[event.key]);
    else if (event.key === "PageUp" || event.key === "PageDown") {
      const first = clampDate(shiftMonth(day, event.key === "PageUp" ? -1 : 1)),
        last = new Date(
          Date.UTC(
            D.parse(first).getUTCFullYear(),
            D.parse(first).getUTCMonth() + 1,
            0,
          ),
        ).getUTCDate();
      target =
        first.slice(0, 8) +
        String(Math.min(D.parse(day).getUTCDate(), last)).padStart(2, "0");
    } else return;
    event.preventDefault();
    const { min, max } = bounds();
    target = target < min ? min : target > max ? max : target;
    month = monthStart(target);
    focusDay = target;
    renderCalendar();
    $("calendar-months")
      .querySelector(`[data-date="${target}"]`)
      ?.focus({ preventScroll: true });
  }
  function choose(day) {
    if (busy) return;
    const { choosingExit } = bounds();
    if (choosingExit) $("check-out").value = day;
    else {
      $("check-in").value = day;
      $("check-out").value = "";
    }
    focusDay = choosingExit ? day : clampDate(D.add(day, 1));
    month = monthStart(focusDay);
    changed(false);
    if (choosingExit) {
      $("step-next").focus({ preventScroll: true });
      return;
    }
    const next = focusDay;
    $("calendar-months")
      .querySelector(`[data-date="${next}"]:not(:disabled)`)
      ?.focus({ preventScroll: true });
  }
  function changed(moveMonth) {
    $("date-error").textContent = "";
    $("check-in").removeAttribute("aria-invalid");
    $("check-out").removeAttribute("aria-invalid");
    if (moveMonth)
      month = monthStart(
        safeDate($("check-in").value) ||
          safeDate($("booked-on").value) ||
          D.today(),
      );
    syncDates();
    hooks.edited();
    refresh();
    const s = rawStay();
    if (s.check_in && s.check_out) {
      try {
        D.features(s);
      } catch (e) {
        $("date-error").textContent = e.message;
        $("check-out").setAttribute("aria-invalid", "true");
      }
    }
  }
  function review() {
    const values = hooks.inputs(),
      total = values.stays_in_weekend_nights + values.stays_in_week_nights;
    let stay = null;
    try {
      stay = getStay();
    } catch {}
    const rows = [
      [
        "Referencia",
        $("reference").value || "Se asignará un código al guardar",
      ],
    ];
    if (stay)
      rows.push(
        ["Llegada", D.format(stay.check_in)],
        ["Salida", D.format(stay.check_out)],
        ["Duración", `${total} ${total === 1 ? "noche" : "noches"}`],
        ["Reserva creada el", D.format(stay.booked_on)],
      );
    else
      rows.push([
        "Estancia",
        mode === "calendar"
          ? "Fechas por elegir"
          : `${total} noches · ${values.lead_time} días de anticipación`,
      ]);
    for (const key of Object.keys(hooks.names).filter(
      (k) => !numeric.includes(k),
    ))
      rows.push([hooks.names[key], hooks.labels[values[key]] || values[key]]);
    $("review-summary").innerHTML = rows
      .map(
        ([title, value], i) =>
          `<div class="${i === 0 ? "wide" : ""}"><dt>${title}</dt><dd>${escape(value)}</dd></div>`,
      )
      .join("");
    $("derived-fields").innerHTML = Object.keys(hooks.names)
      .map((k) => `<span>${hooks.names[k]}: <b>${escape(values[k])}</b></span>`)
      .join("");
  }
  function refresh() {
    if (!hooks.inputs) return;
    $("calendar-mode").hidden = mode !== "calendar";
    $("historical-mode").hidden = mode === "calendar";
    numeric.forEach((k) => ($(k).disabled = busy || mode === "calendar"));
    ["booked-on", "check-in", "check-out"].forEach(
      (k) => ($(k).disabled = busy || mode !== "calendar"),
    );
    syncDates();
    let stay = null;
    try {
      stay = getStay();
    } catch {}
    const values = hooks.inputs(),
      nights = values.stays_in_weekend_nights + values.stays_in_week_nights;
    if (stay || mode === "historical") {
      $("stay-total").innerHTML =
        `<strong>${nights} ${nights === 1 ? "noche" : "noches"}</strong> · ${values.stays_in_week_nights} entre semana y ${values.stays_in_weekend_nights} de fin de semana · ${values.lead_time} días de anticipación`;
      $("itinerary-title").textContent =
        `${nights} ${nights === 1 ? "noche" : "noches"} en hotel ${values.hotel === "City Hotel" ? "urbano" : "vacacional"}`;
      $("itinerary-dates").textContent = stay
        ? `${D.format(stay.check_in)} → ${D.format(stay.check_out)}`
        : "Ejemplo sin fechas completas. Se conservan sus variables originales.";
      $("itinerary-facts").innerHTML =
        `<span>${values.lead_time} días de anticipación</span><span>${hooks.labels[values.meal] || values.meal}</span>`;
    } else {
      $("stay-total").textContent = $("check-in").value
        ? "Llegada elegida. Ahora selecciona la salida."
        : "Elige dos fechas para ver la duración.";
      $("itinerary-title").textContent = $("check-in").value
        ? "Falta elegir la salida"
        : "Empieza por las fechas";
      $("itinerary-dates").textContent = safeDate($("check-in").value)
        ? `Llegada: ${D.format($("check-in").value)}`
        : "Tu resumen se irá completando aquí.";
      $("itinerary-facts").textContent = "";
    }
    if (mode === "calendar") renderCalendar();
    review();
  }
  function reset(stay = null, historical = false) {
    mode = historical ? "historical" : "calendar";
    focusDay = null;
    step = 1;
    $("booked-on").value = stay?.booked_on || D.today();
    $("check-in").value = stay?.check_in || "";
    $("check-out").value = stay?.check_out || "";
    month = monthStart(stay?.check_in || $("booked-on").value);
    $("date-error").textContent = "";
    $("after-save").hidden = true;
    $("check-in").removeAttribute("aria-invalid");
    $("check-out").removeAttribute("aria-invalid");
    refresh();
    showStep(historical || stay ? 3 : 1, false);
  }
  function init(options) {
    hooks = options;
    $("check-in").oninput = () => {
      const start = $("check-in").value,
        end = $("check-out").value;
      if (
        validDate(start) &&
        validDate(end) &&
        (end <= start || D.difference(start, end) > 30)
      )
        $("check-out").value = "";
      changed(true);
    };
    $("check-out").oninput = () => changed(false);
    $("booked-on").oninput = () => {
      month = monthStart(safeDate($("booked-on").value) || D.today());
      changed(false);
    };
    $("clear-dates").onclick = () => {
      $("check-in").value = "";
      $("check-out").value = "";
      focusDay = null;
      changed(true);
      $("check-in").focus();
    };
    $("calendar-prev").onclick = () => {
      month = shiftMonth(month, -1);
      renderCalendar();
    };
    $("calendar-next").onclick = () => {
      month = shiftMonth(month, 1);
      renderCalendar();
    };
    $("use-calendar").onclick = () => {
      reset();
      hooks.edited();
    };
    $("step-next").onclick = () => showStep(step + 1);
    $("step-back").onclick = () => showStep(step - 1);
    document
      .querySelectorAll("[data-step]")
      .forEach(
        (button) =>
          (button.onclick = () => showStep(Number(button.dataset.step))),
      );
  }
  root.Booking = {
    init,
    reset,
    refresh,
    getStay,
    validate,
    showStep,
    getStep: () => step,
    setBusy(value) {
      busy = value;
      document
        .querySelectorAll("[data-step]")
        .forEach((b) => (b.disabled = value));
      if (!busy) refresh();
    },
  };
})(window);

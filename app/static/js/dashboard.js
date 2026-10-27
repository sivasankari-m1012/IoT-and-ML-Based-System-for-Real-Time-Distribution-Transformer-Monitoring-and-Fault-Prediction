(() => {
  const boot = JSON.parse(document.getElementById("boot").textContent);
  const TH = boot.thresholds;
  const API = "/api/v1";

  // Gauge scales + which direction is dangerous. Limits come from the server config.
  const METRICS = {
    temperature: { field: "temperature", label: "Temperature", unit: "°C", min: 0, max: 100, digits: 1,
                   dir: "above", warn: TH.temperature.warn, fault: TH.temperature.fault },
    voltage:     { field: "voltage", label: "Voltage", unit: "V", min: 0, max: 15, digits: 2,
                   dir: "below", warn: TH.voltage.warn_below, fault: TH.voltage.fault_below },
    current:     { field: "current", label: "Current", unit: "A", min: 0, max: 6, digits: 2,
                   dir: "above", warn: TH.current.warn, fault: TH.current.fault },
    oil:         { field: "oil_percentage", label: "Oil level", unit: "%", min: 0, max: 100, digits: 0,
                   dir: "below", warn: TH.oil.warn_below, fault: TH.oil.fault_below },
  };

  const $ = (sel, root = document) => root.querySelector(sel);
  const pct = (m, v) => Math.max(0, Math.min(100, ((v - m.min) / (m.max - m.min)) * 100));

  function trackGradient(m) {
    const w = pct(m, m.warn), f = pct(m, m.fault);
    return m.dir === "above"
      ? `linear-gradient(90deg, var(--ok) 0 ${w}%, var(--warn) ${w}% ${f}%, var(--fault) ${f}% 100%)`
      : `linear-gradient(90deg, var(--fault) 0 ${f}%, var(--warn) ${f}% ${w}%, var(--ok) ${w}% 100%)`;
  }

  // Build the static parts of each gauge once.
  for (const [key, m] of Object.entries(METRICS)) {
    const el = $(`.gauge[data-metric="${key}"]`);
    $(".track", el).style.background = trackGradient(m);
    $(".limits", el).textContent = m.dir === "above"
      ? `Warning from ${m.warn} ${m.unit}, fault from ${m.fault} ${m.unit}`
      : `Warning below ${m.warn} ${m.unit}, fault below ${m.fault} ${m.unit}`;
  }

  // ---- chart ----
  let currentTab = "temperature";
  const chart = new Chart($("#chart"), {
    type: "line",
    data: { labels: [], datasets: [
      { data: [], borderColor: "#2c5f8d", backgroundColor: "#2c5f8d", borderWidth: 2, pointRadius: 2, tension: 0.25 },
      { data: [], borderColor: "#b87800", borderDash: [6, 4], borderWidth: 1.5, pointRadius: 0 },
      { data: [], borderColor: "#b3261e", borderDash: [6, 4], borderWidth: 1.5, pointRadius: 0 },
    ] },
    options: {
      animation: false, responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { ticks: { maxTicksLimit: 7 }, grid: { display: false } } },
    },
  });
  let lastReadings = [];

  function drawChart() {
    const m = METRICS[currentTab];
    const labels = lastReadings.map(r => new Date(r.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
    chart.data.labels = labels;
    chart.data.datasets[0].data = lastReadings.map(r => r[m.field]);
    chart.data.datasets[0].label = `${m.label} (${m.unit})`;
    chart.data.datasets[1].data = labels.map(() => m.warn);
    chart.data.datasets[2].data = labels.map(() => m.fault);
    chart.update();
  }

  document.querySelectorAll(".tabs button").forEach(btn => btn.addEventListener("click", () => {
    currentTab = btn.dataset.tab;
    document.querySelectorAll(".tabs button").forEach(b => b.setAttribute("aria-pressed", String(b === btn)));
    drawChart();
  }));

  // ---- rendering ----
  function setState(state) { document.documentElement.dataset.state = state; }

  function renderLatest(r) {
    if (!r) { setState("empty"); return; }
    const age = (Date.now() - new Date(r.timestamp).getTime()) / 1000;
    const stale = age > boot.staleSeconds;
    setState(stale ? "offline" : r.status.toLowerCase());

    $("#state-word").textContent = stale ? "Offline" : ({ NORMAL: "Normal", WARNING: "Warning", FAULT: "Fault", OFF: "Power off" })[r.status];
    const ul = $("#reasons");
    ul.replaceChildren(...(stale
      ? [`No reading for ${humanAge(age)}. Check the ESP32 power and Wi-Fi.`, `Last known state: ${r.status.toLowerCase()}`]
      : r.reasons).map(text => Object.assign(document.createElement("li"), { textContent: text })));
    $("#when").textContent = `Last reading ${new Date(r.timestamp).toLocaleString()}` +
      (r.anomaly_score != null ? ` · anomaly score ${r.anomaly_score}` : "");

    const link = $("#link");
    link.className = "link " + (stale ? "stale" : "live");
    $("#link-text").textContent = stale ? `Device offline (${humanAge(age)})` : `Live · ${humanAge(age)} ago`;

    for (const [key, m] of Object.entries(METRICS)) {
      const el = $(`.gauge[data-metric="${key}"]`);
      const v = r[m.field];
      $(".num", el).textContent = v.toFixed(m.digits);
      const marker = $(".marker", el);
      marker.hidden = false;
      marker.style.left = pct(m, v) + "%";
    }
  }

  function renderRows(readings) {
    const body = $("#rows");
    body.replaceChildren(...readings.slice(-10).reverse().map(r => {
      const tr = document.createElement("tr");
      const cells = [
        new Date(r.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
        r.temperature.toFixed(1), r.voltage.toFixed(2), r.current.toFixed(2), r.oil_percentage.toFixed(0) + "%",
      ];
      cells.forEach(c => tr.appendChild(Object.assign(document.createElement("td"), { textContent: c })));
      const td = document.createElement("td");
      td.appendChild(Object.assign(document.createElement("span"), { className: "chip " + r.status, textContent: r.status }));
      tr.appendChild(td);
      return tr;
    }));
  }

  function renderAlerts(alerts) {
    const ul = $("#alerts");
    if (!alerts.length) {
      ul.replaceChildren(Object.assign(document.createElement("li"), { className: "muted", textContent: "No active alerts" }));
      return;
    }
    ul.replaceChildren(...alerts.map(a => {
      const li = Object.assign(document.createElement("li"), { className: a.severity, textContent: a.message });
      li.appendChild(Object.assign(document.createElement("time"), {
        dateTime: a.created_at, textContent: `${a.severity.toLowerCase()} · ${new Date(a.created_at).toLocaleString()}`,
      }));
      return li;
    }));
  }

  function humanAge(s) {
    s = Math.round(s);
    if (s < 60) return `${s} s`;
    if (s < 3600) return `${Math.round(s / 60)} min`;
    return `${(s / 3600).toFixed(1)} h`;
  }

  // ---- polling ----
  async function getJSON(url) {
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`${url} -> ${res.status}`);
    return res.json();
  }

  async function refresh() {
    try {
      const since = new Date(Date.now() - 3600 * 1000).toISOString();
      const [data, alerts] = await Promise.all([
        getJSON(`${API}/transformers/${boot.transformerId}/readings?limit=500&since=${encodeURIComponent(since)}`),
        getJSON(`${API}/alerts?transformer_id=${boot.transformerId}&active=true&limit=5`),
      ]);
      lastReadings = data ? data.readings : [];
      // Nothing in the last hour? Still show the most recent reading so the page is never blank.
      let latest = lastReadings.at(-1);
      if (!latest && data) latest = (await getJSON(`${API}/transformers/${boot.transformerId}/latest`)).reading;
      renderLatest(latest);
      renderRows(lastReadings.length ? lastReadings : (latest ? [latest] : []));
      renderAlerts(alerts ? alerts.alerts : []);
      drawChart();
    } catch (err) {
      console.error(err);
      $("#link").className = "link stale";
      $("#link-text").textContent = "Dashboard cannot reach the server";
    }
  }

  let timer = null;
  const start = () => { refresh(); timer = setInterval(refresh, boot.pollMs); };
  const stop = () => { clearInterval(timer); timer = null; };
  document.addEventListener("visibilitychange", () => (document.hidden ? stop() : (!timer && start())));
  start();
})();

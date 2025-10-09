const $ = (sel) => document.querySelector(sel);

const els = {
  btn: $("#predictButton"),
  input: $("#tickerInput"),
  status: $("#status"),
  list: $("#predictionList"),
  json: $("#jsonDump"),
  chart: $("#chart"),
  smooth: $("#smoothToggle"),
  meta: {
    ticker: $("#m-ticker"),
    updated: $("#m-updated"),
    start: $("#m-start"),
    end: $("#m-end"),
    change: $("#m-change"),
    changePct: $("#m-changePct"),
  },
};

function toast(kind, msg) {
  els.status.className = `toast ${kind} show`;
  els.status.textContent = msg;
}

function clearList() {
  els.list.innerHTML = '<li class="muted">—</li>';
}

function fmt(n, d = 2) {
  return Number(n).toFixed(d);
}

function drawChart(points, smooth = false) {
  const ctx = els.chart.getContext("2d");
  const w = els.chart.width, h = els.chart.height;
  ctx.clearRect(0, 0, w, h);

  if (!points || points.length === 0) {
    ctx.fillStyle = "#9ca3af";
    ctx.fillText("No data", 20, 24);
    return;
  }

  const prices = points.map(p => p.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const pad = 10;

  const x = (i) => pad + (i / (points.length - 1 || 1)) * (w - pad * 2);
  const y = (v) => h - pad - ((v - min) / (max - min || 1)) * (h - pad * 2);

  // grid
  ctx.strokeStyle = "rgba(148,163,184,.15)";
  ctx.lineWidth = 1;
  [0, 0.25, 0.5, 0.75, 1].forEach(t => {
    ctx.beginPath();
    const yy = pad + t * (h - pad * 2);
    ctx.moveTo(pad, yy);
    ctx.lineTo(w - pad, yy);
    ctx.stroke();
  });

  // line
  ctx.beginPath();
  ctx.lineWidth = 2;
  ctx.strokeStyle = "#6366f1";
  ctx.moveTo(x(0), y(prices[0]));
  for (let i = 1; i < points.length; i++) {
    if (smooth) {
      const x0 = x(i - 1), y0 = y(prices[i - 1]);
      const x1 = x(i), y1 = y(prices[i]);
      const cx = (x0 + x1) / 2;
      ctx.bezierCurveTo(cx, y0, cx, y1, x1, y1);
    } else {
      ctx.lineTo(x(i), y(prices[i]));
    }
  }
  ctx.stroke();

  // fill
  const grad = ctx.createLinearGradient(0, pad, 0, h - pad);
  grad.addColorStop(0, "rgba(99,102,241,.35)");
  grad.addColorStop(1, "rgba(99,102,241,0)");
  ctx.lineTo(w - pad, h - pad);
  ctx.lineTo(pad, h - pad);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();
}

function setLoading(isLoading) {
  els.btn.classList.toggle("loading", isLoading);
  els.btn.disabled = isLoading;
}

async function fetchPrediction() {
  const ticker = els.input.value.trim().toUpperCase();
  if (!ticker) {
    toast("err", "Please enter a ticker symbol.");
    return;
  }

  setLoading(true);
  clearList();
  toast("info", `Fetching prediction for ${ticker}…`);

  try {
    const days = 7;
    const url = `http://127.0.0.1:5000/predict?ticker=${ticker}&days=${days}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (data.error) {
      toast("err", `Error: ${data.error}`);
      drawChart([]);
      setLoading(false);
      return;
    }

    // Render meta
    els.meta.ticker.textContent = data.ticker ?? ticker;
    els.meta.updated.textContent = new Date().toLocaleString();
    els.list.innerHTML = "";

    const points = (data.predictions ?? []).map(p => ({
      date: p.date,
      price: Number(p.price),
    }));

    points.forEach(p => {
      const li = document.createElement("li");
      li.textContent = `Date: ${p.date} • $${fmt(p.price)}`;
      els.list.appendChild(li);
    });

    if (points.length) {
      const start = points[0].price;
      const end = points[points.length - 1].price;
      const delta = end - start;
      const pct = (delta / (start || 1)) * 100;

      els.meta.start.textContent = `$${fmt(start)}`;
      els.meta.end.textContent = `$${fmt(end)}`;
      els.meta.change.textContent = `${delta >= 0 ? "+" : ""}$${fmt(delta)}`;
      els.meta.changePct.textContent = `${delta >= 0 ? "+" : ""}${fmt(pct)}%`;
    } else {
      els.meta.start.textContent = els.meta.end.textContent =
      els.meta.change.textContent = els.meta.changePct.textContent = "—";
    }

    els.json.textContent = JSON.stringify(data, null, 2);
    drawChart(points, els.smooth.checked);
    toast("ok", `Prediction for ${data.ticker ?? ticker} retrieved successfully!`);
  } catch (err) {
    console.error(err);
    toast("err", `Failed to connect to the API. Is the backend running? (${err.message})`);
    drawChart([]);
  } finally {
    setLoading(false);
  }
}

// events
els.btn.addEventListener("click", fetchPrediction);
els.input.addEventListener("keydown", (e) => { if (e.key === "Enter") fetchPrediction(); });
els.smooth.addEventListener("change", () => {
  // re-render last response if available
  try {
    const obj = JSON.parse(els.json.textContent || "{}");
    const points = (obj.predictions || []).map(p => ({ date: p.date, price: Number(p.price) }));
    drawChart(points, els.smooth.checked);
  } catch {}
});

// initial empty chart
drawChart([]);
toast("info", "Ready. Enter a ticker and click Get Prediction.");

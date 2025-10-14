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

// ⚡️ NEW: Hardcoded demo data extracted from seed.sql (Last 7 prices used to simulate a prediction)
const DEMO_DATA = {
  // Lockheed Martin (LMT) data
  "LMT": {
    ticker: "LMT",
    updated: "2025-09-17",
    points: [
      { date: "2025-09-11", price: 421.15 },
      { date: "2025-09-12", price: 425.67 },
      { date: "2025-09-13 (Proj)", price: 426.50 }, // Simulated point
      { date: "2025-09-14 (Proj)", price: 427.45 }, // Simulated point
      { date: "2025-09-15", price: 427.89 },
      { date: "2025-09-16", price: 428.30 },
      { date: "2025-09-17", price: 429.85 }
    ]
  },
  // Raytheon (RTX) data
  "RTX": {
    ticker: "RTX",
    updated: "2025-09-17",
    points: [
      { date: "2025-09-11", price: 111.75 },
      { date: "2025-09-12", price: 112.85 },
      { date: "2025-09-13 (Proj)", price: 113.10 },
      { date: "2025-09-14 (Proj)", price: 113.50 },
      { date: "2025-09-15", price: 113.95 },
      { date: "2025-09-16", price: 113.80 },
      { date: "2025-09-17", price: 114.90 }
    ]
  },
  // Boeing (BA) data
  "BA": {
    ticker: "BA",
    updated: "2025-09-17",
    points: [
      { date: "2025-09-11", price: 173.25 },
      { date: "2025-09-12", price: 175.60 },
      { date: "2025-09-13 (Proj)", price: 176.50 },
      { date: "2025-09-14 (Proj)", price: 177.00 },
      { date: "2025-09-15", price: 177.85 },
      { date: "2025-09-16", price: 178.25 },
      { date: "2025-09-17", price: 180.35 }
    ]
  },
  // Default data for non-demo tickers
  "DEFAULT": {
    ticker: "—",
    updated: "—",
    points: []
  }
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

  const xStep = (w - pad * 2) / (points.length - 1);
  const yRange = max - min;
  const yScale = (h - pad * 2) / (yRange || 1);

  ctx.strokeStyle = "#4f46e5";
  ctx.lineWidth = 2;
  ctx.beginPath();

  const getPos = (i, price) => ({
    x: pad + i * xStep,
    y: h - pad - (price - min) * yScale,
  });

  const getPoint = (i) => getPos(i, points[i].price);

  // Line drawing
  const startPoint = getPoint(0);
  ctx.moveTo(startPoint.x, startPoint.y);

  if (smooth) {
    for (let i = 0; i < points.length - 1; i++) {
      const p1 = getPoint(i);
      const p2 = getPoint(i + 1);
      const ctrlX = (p1.x + p2.x) / 2;

      ctx.bezierCurveTo(ctrlX, p1.y, ctrlX, p2.y, p2.x, p2.y);
    }
  } else {
    for (let i = 1; i < points.length; i++) {
      const p = getPoint(i);
      ctx.lineTo(p.x, p.y);
    }
  }

  ctx.stroke();

  // Dots
  ctx.fillStyle = "#6366f1";
  points.forEach((_, i) => {
    const p = getPoint(i);
    ctx.beginPath();
    ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
    ctx.fill();
  });
}

function setLoading(isLoading) {
  els.btn.disabled = isLoading;
  els.input.disabled = isLoading;
  els.btn.textContent = isLoading ? "Fetching..." : "Predict";
}

function processData(data, ticker) {
  const points = data.points;
  const listHTML = points.map((p) => {
    const isProjected = p.date.includes('(Proj)');
    const priceStr = `$${fmt(p.price)}`;
    const style = isProjected ? 'style="font-style: italic; opacity: 0.8;"' : '';
    return `<li ${style}><b>${p.date.replace(' (Proj)', '')}:</b> ${priceStr}</li>`;
  }).join('');

  els.list.innerHTML = listHTML;
  els.meta.ticker.textContent = data.ticker ?? ticker;
  els.meta.updated.textContent = data.updated ?? "—";

  if (points && points.length > 1) {
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
  toast("ok", `Demo prediction for ${data.ticker ?? ticker} loaded successfully!`);
}

// ⚡️ NEW LOGIC: Use demo data instead of fetching from API
async function fetchPrediction() {
  const ticker = els.input.value.toUpperCase().trim();
  if (!ticker) {
    toast("err", "Please enter a stock ticker.");
    return;
  }
  clearList();
  setLoading(true);

  // Check for hardcoded demo data
  const data = DEMO_DATA[ticker] ?? DEMO_DATA.DEFAULT;

  if (data.ticker === "—") {
    toast("err", `Ticker '${ticker}' not available in demo data. Please try LMT, RTX, or BA.`);
    drawChart([]);
  } else {
    // Simulate network delay for a better demo experience
    setTimeout(() => {
      processData(data, ticker);
      setLoading(false);
    }, 500);
    return; // Exit here since we are using demo data
  }
  
  setLoading(false);
}

// events
els.btn.addEventListener("click", fetchPrediction);
els.input.addEventListener("keydown", (e) => { if (e.key === "Enter") fetchPrediction(); });
els.smooth.addEventListener("change", () => {
  // re-render last response if available
  try {
    const obj = JSON.parse(els.json.textContent || "{}");
    const points = obj.points || [];
    drawChart(points, els.smooth.checked);
  } catch (err) {
    // If json is empty or invalid, do nothing
  }
});
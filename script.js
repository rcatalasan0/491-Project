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

  const prices = points.map(p => p.predicted_price);
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

  const getPoint = (i) => getPos(i, points[i].predicted_price);

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

function processData(data) {
  const points = data.predictions;
  
  // Build list HTML
  const listHTML = points.map((p) => {
    const priceStr = `$${fmt(p.predicted_price)}`;
    return `<li><b>Day ${p.day}:</b> ${priceStr}</li>`;
  }).join('');

  els.list.innerHTML = listHTML;
  els.meta.ticker.textContent = data.ticker;
  els.meta.updated.textContent = new Date(data.generated_at).toLocaleString();

  if (points && points.length > 0) {
    const start = points[0].predicted_price;
    const end = points[points.length - 1].predicted_price;
    const delta = end - start;
    const pct = (delta / (start || 1)) * 100;

    els.meta.start.textContent = `$${fmt(start)}`;
    els.meta.end.textContent = `$${fmt(end)}`;
    els.meta.change.textContent = `${delta >= 0 ? "+" : ""}$${fmt(delta)}`;
    els.meta.changePct.textContent = `${delta >= 0 ? "+" : ""}${fmt(pct)}%`;
  }

  els.json.textContent = JSON.stringify(data, null, 2);
  drawChart(points, els.smooth.checked);
  toast("ok", `Prediction for ${data.ticker} loaded successfully!`);
}

async function fetchPrediction() {
  const ticker = els.input.value.toUpperCase().trim();
  if (!ticker) {
    toast("err", "Please enter a stock ticker.");
    return;
  }
  
  clearList();
  setLoading(true);
  toast("info", "Fetching prediction...");

  try {
    const response = await fetch(`http://127.0.0.1:5000/predict?ticker=${ticker}&days=7`);
    const data = await response.json();

    if (response.ok) {
      processData(data);
    } else {
      toast("err", data.error || "Failed to fetch prediction");
      drawChart([]);
    }
  } catch (error) {
    console.error("Fetch error:", error);
    toast("err", "Unable to connect to server. Make sure Flask is running.");
    drawChart([]);
  } finally {
    setLoading(false);
  }
}

// Event listeners
els.btn.addEventListener("click", fetchPrediction);
els.input.addEventListener("keydown", (e) => { 
  if (e.key === "Enter") fetchPrediction(); 
});

els.smooth.addEventListener("change", () => {
  try {
    const obj = JSON.parse(els.json.textContent || "{}");
    const points = obj.predictions || [];
    drawChart(points, els.smooth.checked);
  } catch (err) {
    // Ignore if no valid data
  }
});

// Initial message
toast("info", "Enter a ticker symbol to get started!");
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
    // ADDED: New element for next-day ML prediction
    nextPrice: $("#m-nextPrice"), 
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

  const getPos = (i, price) => ({
    x: pad + i * xStep,
    y: h - pad - (price - min) * yScale,
  });

  const getPoint = (i) => getPos(i, points[i].predicted_price);
  
  // --- START AREA FILL LOGIC ---
  ctx.beginPath();
  const startPoint = getPoint(0);
  ctx.moveTo(startPoint.x, startPoint.y);

  // 1. Define the line path
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

  // 2. Close the path by connecting to the bottom corners
  const lastPoint = getPoint(points.length - 1);
  ctx.lineTo(lastPoint.x, h - pad); // Line down to bottom right padding edge
  ctx.lineTo(pad, h - pad);          // Line across to bottom left padding edge
  ctx.closePath();                   // Line up to the start point (optional, but good practice)
  
  // 3. Create and apply the gradient fill
  const gradient = ctx.createLinearGradient(0, 0, 0, h);
  gradient.addColorStop(0, "rgba(99, 102, 241, 0.4)"); // Top color (Blue, 40% opacity)
  gradient.addColorStop(1, "rgba(99, 102, 241, 0.05)"); // Bottom color (Blue, 5% opacity)
  
  ctx.fillStyle = gradient;
  ctx.fill();
  // --- END AREA FILL LOGIC ---
  
  // --- LINE STROKE LOGIC (Redrawn over the fill for clarity) ---
  ctx.strokeStyle = "#4f46e5"; // Line color
  ctx.lineWidth = 2;
  
  // Need to start a new path for the line itself so the stroke doesn't include the bottom closure
  ctx.beginPath();
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
  // --- END LINE STROKE LOGIC ---


  // Dots - MODIFIED LOGIC
  const lastHistoricalIndex = points.length - 2; // Index of the 7th point (Day 7)
  const predictionIndex = points.length - 1;     // Index of the 8th point (Day 8/Forecast)
  
  // Get prices for comparison
  const lastHistoricalPrice = points[lastHistoricalIndex]?.predicted_price;
  const predictionPrice = points[predictionIndex]?.predicted_price;
  
  points.forEach((_, i) => {
    const p = getPoint(i);
    let dotColor = "#6366f1"; // Default color for historical data (original blue)

    if (i === lastHistoricalIndex) {
      // Point 7 (last historical point) is colored white
      dotColor = "white";
    } else if (i === predictionIndex) {
      // Point 8 (prediction/forecast point) is colored based on change from point 7
      if (predictionPrice > lastHistoricalPrice) {
        dotColor = "#10b981"; // Green (e.g., emerald-500 from Tailwind)
      } else if (predictionPrice < lastHistoricalPrice) {
        dotColor = "#ef4444"; // Red (e.g., red-500 from Tailwind)
      } else {
        dotColor = "#6366f1"; // Blue/Default (if prices are exactly the same)
      }
    }
    
    ctx.fillStyle = dotColor;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 4, 0, Math.PI * 2); // Increased radius to 4 for better visibility of the highlighted dots
    ctx.fill();
  });
}

function setLoading(isLoading) {
  els.btn.disabled = isLoading;
  els.input.disabled = isLoading;
  els.btn.textContent = isLoading ? "Fetching..." : "Predict";
}

function processData(data) {
  // The last point in the 'predictions' array is the ML forecast
  const points = data.predictions;
  const predictionPoint = points.length > 0 ? points[points.length - 1] : null;

  // Build list HTML (Historical + Prediction)
  const listHTML = points.map((p) => {
    const isPrediction = p === predictionPoint;
    // Check if 'day' is present (added in app.py update)
    const dayStr = p.day ? ` (Day ${p.day})` : ''; 
    const priceStr = `$${fmt(p.predicted_price)}`;
    // Highlight the prediction point in the list
    return `<li class="${isPrediction ? 'highlight' : ''}"><b>${p.date}${dayStr}:</b> ${priceStr} ${isPrediction ? '<span class="badge small">Forecast</span>' : ''}</li>`;
  }).join('');

  els.list.innerHTML = listHTML;
  els.meta.ticker.textContent = data.ticker;
  els.meta.updated.textContent = new Date(data.generated_at).toLocaleString();

  // Clear or populate meta data
  if (points && points.length > 0) {
    // The historical data ends one point before the forecast
    const historicalPoints = points.slice(0, -1);
    
    // UPDATED: Set the Next Day Prediction Price
    if (predictionPoint) {
      els.meta.nextPrice.textContent = `$${fmt(predictionPoint.predicted_price)}`;
      els.meta.nextPrice.title = `Forecast for ${predictionPoint.date}`;
    } else {
      els.meta.nextPrice.textContent = '—';
      els.meta.nextPrice.title = '';
    }

    // Check if there is enough historical data for start/end comparison
    if (historicalPoints.length > 0) {
      const start = historicalPoints[0].predicted_price;
      const end = historicalPoints[historicalPoints.length - 1].predicted_price;
      const delta = predictionPoint.predicted_price - end; // Compare forecast to last historical price
      const pct = (delta / (end || 1)) * 100;

      els.meta.start.textContent = `$${fmt(start)}`;
      els.meta.end.textContent = `$${fmt(end)}`;
      
      // Check if the prediction has a positive or negative change to apply color (optional, but good UX)
      const changeClass = delta >= 0 ? 'ok' : 'err';
      
      els.meta.change.innerHTML = `<span class="${changeClass}">${delta >= 0 ? "+" : ""}$${fmt(delta)}</span>`;
      els.meta.changePct.innerHTML = `<span class="${changeClass}">${delta >= 0 ? "+" : ""}${fmt(pct)}%</span>`;
      
      // Also update start and end dates in the meta
      els.meta.start.title = historicalPoints[0].date; 
      els.meta.end.title = historicalPoints[historicalPoints.length - 1].date; 
    }

  } else {
    // Clear metadata if no points
    els.meta.start.textContent = '—';
    els.meta.end.textContent = '—';
    els.meta.change.textContent = '—';
    els.meta.changePct.textContent = '—';
    els.meta.nextPrice.textContent = '—'; // Clear the new element
  }

  els.json.textContent = JSON.stringify(data, null, 2);
  drawChart(points, els.smooth.checked);
  toast("ok", `Forecast for ${data.ticker} loaded successfully!`);
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
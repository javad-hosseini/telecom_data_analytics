/* =========================================================
   CHARTS
   Thin wrapper around Chart.js so dashboard.js just passes data.
   ========================================================= */

const Charts = (() => {

  const instances = {};

  const palette = {
    blue: "#4C8DFF",
    cyan: "#33D6E6",
    purple: "#9B6CFF",
    emerald: "#35D69A",
    amber: "#F5B34C",
    red: "#FF6B6B",
    grid: "rgba(255,255,255,0.06)",
    text: "#9AA6BD"
  };

  const colorCycle = [palette.blue, palette.cyan, palette.purple, palette.emerald, palette.amber, palette.red];

  Chart.defaults.font.family = "'Vazirmatn','Manrope',sans-serif";
  Chart.defaults.color = palette.text;
  Chart.defaults.font.size = 11.5;

  function baseOptions(overrides = {}) {
    return Object.assign({
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 650, easing: "easeOutQuart" },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(19,28,47,0.95)",
          borderColor: "rgba(255,255,255,0.1)",
          borderWidth: 1,
          padding: 10,
          titleFont: { weight: "700" },
          rtl: true
        }
      },
      scales: {
        x: { grid: { color: palette.grid, drawTicks: false }, border: { display: false } },
        y: { grid: { color: palette.grid, drawTicks: false }, border: { display: false }, beginAtZero: true }
      }
    }, overrides);
  }

  function gradient(ctx, color) {
    const g = ctx.createLinearGradient(0, 0, 0, 240);
    g.addColorStop(0, color + "AA");
    g.addColorStop(1, color + "05");
    return g;
  }

  function upsertBar(canvasId, labels, data, color = palette.blue, horizontal = false) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    if (instances[canvasId]) instances[canvasId].destroy();

    instances[canvasId] = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: gradient(ctx, color),
          borderRadius: 8,
          borderSkipped: false,
          barThickness: horizontal ? 14 : 22,
          maxBarThickness: 26
        }]
      },
      options: Object.assign(baseOptions(), {
        indexAxis: horizontal ? "y" : "x",
        scales: horizontal
          ? { x: { grid: { color: palette.grid }, beginAtZero: true }, y: { grid: { display: false } } }
          : baseOptions().scales
      })
    });
  }

  function upsertLine(canvasId, labels, data, color = palette.cyan) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    if (instances[canvasId]) instances[canvasId].destroy();

    instances[canvasId] = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          data,
          borderColor: color,
          backgroundColor: gradient(ctx, color),
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: color,
          borderWidth: 2.5
        }]
      },
      options: baseOptions()
    });
  }

  function upsertDoughnut(canvasId, labels, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    if (instances[canvasId]) instances[canvasId].destroy();

    instances[canvasId] = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: colorCycle,
          borderColor: "rgba(11,15,25,0.9)",
          borderWidth: 3,
          hoverOffset: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "68%",
        animation: { duration: 650, easing: "easeOutQuart" },
        plugins: {
          legend: {
            display: true,
            position: "bottom",
            rtl: true,
            labels: { color: palette.text, boxWidth: 10, boxHeight: 10, padding: 14, font: { size: 11 } }
          },
          tooltip: {
            backgroundColor: "rgba(19,28,47,0.95)",
            borderColor: "rgba(255,255,255,0.1)",
            borderWidth: 1,
            rtl: true
          }
        }
      }
    });
  }

  function destroyAll() {
    Object.values(instances).forEach(c => c && c.destroy());
  }

  return { upsertBar, upsertLine, upsertDoughnut, destroyAll, palette, colorCycle };
})();

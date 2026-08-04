/* =========================================================
   DASHBOARD
   Fetches data for each view and renders KPI cards, charts,
   partition cards and health status.
   ========================================================= */

const Dashboard = (() => {

  const kpiGrid = document.getElementById("kpiGrid");

  const kpiDefs = [
    { key: "total_events", label: "کل رویدادها", icon: "activity", color: "blue", suffix: "" },
    { key: "avg_latency", label: "میانگین تأخیر", icon: "timer", color: "cyan", suffix: " ms", decimals: 1 },
    { key: "avg_speed", label: "میانگین سرعت دانلود", icon: "download", color: "emerald", suffix: " Mbps", decimals: 1 },
    { key: "avg_packet_loss", label: "میانگین افت پکت", icon: "wifi-off", color: "red", suffix: "%", decimals: 2 },
    { key: "apps", label: "اپلیکیشن‌های فعال", icon: "smartphone", color: "purple", suffix: "" },
    { key: "devices", label: "دستگاه‌های فعال", icon: "tablet-smartphone", color: "amber", suffix: "" },
    { key: "networks", label: "انواع شبکه", icon: "signal", color: "blue", suffix: "" },
    { key: "cities", label: "شهرهای فعال", icon: "map-pin", color: "cyan", suffix: "" }
  ];

  function renderKpiSkeleton() {
    kpiGrid.innerHTML = kpiDefs.map(def => `
      <div class="kpi-card">
        <div class="kpi-top">
          <div class="kpi-icon ${def.color}"><i data-lucide="${def.icon}"></i></div>
        </div>
        <div class="skel-bar" style="width:70%;height:22px;margin-top:4px;"></div>
        <div class="kpi-label">${def.label}</div>
      </div>
    `).join("");
    if (window.lucide) lucide.createIcons();
  }

  function renderKpis(values) {
    kpiGrid.innerHTML = kpiDefs.map(def => {
      const raw = values[def.key];
      const display = def.decimals
        ? (raw != null ? Utils.formatDecimal(raw, def.decimals) : "—")
        : (raw != null ? Utils.formatNumber(raw) : "—");
      return `
        <div class="kpi-card">
          <div class="kpi-top">
            <div class="kpi-icon ${def.color}"><i data-lucide="${def.icon}"></i></div>
          </div>
          <div class="kpi-value">${display}${def.suffix}</div>
          <div class="kpi-label">${def.label}</div>
        </div>
      `;
    }).join("");
    if (window.lucide) lucide.createIcons();
  }

  function weightedAvg(rows, valueKey, weightKey) {
    const totalWeight = rows.reduce((s, r) => s + (r[weightKey] || 0), 0);
    if (!totalWeight) return null;
    const sum = rows.reduce((s, r) => s + (r[valueKey] || 0) * (r[weightKey] || 0), 0);
    return sum / totalWeight;
  }

  // ---------------------------------------------------------
  // OVERVIEW
  // ---------------------------------------------------------
  async function loadOverview() {
    renderKpiSkeleton();

    const results = await Promise.allSettled([
      Api.eventsCount(),
      Api.networkQuality(),
      Api.topApps(100),
      Api.deviceStats(),
      Api.cityStats(50),
      Api.hourlyHeatmap(7)
    ]);

    const [countRes, netRes, appsRes, devicesRes, citiesRes, hourlyRes] = results;

    const totalEvents = countRes.status === "fulfilled" ? countRes.value.total_events : null;
    const netQuality = netRes.status === "fulfilled" ? netRes.value : [];
    const topApps = appsRes.status === "fulfilled" ? appsRes.value : [];
    const devices = devicesRes.status === "fulfilled" ? devicesRes.value : [];
    const cities = citiesRes.status === "fulfilled" ? citiesRes.value : [];
    const hourly = hourlyRes.status === "fulfilled" ? hourlyRes.value : [];

    renderKpis({
      total_events: totalEvents,
      avg_latency: weightedAvg(netQuality, "avg_latency", "total_events"),
      avg_speed: weightedAvg(netQuality, "avg_speed", "total_events"),
      avg_packet_loss: weightedAvg(netQuality, "avg_packet_loss", "total_events"),
      apps: topApps.length,
      devices: devices.length,
      networks: netQuality.length,
      cities: cities.length
    });

    // Top apps chart (top 8)
    const topAppsSlice = topApps.slice(0, 8);
    Charts.upsertBar("chartTopApps",
      topAppsSlice.map(a => a.app_name),
      topAppsSlice.map(a => a.event_count),
      Charts.palette.blue, true);

    // Network quality (latency) doughnut-ish -> bar by network type
    Charts.upsertBar("chartNetworkQuality",
      netQuality.map(n => n.network_type),
      netQuality.map(n => Number(n.avg_latency.toFixed(1))),
      Charts.palette.purple);

    // Hourly heatmap (line)
    const hourlyLabels = hourly.map(h => `${h.hour}:00`);
    Charts.upsertLine("chartHourly", hourlyLabels, hourly.map(h => h.event_count), Charts.palette.cyan);

    // Cities (top 6, doughnut)
    const topCities = cities.slice(0, 6);
    Charts.upsertDoughnut("chartCities", topCities.map(c => c.city), topCities.map(c => c.event_count));

    // Devices (top 6, bar)
    const topDevices = devices.slice(0, 6);
    Charts.upsertBar("chartDevices", topDevices.map(d => d.device), topDevices.map(d => d.event_count), Charts.palette.emerald, true);
  }

  // ---------------------------------------------------------
  // ANALYTICS
  // ---------------------------------------------------------
  async function loadAnalytics(days = 7) {
    const results = await Promise.allSettled([
      Api.topApps(10),
      Api.networkQuality(),
      Api.hourlyHeatmap(days),
      Api.deviceStats(),
      Api.cityStats(10)
    ]);

    const [appsRes, netRes, hourlyRes, devicesRes, citiesRes] = results;

    if (appsRes.status === "fulfilled") {
      const apps = appsRes.value;
      Charts.upsertBar("chartAnalyticsApps", apps.map(a => a.app_name), apps.map(a => a.event_count), Charts.palette.blue, true);
    }

    if (netRes.status === "fulfilled") {
      const net = netRes.value;
      Charts.upsertBar("chartPacketLoss", net.map(n => n.network_type), net.map(n => Number(n.avg_packet_loss.toFixed(2))), Charts.palette.red);
    }

    if (hourlyRes.status === "fulfilled") {
      const hourly = hourlyRes.value;
      Charts.upsertLine("chartAnalyticsHourly", hourly.map(h => `${h.hour}:00`), hourly.map(h => h.event_count), Charts.palette.cyan);
    }

    if (devicesRes.status === "fulfilled") {
      const devices = devicesRes.value.slice(0, 8);
      Charts.upsertBar("chartDeviceSpeed", devices.map(d => d.device), devices.map(d => Number(d.avg_speed.toFixed(1))), Charts.palette.emerald, true);
    }

    if (citiesRes.status === "fulfilled") {
      const cities = citiesRes.value;
      Charts.upsertDoughnut("chartCityUsers", cities.map(c => c.city), cities.map(c => c.unique_users));
    }
  }

  // ---------------------------------------------------------
  // PARTITIONS
  // ---------------------------------------------------------
  async function loadPartitions() {
    const grid = document.getElementById("partitionsGrid");
    grid.innerHTML = Array.from({ length: 4 }).map(() => `
      <div class="partition-card">
        <div class="skel-bar" style="width:50%;height:18px;"></div>
        <div class="skel-bar" style="width:80%;height:12px;"></div>
        <div class="skel-bar" style="width:65%;height:12px;"></div>
      </div>
    `).join("");

    try {
      const data = await Api.partitionStatus();
      const partitions = (data && data.partitions) || [];

      if (partitions.length === 0) {
        grid.innerHTML = `<div class="table-empty" style="grid-column:1/-1;">
          <i data-lucide="layers"></i><p>پارتیشنی یافت نشد</p>
        </div>`;
        if (window.lucide) lucide.createIcons();
        return;
      }

      grid.innerHTML = partitions.map(p => `
        <div class="partition-card">
          <div class="partition-head">
            <span class="partition-name">${p.partition_name}</span>
            <div class="partition-icon"><i data-lucide="layers"></i></div>
          </div>
          <div class="partition-stat-row"><span>تعداد رکورد</span><span>${Utils.formatNumber(p.row_count)}</span></div>
          <div class="partition-stat-row"><span>حجم</span><span>${p.size_human}</span></div>
          <div class="partition-stat-row"><span>از</span><span>${Utils.formatDateTime(p.min_date)}</span></div>
          <div class="partition-stat-row"><span>تا</span><span>${Utils.formatDateTime(p.max_date)}</span></div>
          <div class="partition-footer">
            <button class="btn btn-danger-ghost" data-partition="${p.partition_name}">
              <i data-lucide="trash-2"></i> حذف پارتیشن
            </button>
          </div>
        </div>
      `).join("");

      if (window.lucide) lucide.createIcons();

      grid.querySelectorAll("[data-partition]").forEach(btn => {
        btn.addEventListener("click", () => dropPartition(btn.dataset.partition));
      });

    } catch (err) {
      grid.innerHTML = `<div class="table-empty" style="grid-column:1/-1;">
        <i data-lucide="alert-triangle"></i><p>خطا در دریافت پارتیشن‌ها</p>
      </div>`;
      if (window.lucide) lucide.createIcons();
      Utils.showToast("دریافت پارتیشن‌ها ناموفق بود: " + err.message, "error");
    }
  }

  async function dropPartition(yearMonth) {
    if (!confirm(`پارتیشن ${yearMonth} برای همیشه حذف شود؟`)) return;
    try {
      await Api.dropPartition(yearMonth);
      Utils.showToast(`پارتیشن ${yearMonth} حذف شد`, "success");
      loadPartitions();
    } catch (err) {
      Utils.showToast("حذف پارتیشن ناموفق بود: " + err.message, "error");
    }
  }

  async function cleanOldPartitions() {
    const months = Number(document.getElementById("cleanMonthsInput").value) || 6;
    try {
      const result = await Api.cleanPartitions(months);
      Utils.showToast(`${result.total_dropped} پارتیشن قدیمی پاکسازی شد`, "success");
      loadPartitions();
    } catch (err) {
      Utils.showToast("پاکسازی ناموفق بود: " + err.message, "error");
    }
  }

  // ---------------------------------------------------------
  // HEALTH
  // ---------------------------------------------------------
  async function loadHealth() {
    const overallText = document.getElementById("healthOverallText");
    const overallTs = document.getElementById("healthTimestamp");
    const overallIcon = document.getElementById("healthIcon");
    const overallCard = document.getElementById("healthOverallCard");
    const pulse = document.getElementById("healthPulse");

    const dbText = document.getElementById("healthDbText");
    const dbDetail = document.getElementById("healthDbDetail");
    const readyDetail = document.getElementById("healthReadyDetail");

    try {
      const health = await Api.health();
      const healthy = health.status === "healthy";

      overallText.textContent = healthy ? "سیستم سالم است" : "مشکلی در سیستم وجود دارد";
      overallTs.textContent = Utils.formatDateTime(health.timestamp);
      overallIcon.setAttribute("data-lucide", healthy ? "check-circle" : "alert-triangle");

      const badge = overallCard.querySelector(".health-badge");
      badge.style.background = healthy ? "rgba(53,214,154,0.12)" : "rgba(255,107,107,0.12)";
      badge.style.color = healthy ? "var(--accent-emerald)" : "var(--accent-red)";
      pulse.style.borderColor = healthy ? "var(--accent-emerald)" : "var(--accent-red)";

      const ch = health.services && health.services.clickhouse;
      if (ch) {
        dbText.textContent = ch.version ? `ClickHouse ${ch.version}` : "ClickHouse";
        dbDetail.textContent = ch.status === "healthy" ? "متصل و سالم" : (ch.message || "خطا در اتصال");
      }

      setStatusChip(healthy);

    } catch (err) {
      overallText.textContent = "امکان دریافت وضعیت سلامت نبود";
      overallTs.textContent = "—";
      setStatusChip(false);
    }

    try {
      const ready = await Api.ready();
      readyDetail.textContent = ready.status === "ready" ? "آماده‌ی دریافت ترافیک" : (ready.error || "آماده نیست");
    } catch {
      readyDetail.textContent = "خطا در بررسی آمادگی";
    }

    if (window.lucide) lucide.createIcons();
  }

  function setStatusChip(healthy) {
    const dot = document.getElementById("apiStatusDot");
    const text = document.getElementById("apiStatusText");
    const sidebarDot = document.querySelector("#sidebarStatus .dot");
    const sidebarText = document.querySelector("#sidebarStatus .mini-status-text");

    dot.className = "dot " + (healthy ? "dot-ok" : "dot-bad");
    text.textContent = healthy ? "متصل" : "قطع ارتباط";
    if (sidebarDot) sidebarDot.className = "dot " + (healthy ? "dot-ok" : "dot-bad");
    if (sidebarText) sidebarText.textContent = healthy ? "API متصل است" : "خطا در اتصال به API";
  }

  return {
    loadOverview,
    loadAnalytics,
    loadPartitions,
    loadHealth,
    cleanOldPartitions,
    setStatusChip
  };
})();

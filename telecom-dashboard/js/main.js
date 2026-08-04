/* =========================================================
   MAIN — app bootstrap & navigation
   ========================================================= */

(() => {

  const viewMeta = {
    overview: { title: "نمای کلی", sub: "وضعیت زنده‌ی شبکه در یک نگاه" },
    events: { title: "رویدادها", sub: "کاوش در رویدادهای خام شبکه" },
    analytics: { title: "تحلیل‌ها", sub: "گزارش‌های آماری و روندها" },
    partitions: { title: "پارتیشن‌ها", sub: "مدیریت پارتیشن‌های ماهانه‌ی ClickHouse" },
    health: { title: "سلامت سیستم", sub: "وضعیت اتصال و آمادگی سرویس" },
    settings: { title: "تنظیمات", sub: "پیکربندی آدرس API" }
  };

  const loadedViews = new Set();

  function switchView(view) {
    document.querySelectorAll(".nav-item").forEach(btn =>
      btn.classList.toggle("active", btn.dataset.view === view)
    );
    document.querySelectorAll(".view").forEach(section =>
      section.classList.toggle("active", section.id === `view-${view}`)
    );

    document.getElementById("viewTitle").textContent = viewMeta[view].title;
    document.getElementById("viewSubtitle").textContent = viewMeta[view].sub;

    document.getElementById("sidebar").classList.remove("open");

    loadViewData(view);
  }

  function loadViewData(view, force = false) {
    if (!force && loadedViews.has(view)) return;
    loadedViews.add(view);

    switch (view) {
      case "overview": Dashboard.loadOverview(); break;
      case "events": EventsTable.reload(); break;
      case "analytics":
        Dashboard.loadAnalytics(Number(document.getElementById("hourlyDaysSelect").value));
        break;
      case "partitions": Dashboard.loadPartitions(); break;
      case "health": Dashboard.loadHealth(); break;
    }
  }

  function refreshCurrentView() {
    const active = document.querySelector(".nav-item.active");
    const view = active ? active.dataset.view : "overview";
    const btn = document.getElementById("refreshBtn");
    btn.classList.add("spinning");
    loadViewData(view, true);
    Dashboard.loadHealth(); // keep status chip fresh on every manual refresh
    setTimeout(() => btn.classList.remove("spinning"), 700);
  }

  function startClock() {
    const clockText = document.getElementById("clockText");
    function tick() { clockText.textContent = Utils.formatClock(new Date()); }
    tick();
    setInterval(tick, 1000);
  }

  function bindNav() {
    document.querySelectorAll(".nav-item").forEach(btn => {
      btn.addEventListener("click", () => switchView(btn.dataset.view));
    });

    document.getElementById("menuToggle").addEventListener("click", () => {
      document.getElementById("sidebar").classList.toggle("open");
    });

    document.getElementById("refreshBtn").addEventListener("click", refreshCurrentView);

    document.getElementById("hourlyDaysSelect").addEventListener("change", e => {
      Dashboard.loadAnalytics(Number(e.target.value));
    });

    document.getElementById("cleanPartitionsBtn").addEventListener("click", () => {
      Dashboard.cleanOldPartitions();
    });

    document.getElementById("partitionsRefreshBtn").addEventListener("click", () => {
      Dashboard.loadPartitions();
    });
  }

  function bindSettings() {
    const input = document.getElementById("apiBaseInput");
    input.value = Api.getBaseUrl();

    document.getElementById("saveSettingsBtn").addEventListener("click", async () => {
      const value = input.value.trim();
      if (!value) {
        Utils.showToast("آدرس معتبر وارد کنید", "error");
        return;
      }
      Api.setBaseUrl(value);
      Utils.showToast("در حال تست اتصال...", "info");
      try {
        const health = await Api.health();
        Dashboard.setStatusChip(health.status === "healthy");
        Utils.showToast("اتصال با موفقیت برقرار شد", "success");
        loadedViews.clear();
        loadViewData("overview", true);
      } catch (err) {
        Dashboard.setStatusChip(false);
        Utils.showToast("اتصال ناموفق بود: " + err.message, "error");
      }
    });
  }

  function init() {
    if (window.lucide) lucide.createIcons();

    bindNav();
    bindSettings();
    startClock();

    EventsTable.init();
    Dashboard.loadHealth();
    loadViewData("overview");

    // periodic background refresh of health/status only
    setInterval(() => Dashboard.loadHealth(), 30000);
  }

  document.addEventListener("DOMContentLoaded", init);
})();

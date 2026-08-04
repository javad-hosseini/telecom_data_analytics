/* =========================================================
   UTILITIES
   ========================================================= */

const Utils = (() => {

  function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return "—";
    return new Intl.NumberFormat("en-US").format(num);
  }

  function formatDecimal(num, digits = 1) {
    if (num === null || num === undefined || isNaN(num)) return "—";
    return Number(num).toFixed(digits);
  }

  function formatDateTime(value) {
    if (!value) return "—";
    try {
      const d = new Date(value);
      if (isNaN(d.getTime())) return String(value);
      return d.toLocaleString("fa-IR", {
        year: "numeric", month: "2-digit", day: "2-digit",
        hour: "2-digit", minute: "2-digit", second: "2-digit"
      });
    } catch {
      return String(value);
    }
  }

  function formatClock(date) {
    return date.toLocaleTimeString("en-GB", { hour12: false });
  }

  function debounce(fn, delay = 300) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), delay);
    };
  }

  function networkBadgeClass(networkType) {
    if (!networkType) return "net-other";
    const n = String(networkType).toUpperCase();
    if (n.includes("5G")) return "net-5g";
    if (n.includes("4G")) return "net-4g";
    if (n.includes("3G") || n.includes("2G")) return "net-3g";
    if (n.includes("WIFI") || n.includes("WI-FI")) return "net-wifi";
    return "net-other";
  }

  function animateCount(el, target, opts = {}) {
    const duration = opts.duration || 900;
    const decimals = opts.decimals || 0;
    const start = 0;
    const startTime = performance.now();

    function step(now) {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = start + (target - start) * eased;
      el.textContent = decimals > 0
        ? Number(value).toFixed(decimals)
        : formatNumber(Math.round(value));
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  function showToast(message, type = "info") {
    const stack = document.getElementById("toastStack");
    if (!stack) return;

    const icons = { success: "check-circle-2", error: "alert-circle", info: "info" };
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i data-lucide="${icons[type] || "info"}"></i><span>${message}</span>`;
    stack.appendChild(toast);

    if (window.lucide) lucide.createIcons();

    setTimeout(() => {
      toast.style.transition = "opacity .3s ease, transform .3s ease";
      toast.style.opacity = "0";
      toast.style.transform = "translateY(8px)";
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function el(tag, className, html) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (html !== undefined) node.innerHTML = html;
    return node;
  }

  return {
    formatNumber,
    formatDecimal,
    formatDateTime,
    formatClock,
    debounce,
    networkBadgeClass,
    animateCount,
    showToast,
    el
  };
})();

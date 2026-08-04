/* =========================================================
   API LAYER
   Single source of truth for talking to the FastAPI backend.
   Every endpoint below matches Docs.json exactly.
   ========================================================= */

const Api = (() => {

  const STORAGE_KEY = "telecom_api_base_url";
  let baseUrl = localStorage.getItem(STORAGE_KEY) || "http://localhost:8000";

  function getBaseUrl() {
    return baseUrl;
  }

  function setBaseUrl(url) {
    baseUrl = url.replace(/\/+$/, "");
    localStorage.setItem(STORAGE_KEY, baseUrl);
  }

  /**
   * Core request function: handles timeout, retry, JSON parsing and
   * unwraps the backend's { status, message, data, errors, timestamp } envelope.
   */
  async function request(path, { method = "GET", params = null, timeout = 10000, retries = 1 } = {}) {
    let url = `${baseUrl}${path}`;

    if (params) {
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== "") qs.append(k, v);
      });
      const qsString = qs.toString();
      if (qsString) url += `?${qsString}`;
    }

    let lastError;

    for (let attempt = 0; attempt <= retries; attempt++) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeout);

      try {
        const res = await fetch(url, {
          method,
          headers: { "Accept": "application/json" },
          signal: controller.signal
        });

        clearTimeout(timer);

        let body = null;
        try { body = await res.json(); } catch { body = null; }

        if (!res.ok) {
          const detail = body && (body.detail || body.message) || `HTTP ${res.status}`;
          throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
        }

        // Unwrap ApiResponse envelope if present, else return raw body
        if (body && typeof body === "object" && "data" in body) {
          return body.data;
        }
        return body;

      } catch (err) {
        clearTimeout(timer);
        lastError = err;
        if (attempt === retries) break;
        await new Promise(r => setTimeout(r, 400 * (attempt + 1)));
      }
    }

    throw lastError;
  }

  return {
    getBaseUrl,
    setBaseUrl,

    // ---------- Health ----------
    health: () => request("/health"),
    ready: () => request("/ready"),

    // ---------- Events ----------
    eventsCount: () => request("/api/events/count"),
    eventsSample: (limit = 10) => request("/api/events/sample", { params: { limit } }),
    userEvents: (userId, limit = 20, includeStats = false) =>
      request(`/api/events/user/${userId}`, { params: { limit, include_stats: includeStats } }),
    searchEvents: (query, limit = 50) =>
      request("/api/events/search", { method: "POST", params: { query, limit } }),

    // ---------- Analytics ----------
    topApps: (limit = 10) => request("/api/analytics/top-apps", { params: { limit } }),
    networkQuality: () => request("/api/analytics/network-quality"),
    hourlyHeatmap: (days = 7) => request("/api/analytics/hourly-heatmap", { params: { days } }),
    deviceStats: () => request("/api/analytics/device-stats"),
    cityStats: (limit = 10) => request("/api/analytics/city-stats", { params: { limit } }),

    // ---------- Partitions ----------
    partitionStatus: () => request("/api/partitions/status"),
    dropPartition: (yearMonth) => request(`/api/partitions/${yearMonth}`, { method: "DELETE" }),
    cleanPartitions: (months = 6) => request("/api/partitions/clean", { method: "POST", params: { months } })
  };
})();

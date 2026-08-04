/* =========================================================
   EVENTS TABLE
   Fetches a sample of raw events and provides client-side
   search / sort / pagination on top of it.
   ========================================================= */

const EventsTable = (() => {

  let allRows = [];      // raw rows from /api/events/sample
  let filteredRows = [];
  let sortKey = null;
  let sortDir = 1;
  let currentPage = 1;
  const pageSize = 12;
  const SAMPLE_SIZE = 100; // backend caps /api/events/sample at limit<=100

  const tbody = document.getElementById("eventsTableBody");
  const emptyState = document.getElementById("eventsEmptyState");
  const pagination = document.getElementById("eventsPagination");
  const countLabel = document.getElementById("eventsCountLabel");

  function renderSkeleton(rows = 6) {
    tbody.innerHTML = "";
    emptyState.hidden = true;
    for (let i = 0; i < rows; i++) {
      const tr = document.createElement("tr");
      tr.className = "skel-row";
      tr.innerHTML = Array.from({ length: 10 }).map(() =>
        `<td><div class="skel-bar" style="width:${60 + Math.random() * 40}%"></div></td>`
      ).join("");
      tbody.appendChild(tr);
    }
  }

  function networkBadge(value) {
    const cls = Utils.networkBadgeClass(value);
    return `<span class="badge-pill ${cls}">${value ?? "—"}</span>`;
  }

  function render() {
    const start = (currentPage - 1) * pageSize;
    const pageRows = filteredRows.slice(start, start + pageSize);

    tbody.innerHTML = "";

    if (pageRows.length === 0) {
      emptyState.hidden = false;
    } else {
      emptyState.hidden = true;
      pageRows.forEach(row => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${Utils.formatDateTime(row[0])}</td>
          <td>#${row[1] ?? "—"}</td>
          <td>${row[2] ?? "—"}</td>
          <td>${row[4] ?? "—"}</td>
          <td>${row[5] ?? "—"}</td>
          <td>${networkBadge(row[6])}</td>
          <td>${row[7] ?? "—"}</td>
          <td>${row[8] != null ? row[8] + " ms" : "—"}</td>
          <td>${row[9] != null ? Utils.formatDecimal(row[9], 1) + " Mbps" : "—"}</td>
          <td>${row[10] != null ? Utils.formatDecimal(row[10], 2) + "%" : "—"}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    renderPagination();
    countLabel.textContent = `${Utils.formatNumber(filteredRows.length)} رویداد از ${Utils.formatNumber(allRows.length)} نمونه`;
  }

  function renderPagination() {
    pagination.innerHTML = "";
    const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));
    currentPage = Math.min(currentPage, totalPages);

    const prev = Utils.el("button", "page-btn", '<i data-lucide="chevron-right"></i>');
    prev.disabled = currentPage === 1;
    prev.onclick = () => { currentPage--; render(); if (window.lucide) lucide.createIcons(); };
    pagination.appendChild(prev);

    const maxButtons = 5;
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);
    startPage = Math.max(1, endPage - maxButtons + 1);

    for (let p = startPage; p <= endPage; p++) {
      const btn = Utils.el("button", "page-btn" + (p === currentPage ? " active" : ""), p);
      btn.onclick = () => { currentPage = p; render(); };
      pagination.appendChild(btn);
    }

    const next = Utils.el("button", "page-btn", '<i data-lucide="chevron-left"></i>');
    next.disabled = currentPage === totalPages;
    next.onclick = () => { currentPage++; render(); if (window.lucide) lucide.createIcons(); };
    pagination.appendChild(next);

    if (window.lucide) lucide.createIcons();
  }

  function applyFilter(term) {
    if (!term) {
      filteredRows = allRows;
    } else {
      const t = term.toLowerCase();
      filteredRows = allRows.filter(row =>
        [row[2], row[4], row[5], row[6], row[7]].some(v => String(v ?? "").toLowerCase().includes(t))
      );
    }
    if (sortKey !== null) applySort(sortKey, false);
    currentPage = 1;
    render();
  }

  function applySort(key, toggle = true) {
    if (toggle) {
      sortDir = (sortKey === key) ? -sortDir : 1;
    }
    sortKey = key;
    filteredRows = [...filteredRows].sort((a, b) => {
      const va = a[key], vb = b[key];
      if (va === vb) return 0;
      if (va === null || va === undefined) return 1;
      if (vb === null || vb === undefined) return -1;
      return (va > vb ? 1 : -1) * sortDir;
    });
    render();
  }

  async function load() {
    renderSkeleton();
    try {
      const data = await Api.eventsSample(SAMPLE_SIZE);
      allRows = (data && data.events) || [];
      filteredRows = allRows;
      currentPage = 1;
      render();
    } catch (err) {
      tbody.innerHTML = "";
      emptyState.hidden = false;
      countLabel.textContent = "خطا در دریافت رویدادها";
      Utils.showToast("دریافت رویدادها ناموفق بود: " + err.message, "error");
    }
  }

  function bindEvents() {
    document.getElementById("eventSearchInput").addEventListener("input",
      Utils.debounce(e => applyFilter(e.target.value.trim()), 250)
    );

    document.getElementById("eventsRefreshBtn").addEventListener("click", () => load());

    document.querySelectorAll("#eventsTable thead th").forEach(th => {
      th.addEventListener("click", () => applySort(Number(th.dataset.key)));
    });
  }

  function init() {
    bindEvents();
    load();
  }

  return { init, reload: load };
})();

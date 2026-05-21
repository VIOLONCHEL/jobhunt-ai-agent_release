let currentPage = 0;
const pageSize = 5;

let matchedResults = [];
let allResults = [];
let currentResults = [];
let currentQuery = "";
let currentStatusFilter = "all";

function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");

  if (!container) return;

  const toast = document.createElement("div");

  toast.className = `toast ${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  setTimeout(() => toast.remove(), 3500);
}

async function matchJobs() {
  const text = document.getElementById("resumeText")?.value.trim();

  if (!text) {
    showToast("Please paste a resume first", "error");
    return;
  }

  try {
    const container = document.getElementById("matchResults");

    if (container) {
      container.innerHTML = `<div class="empty-state">Loading vacancies from Adzuna...</div>`;
    }

    const response = await matchJobsAPI(text);

    currentQuery = response.query || "";
    currentStatusFilter = "all";

    matchedResults = (response.results || [])
      .filter((job) => job && job.job_id)
      .map((job) => ({
        ...job,
        status: job.status || "none",
        experience: detectExperience(job.description || ""),
        match_percent: normalizeVisiblePercent(job.match_percent),
      }))
      .filter((job) => Number(job.match_percent) >= 1)
      .sort((a, b) => Number(b.match_percent || 0) - Number(a.match_percent || 0));

    allResults = [...matchedResults];

    applyAdvancedFilters();

    showToast(`Loaded ${allResults.length} matching vacancies`, "success");
  } catch (e) {
    console.error(e);

    const container = document.getElementById("matchResults");

    if (container) {
      container.innerHTML = `
        <div class="empty-state">Unable to load vacancies right now. Please try again later.</div>
      `;
    }

    showToast(e.message || "Failed to match jobs", "error");
  }
}

function normalizeVisiblePercent(value) {
  const number = Number(value || 0);

  if (!Number.isFinite(number)) return 1;

  return Math.max(1, Math.min(100, number));
}

function detectExperience(text) {
  const value = (text || "").toLowerCase();

  if (/(7\+|8\+|9\+|10\+|lead|principal)/.test(value)) {
    return "lead";
  }

  if (/(5\+|6\+|7\s+years|senior)/.test(value)) {
    return "senior";
  }

  if (/(2\+|3\+|4\+|5\s+years|middle|mid-level|mid level)/.test(value)) {
    return "middle";
  }

  if (/(0\+|1\+|2\s+years|junior|entry)/.test(value)) {
    return "junior";
  }

  return "";
}

async function setStatus(jobId, status) {
  try {
    const job =
      allResults.find((j) => String(j.job_id) === String(jobId)) ||
      currentResults.find((j) => String(j.job_id) === String(jobId)) ||
      matchedResults.find((j) => String(j.job_id) === String(jobId));

    if (!job) {
      showToast("Job was not found in current results", "error");
      return;
    }

    await saveJobStatus(job, status, currentQuery);

    matchedResults = matchedResults.map((j) =>
      String(j.job_id) === String(jobId) ? { ...j, status } : j,
    );

    allResults = allResults.map((j) =>
      String(j.job_id) === String(jobId) ? { ...j, status } : j,
    );

    currentResults = currentResults.map((j) =>
      String(j.job_id) === String(jobId) ? { ...j, status } : j,
    );

    if (currentStatusFilter !== "all" && status !== currentStatusFilter) {
      allResults = matchedResults.filter((job) => job.status === currentStatusFilter);
    }

    applyAdvancedFilters(false);

    showToast(
      status === "none" ? "Job status removed" : `Job moved to ${status}`,
      "success",
    );
  } catch (e) {
    console.error(e);
    showToast(e.message || "Failed to update status", "error");
  }
}

async function loadCategory(status) {
  try {
    currentStatusFilter = status;

    if (status === "all") {
      allResults = [...matchedResults];
      applyAdvancedFilters();
      return;
    }

    const savedFromBackend = await getJobsByStatus(status);

    if (Array.isArray(savedFromBackend) && savedFromBackend.length > 0) {
      allResults = savedFromBackend.map((job) => ({
        ...job,
        experience: detectExperience(job.description || ""),
        match_percent: normalizeVisiblePercent(job.match_percent),
      }));
    } else {
      allResults = matchedResults.filter((job) => job.status === status);
    }

    applyAdvancedFilters();
  } catch (e) {
    console.error(e);
    showToast(e.message || "Failed to load category", "error");
  }
}

function applyAdvancedFilters(resetPage = true) {
  let results = [...allResults];

  const workMode = document.getElementById("workModeFilter")?.value || "";
  const experience = document.getElementById("experienceFilter")?.value || "";
  const sortValue = document.getElementById("sortSelect")?.value || "score_desc";

  if (workMode) {
    results = results.filter((j) => {
      const work = `${j.work_mode || ""} ${j.contract_time || ""}`.toLowerCase();

      return work.includes(workMode.toLowerCase());
    });
  }

  if (experience) {
    results = results.filter((j) => j.experience === experience);
  }

  if (sortValue === "score_asc") {
    results.sort(
      (a, b) => Number(a.match_percent || 0) - Number(b.match_percent || 0),
    );
  } else {
    results.sort(
      (a, b) => Number(b.match_percent || 0) - Number(a.match_percent || 0),
    );
  }

  currentResults = results;

  if (resetPage) currentPage = 0;

  renderTable();
}

function resetAdvancedFilters() {
  const sortSelect = document.getElementById("sortSelect");
  const workModeFilter = document.getElementById("workModeFilter");
  const experienceFilter = document.getElementById("experienceFilter");

  if (sortSelect) sortSelect.value = "score_desc";
  if (workModeFilter) workModeFilter.value = "";
  if (experienceFilter) experienceFilter.value = "";

  applyAdvancedFilters();
}

document.addEventListener("click", () => {
  document.querySelectorAll(".menu").forEach((m) => m.classList.add("hidden"));
});

function toggleMenu(jobId, e) {
  if (e) e.stopPropagation();

  document.querySelectorAll(".menu").forEach((m) => {
    if (m.id !== `menu-${jobId}`) m.classList.add("hidden");
  });

  const menu = document.getElementById(`menu-${jobId}`);

  if (menu) menu.classList.toggle("hidden");
}

function renderEmptyState() {
  const container = document.getElementById("matchResults");

  if (!container) return;

  let message = "No results found for this resume.";

  if (currentStatusFilter === "saved") message = "No saved jobs yet.";
  if (currentStatusFilter === "applied") message = "No applied jobs yet.";
  if (currentStatusFilter === "interview") {
    message = "No interview-stage jobs yet.";
  }

  container.innerHTML = `<div class="empty-state">${message}</div>`;
}

function renderAIInsight(data) {
  const whyMatch = (data.why_match || [])
    .map((item) => `<li>${item}</li>`)
    .join("");

  const missing = (data.missing || [])
    .map((item) => `<span class="ai-chip ai-chip-missing">${item}</span>`)
    .join("");

  const improve = (data.improve || [])
    .map((item) => `<li>${item}</li>`)
    .join("");

  return `
    <div class="ai-box">
      <div class="ai-header">
        <span class="ai-badge">AI Insight</span>
      </div>

      <p class="ai-summary">
        ${data.summary || "No summary available."}
      </p>

      <div class="ai-sections">
        <div class="ai-section">
          <h4>Why match</h4>
          <ul>${whyMatch || "<li>No explanation provided.</li>"}</ul>
        </div>

        <div class="ai-section">
          <h4>Missing</h4>
          <div class="ai-chip-wrap">
            ${missing || '<span class="ai-chip">Nothing major detected</span>'}
          </div>
        </div>

        <div class="ai-section">
          <h4>Improve</h4>
          <ul>${improve || "<li>No suggestions provided.</li>"}</ul>
        </div>
      </div>
    </div>
  `;
}

async function handleAIInsight(button, jobId) {
  const row = button.closest("tr");
  const resultBox = row?.querySelector(".ai-result");
  const resumeText = document.getElementById("resumeText")?.value.trim() || "";
  const jobDescription =
    row?.querySelector(".job-description")?.innerText?.trim() || "";

  if (!resultBox) return;

  if (!resumeText) {
    resultBox.classList.remove("hidden");
    resultBox.innerHTML = `<div class="message error">Paste your resume first.</div>`;
    return;
  }

  if (!jobDescription) {
    resultBox.classList.remove("hidden");
    resultBox.innerHTML = `<div class="message error">Job description is missing.</div>`;
    return;
  }

  resultBox.classList.remove("hidden");
  resultBox.innerHTML = `<div class="message success">Generating AI insight...</div>`;

  try {
    const data = await getAIInsight(resumeText, jobDescription);

    resultBox.innerHTML = renderAIInsight(data);
  } catch (e) {
    console.error(e);

    resultBox.innerHTML = `<div class="message error">${
      e.message || "Failed to generate AI insight"
    }</div>`;
  }
}

function renderTable() {
  const container = document.getElementById("matchResults");

  if (!container) return;

  container.innerHTML = "";

  if (!currentResults.length) {
    renderEmptyState();
    return;
  }

  const total = currentResults.length;
  const start = currentPage * pageSize;
  const end = start + pageSize;
  const pageItems = currentResults.slice(start, end);

  let html = `
    <p><strong>Total matches:</strong> ${total}</p>

    <table class="jobs-table">
      <thead>
        <tr>
          <th style="width:18%">Title</th>
          <th style="width:10%">Match %</th>
          <th style="width:12%">Status</th>
          <th style="width:60%">Description</th>
        </tr>
      </thead>

      <tbody>
  `;

  pageItems.forEach((job, index) => {
    const globalIndex = start + index;
    const percent = normalizeVisiblePercent(job.match_percent);

    html += `
      <tr>
        <td>
          <strong>${job.title || "Untitled"}</strong>
          ${
            job.company_name
              ? `<div class="small-help">${job.company_name}</div>`
              : ""
          }
        </td>

        <td>
          <strong>${percent.toFixed(1)}%</strong>
        </td>

        <td>
          <div class="status-select" onclick="toggleMenu('${job.job_id}', event)">
            ${job.status || "none"}
          </div>

          <div id="menu-${job.job_id}" class="menu hidden">
            <div onclick="setStatus('${job.job_id}', 'saved')">Saved</div>
            <div onclick="setStatus('${job.job_id}', 'applied')">Applied</div>
            <div onclick="setStatus('${job.job_id}', 'interview')">Interview</div>
            <div onclick="setStatus('${job.job_id}', 'none')">None</div>
          </div>
        </td>

        <td>
          <div class="job-meta">
            ${
              job.work_mode
                ? `<span class="meta-badge">${job.work_mode}</span>`
                : ""
            }
            ${
              job.contract_time
                ? `<span class="meta-badge">${job.contract_time}</span>`
                : ""
            }
            ${
              job.location_text
                ? `<span class="meta-badge">${job.location_text}</span>`
                : ""
            }
            ${
              job.experience
                ? `<span class="meta-badge">${job.experience}</span>`
                : ""
            }
          </div>

          <div class="job-description" id="desc-${globalIndex}">
            ${job.description || "—"}
          </div>

          <div class="job-actions">
            <button
              type="button"
              class="action-btn action-read"
              id="read-${globalIndex}"
              onclick="toggleDescription(${globalIndex})"
            >
              Read more
            </button>

            ${
              job.source_url
                ? `
                  <a
                    class="action-btn action-apply"
                    href="${job.source_url}"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Apply
                  </a>
                `
                : `
                  <button
                    type="button"
                    class="action-btn action-apply"
                    disabled
                  >
                    Apply
                  </button>
                `
            }

            <button
              type="button"
              class="action-btn action-ai"
              onclick="handleAIInsight(this, '${job.job_id}')"
            >
              AI Insight
            </button>
          </div>

          <div class="ai-result hidden"></div>
        </td>
      </tr>
    `;
  });

  html += `
      </tbody>
    </table>

    <div class="pagination">
      <button onclick="prevPage()" ${currentPage === 0 ? "disabled" : ""}>◀</button>
      <span>Page ${currentPage + 1} of ${Math.ceil(total / pageSize)}</span>
      <button onclick="nextPage()" ${end >= total ? "disabled" : ""}>▶</button>
    </div>
  `;

  container.innerHTML = html;
}

function nextPage() {
  if ((currentPage + 1) * pageSize < currentResults.length) {
    currentPage++;
    renderTable();
  }
}

function prevPage() {
  if (currentPage > 0) {
    currentPage--;
    renderTable();
  }
}

function toggleDescription(index) {
  const el = document.getElementById(`desc-${index}`);
  const readMore = document.getElementById(`read-${index}`);

  if (!el || !readMore) return;

  el.classList.toggle("expanded");

  readMore.textContent = el.classList.contains("expanded")
    ? "Show less"
    : "Read more";
}

window.toggleMenu = toggleMenu;
window.setStatus = setStatus;
window.toggleDescription = toggleDescription;
window.matchJobs = matchJobs;
window.loadCategory = loadCategory;
window.applyAdvancedFilters = applyAdvancedFilters;
window.resetAdvancedFilters = resetAdvancedFilters;
window.nextPage = nextPage;
window.prevPage = prevPage;
window.handleAIInsight = handleAIInsight;
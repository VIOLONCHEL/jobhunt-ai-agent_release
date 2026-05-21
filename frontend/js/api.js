const API_URL = "http://127.0.0.1:8000";

function getToken() {
  return localStorage.getItem("token");
}

function setToken(token) {
  localStorage.setItem("token", token);
}

function clearToken() {
  localStorage.removeItem("token");
}

function normalizeDetail(detail) {
  if (!detail) return "Request failed";

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;

        if (item && typeof item === "object") {
          const where = Array.isArray(item.loc)
            ? item.loc.join(" → ")
            : "field";

          const msg = item.msg || JSON.stringify(item);

          return `${where}: ${msg}`;
        }

        return String(item);
      })
      .join("; ");
  }

  if (typeof detail === "object") {
    return JSON.stringify(detail);
  }

  return String(detail);
}

async function request(path, method = "GET", body = null) {
  const headers = {
    "Content-Type": "application/json",
  };

  const token = getToken();

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const options = {
    method,
    headers,
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  let res;

  try {
    res = await fetch(API_URL + path, options);
  } catch {
    throw new Error(
      "Cannot connect to backend. Make sure FastAPI is running on http://127.0.0.1:8000",
    );
  }

  if (!res.ok) {
    let message = "Request failed";

    try {
      const data = await res.json();
      message = normalizeDetail(data.detail || data);
    } catch {
      message = await res.text();
    }

    throw new Error(message);
  }

  return res.json();
}

async function registerUser(nickname, email, password) {
  return request("/auth/register", "POST", {
    nickname,
    email,
    password,
  });
}

async function loginUser(email, password) {
  return request("/auth/login", "POST", {
    email,
    password,
  });
}

async function getMe() {
  return request("/auth/me", "GET");
}

async function updateProfile(nickname, email) {
  return request("/auth/profile", "PUT", {
    nickname,
    email,
  });
}

async function changePassword(currentPassword, newPassword, confirmNewPassword) {
  return request("/auth/change-password", "POST", {
    current_password: currentPassword,
    new_password: newPassword,
    confirm_new_password: confirmNewPassword,
  });
}

async function deleteProfile(password) {
  return request("/auth/me", "DELETE", {
    password,
  });
}

async function matchJobsAPI(resumeText) {
  return request("/jobs/match", "POST", {
    resume_text: resumeText,
    sort_by: "relevance",
    results_per_page: 50,
  });
}

async function saveJobStatus(job, status, currentQuery = "") {
  return request("/jobs/status", "POST", {
    job_id: String(job.job_id || ""),
    title: job.title || "Untitled vacancy",
    description: job.description || "",
    source_url: job.source_url || "",
    location_text: job.location_text || "",
    country: job.country || "",
    work_mode: job.work_mode || job.contract_time || "",
    score: Number(job.score || 0),
    match_percent: Number(job.match_percent || 0),
    query: currentQuery || "",
    status,
  });
}

async function getJobsByStatus(status) {
  return request(`/jobs/by-status?status=${encodeURIComponent(status)}`, "GET");
}

async function getAdminStats() {
  return request("/admin/stats", "GET");
}

async function getAdminUsers() {
  return request("/admin/users", "GET");
}

async function updateUserRole(userId, role) {
  return request(`/admin/users/${userId}/role`, "PUT", {
    role,
  });
}

async function deleteUser(userId) {
  return request(`/admin/users/${userId}`, "DELETE");
}

async function getAIInsight(resumeText, jobDescription) {
  return request("/ai/insight", "POST", {
    resume_text: resumeText,
    job_description: jobDescription,
  });
}

function logoutUser() {
  clearToken();
}
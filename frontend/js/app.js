let authMode = "login";

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function passwordChecks(password) {
  return {
    length: password.length >= 8,
    latin: /^[A-Za-z\d\W_]+$/.test(password),
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    digit: /\d/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  };
}

function showMessage(targetId, text, type = "success") {
  const box = document.getElementById(targetId);

  if (!box) return;

  box.innerHTML = `<div class="message ${type}">${text}</div>`;
}

function clearMessage(targetId) {
  const box = document.getElementById(targetId);

  if (!box) return;

  box.innerHTML = "";
}

function renderEmailValidation(value) {
  const box = document.getElementById("emailRules");

  if (!box) return;

  if (!value) {
    box.innerHTML = "";
    return;
  }

  box.innerHTML = `
    <div class="validation-row ${isValidEmail(value) ? "ok" : "bad"}">
      ${isValidEmail(value) ? "✔" : "✖"} Valid email format
    </div>
  `;
}

function renderPasswordValidation(value) {
  const box = document.getElementById("passwordRules");

  if (!box) return;

  if (!value || authMode !== "register") {
    box.innerHTML = "";
    return;
  }

  const c = passwordChecks(value);

  box.innerHTML = `
    <div class="validation-row ${c.length ? "ok" : "bad"}">${c.length ? "✔" : "✖"} At least 8 characters</div>
    <div class="validation-row ${c.latin ? "ok" : "bad"}">${c.latin ? "✔" : "✖"} Latin letters only</div>
    <div class="validation-row ${c.upper ? "ok" : "bad"}">${c.upper ? "✔" : "✖"} At least one uppercase letter</div>
    <div class="validation-row ${c.lower ? "ok" : "bad"}">${c.lower ? "✔" : "✖"} At least one lowercase letter</div>
    <div class="validation-row ${c.digit ? "ok" : "bad"}">${c.digit ? "✔" : "✖"} At least one digit</div>
    <div class="validation-row ${c.special ? "ok" : "bad"}">${c.special ? "✔" : "✖"} At least one special character</div>
  `;
}

function renderProfilePasswordRules() {
  const value = document.getElementById("newPassword")?.value || "";
  const box = document.getElementById("profilePasswordRules");

  if (!box) return;

  if (!value) {
    box.innerHTML = "";
    return;
  }

  const c = passwordChecks(value);

  box.innerHTML = `
    <div class="validation-row ${c.length ? "ok" : "bad"}">${c.length ? "✔" : "✖"} At least 8 characters</div>
    <div class="validation-row ${c.latin ? "ok" : "bad"}">${c.latin ? "✔" : "✖"} Latin letters only</div>
    <div class="validation-row ${c.upper ? "ok" : "bad"}">${c.upper ? "✔" : "✖"} At least one uppercase letter</div>
    <div class="validation-row ${c.lower ? "ok" : "bad"}">${c.lower ? "✔" : "✖"} At least one lowercase letter</div>
    <div class="validation-row ${c.digit ? "ok" : "bad"}">${c.digit ? "✔" : "✖"} At least one digit</div>
    <div class="validation-row ${c.special ? "ok" : "bad"}">${c.special ? "✔" : "✖"} At least one special character</div>
  `;
}

function togglePasswordVisibility(inputId, btnEl) {
  const input = document.getElementById(inputId);

  if (!input) return;

  if (input.type === "password") {
    input.type = "text";
    btnEl.innerText = "Hide";
  } else {
    input.type = "password";
    btnEl.innerText = "Show";
  }
}

function updateAuthView() {
  const authTitle = document.getElementById("authTitle");
  const authSubmitBtn = document.getElementById("authSubmitBtn");
  const authNicknameWrap = document.getElementById("authNicknameWrap");

  clearMessage("authMessage");

  document
    .getElementById("loginTab")
    .classList.toggle("active", authMode === "login");

  document
    .getElementById("registerTab")
    .classList.toggle("active", authMode === "register");

  authNicknameWrap.style.display = authMode === "register" ? "block" : "none";

  if (authMode === "login") {
    authTitle.innerText = "Login";
    authSubmitBtn.innerText = "Login";
  }

  if (authMode === "register") {
    authTitle.innerText = "Create account";
    authSubmitBtn.innerText = "Register";
  }

  renderEmailValidation(document.getElementById("authEmail").value.trim());
  renderPasswordValidation(document.getElementById("authPassword").value);
}

function setAuthMode(mode) {
  authMode = mode;
  updateAuthView();
}

async function bootstrapApp() {
  const token = localStorage.getItem("token");

  if (!token) {
    showAuth();
    return;
  }

  try {
    const me = await getMe();
    showApp(me);
  } catch (e) {
    console.error(e);
    logoutUser();
    showAuth();
  }
}

function showAuth() {
  document.getElementById("auth-view").style.display = "grid";
  document.getElementById("app-view").style.display = "none";
  document.getElementById("logoutBtn").style.display = "none";
  document.getElementById("currentUserGreeting").innerText = "";
  document.getElementById("currentUserRole").innerText = "";
  updateAuthView();
}

function showApp(user) {
  document.getElementById("auth-view").style.display = "none";
  document.getElementById("app-view").style.display = "block";

  document.getElementById("currentUserGreeting").innerText =
    `Hello, ${user.nickname}`;

  document.getElementById("currentUserRole").innerText = user.role;
  document.getElementById("logoutBtn").style.display = "inline-block";

  document.getElementById("profileNickname").value = user.nickname || "";
  document.getElementById("profileEmail").value = user.email || "";

  const adminPanel = document.getElementById("admin-view");
  const adminNavBtn = document.getElementById("adminNavBtn");

  const isAdmin = user.role === "admin";

  adminPanel.style.display = "none";
  adminNavBtn.style.display = isAdmin ? "inline-block" : "none";

  if (isAdmin) {
    loadAdminPanel();
  }

  setAppView("dashboard");
}

function setAppView(view, event = null) {
  if (event) {
    document
      .querySelectorAll(".nav-tab")
      .forEach((btn) => btn.classList.remove("active"));

    event.target.classList.add("active");
  } else {
    document.querySelectorAll(".nav-tab").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.view === view);
    });
  }

  document.getElementById("dashboard-view").style.display =
    view === "dashboard" ? "block" : "none";

  document.getElementById("profile-view").style.display =
    view === "profile" ? "block" : "none";

  document.getElementById("admin-view").style.display =
    view === "admin" ? "block" : "none";
}

async function handleAuthSubmit() {
  const nickname = document.getElementById("authNickname").value.trim();
  const email = document.getElementById("authEmail").value.trim();
  const password = document.getElementById("authPassword").value.trim();

  try {
    if (authMode === "register") {
      if (!nickname) throw new Error("Nickname is required");
      if (!email) throw new Error("Email is required");
      if (!password) throw new Error("Password is required");

      const data = await registerUser(nickname, email, password);

      setToken(data.access_token);
      showApp(data.user);
      return;
    }

    if (authMode === "login") {
      if (!email) throw new Error("Email is required");
      if (!password) throw new Error("Password is required");

      const data = await loginUser(email, password);

      setToken(data.access_token);
      showApp(data.user);
      return;
    }
  } catch (e) {
    console.error(e);
    showMessage("authMessage", e.message || "Request failed", "error");
  }
}

async function saveProfileChanges() {
  const nickname = document.getElementById("profileNickname").value.trim();
  const email = document.getElementById("profileEmail").value.trim();

  try {
    const user = await updateProfile(nickname, email);

    document.getElementById("currentUserGreeting").innerText =
      `Hello, ${user.nickname}`;

    showMessage("profileMessage", "Profile updated successfully", "success");
  } catch (e) {
    console.error(e);
    showMessage(
      "profileMessage",
      e.message || "Failed to update profile",
      "error",
    );
  }
}

async function handleChangePassword() {
  const currentPassword = document
    .getElementById("currentPassword")
    .value.trim();

  const newPassword = document.getElementById("newPassword").value.trim();

  const confirmNewPassword = document
    .getElementById("confirmNewPassword")
    .value.trim();

  try {
    const data = await changePassword(
      currentPassword,
      newPassword,
      confirmNewPassword,
    );

    showMessage(
      "profileMessage",
      data.message || "Password changed successfully",
      "success",
    );

    document.getElementById("currentPassword").value = "";
    document.getElementById("newPassword").value = "";
    document.getElementById("confirmNewPassword").value = "";
    document.getElementById("profilePasswordRules").innerHTML = "";
  } catch (e) {
    console.error(e);
    showMessage(
      "profileMessage",
      e.message || "Failed to change password",
      "error",
    );
  }
}

async function handleDeleteProfile() {
  const password = prompt(
    "Enter your password to permanently delete your profile:",
  );

  if (!password) return;

  try {
    const data = await deleteProfile(password);

    logoutUser();

    alert(data.message || "Profile deleted");
    location.reload();
  } catch (e) {
    console.error(e);

    showMessage(
      "profileMessage",
      e.message || "Failed to delete profile",
      "error",
    );
  }
}

function handleLogout() {
  logoutUser();
  location.reload();
}

async function loadAdminPanel() {
  await loadAdminStats();
  await loadAdminUsers();
}

async function loadAdminStats() {
  try {
    const stats = await getAdminStats();

    document.getElementById("adminStats").innerHTML = `
      <p><strong>Total users:</strong> ${stats.total_users}</p>
      <p><strong>Admins:</strong> ${stats.total_admins}</p>
      <p><strong>Regular users:</strong> ${stats.total_regular_users}</p>
      <p><strong>Saved:</strong> ${stats.total_saved}</p>
      <p><strong>Applied:</strong> ${stats.total_applied}</p>
      <p><strong>Interview:</strong> ${stats.total_interview}</p>
    `;
  } catch (e) {
    console.error(e);

    document.getElementById("adminStats").innerHTML =
      `<p>Failed to load statistics</p>`;
  }
}

async function loadAdminUsers() {
  try {
    const users = await getAdminUsers();

    const html = users
      .map(
        (u) => `
      <tr>
        <td>${u.id}</td>
        <td>${u.nickname}</td>
        <td>${u.email}</td>
        <td>
          <select onchange="changeUserRole(${u.id}, this.value)">
            <option value="user" ${u.role === "user" ? "selected" : ""}>user</option>
            <option value="admin" ${u.role === "admin" ? "selected" : ""}>admin</option>
          </select>
        </td>
        <td>${u.saved_jobs_count}</td>
        <td><button onclick="removeUser(${u.id})">Delete</button></td>
      </tr>
    `,
      )
      .join("");

    document.getElementById("adminUsersTable").innerHTML = `
      <table class="jobs-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Nickname</th>
            <th>Email</th>
            <th>Role</th>
            <th>Saved Jobs</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>${html}</tbody>
      </table>
    `;
  } catch (e) {
    console.error(e);

    document.getElementById("adminUsersTable").innerHTML =
      `<p>Failed to load users</p>`;
  }
}

async function changeUserRole(userId, role) {
  try {
    await updateUserRole(userId, role);
    await loadAdminPanel();
  } catch (e) {
    console.error(e);
    alert(e.message || "Failed to update role");
  }
}

async function removeUser(userId) {
  if (!confirm("Delete this user?")) return;

  try {
    await deleteUser(userId);
    await loadAdminPanel();
  } catch (e) {
    console.error(e);
    alert(e.message || "Failed to delete user");
  }
}

window.setAuthMode = setAuthMode;
window.togglePasswordVisibility = togglePasswordVisibility;
window.handleAuthSubmit = handleAuthSubmit;
window.saveProfileChanges = saveProfileChanges;
window.handleChangePassword = handleChangePassword;
window.handleDeleteProfile = handleDeleteProfile;
window.handleLogout = handleLogout;
window.changeUserRole = changeUserRole;
window.removeUser = removeUser;
window.setAppView = setAppView;
window.renderProfilePasswordRules = renderProfilePasswordRules;

document.addEventListener("DOMContentLoaded", () => {
  const authEmail = document.getElementById("authEmail");
  const authPassword = document.getElementById("authPassword");

  if (authEmail) {
    authEmail.addEventListener("input", (e) =>
      renderEmailValidation(e.target.value.trim()),
    );
  }

  if (authPassword) {
    authPassword.addEventListener("input", (e) =>
      renderPasswordValidation(e.target.value),
    );
  }

  bootstrapApp();
});
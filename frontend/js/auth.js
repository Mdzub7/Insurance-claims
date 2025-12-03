const API_BASE = "http://k8s-training-capstone-e0f294e241-9c8360a7cd58c010.elb.eu-west-2.amazonaws.com/api/v1";

function setAuth(token, role, patientId, remember) {
  const storage = remember ? localStorage : sessionStorage;
  storage.setItem("token", token);
  storage.setItem("role", role);
  if (patientId) storage.setItem("patient_id", patientId);
}

function getAuthToken() {
  return sessionStorage.getItem("token") || localStorage.getItem("token");
}

function clearAuth() {
  sessionStorage.clear();
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("patient_id");
}

async function login({ email, patient_id, password }) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, patient_id, password })
  });
  if (!res.ok) {
    try {
      const body = await res.json();
      throw new Error(body.detail || "Login failed");
    } catch {
      throw new Error("Login failed");
    }
  }
  return res.json();
}

async function register(payload) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("Registration failed");
  return res.json();
}

const loginForm = document.getElementById("loginForm");
const registerLink = document.getElementById("registerLink");

if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("loginMessage");
    msg.textContent = "Authenticating...";
    msg.style.color = "#0070cd";
    const method = document.getElementById("loginMethod").value;
    const email = document.getElementById("email").value.trim();
    const patient_id = document.getElementById("patientId").value.trim();
    const password = document.getElementById("password").value;
    const remember = document.getElementById("remember").checked;
    try {
      const data = await login({ email: method === 'email' ? email : null, patient_id: method === 'patient' ? patient_id : null, password });
      setAuth(data.token, data.role, data.patient_id || data.user_id, remember);
      msg.textContent = "Login successful";
      msg.style.color = "green";
      const params = new URLSearchParams(window.location.search);
      const next = params.get('next');
      const target = next || (data.role === "admin" ? "admin/dashboard.html" : "patient/dashboard.html");
      window.location.href = target;
    } catch (err) {
      msg.textContent = "Error: " + err.message;
      msg.style.color = "red";
    }
  });
}

if (registerLink) {
  registerLink.addEventListener("click", async (e) => {
    e.preventDefault();
    const email = prompt("Enter email");
    const password = prompt("Enter a strong password (min 8 chars)");
    const role = prompt("Enter role: patient or admin", "patient");
    const name = prompt("Enter full name");
    if (!email || !password || !role) return;
    const msg = document.getElementById("loginMessage");
    try {
      const data = await register({ email, password, role, name });
      msg.textContent = `Registered. Your patient_id: ${data.patient_id || "n/a"}`;
      msg.style.color = "green";
    } catch (err) {
      msg.textContent = "Registration failed";
      msg.style.color = "red";
    }
  });
}

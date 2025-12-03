const API_BASE = "http://k8s-training-capstone-e0f294e241-9c8360a7cd58c010.elb.eu-west-2.amazonaws.com/api/v1";

function passwordStrength(p) {
  let score = 0;
  if (p.length >= 8) score++;
  if (/[A-Z]/.test(p)) score++;
  if (/[a-z]/.test(p)) score++;
  if (/\d/.test(p)) score++;
  if (/[^A-Za-z0-9]/.test(p)) score++;
  return score;
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

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("registerForm");
  const msg = document.getElementById("registerMessage");
  const pwd = document.getElementById("password");
  const strength = document.getElementById("strength");

  pwd.addEventListener("input", () => {
    const s = passwordStrength(pwd.value);
    const labels = ["Weak", "Fair", "Good", "Strong", "Very Strong"];
    strength.textContent = `Strength: ${labels[Math.max(0, s-1)]}`;
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.textContent = "Registering...";
    msg.style.color = "#0070cd";
    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = pwd.value;
    if (passwordStrength(password) < 3) {
      msg.textContent = "Password too weak";
      msg.style.color = "red";
      return;
    }
    try {
      const data = await register({ name, email, password, role: "patient" });
      msg.textContent = `Registered. Your patient_id: ${data.patient_id}`;
      msg.style.color = "green";
    } catch (err) {
      msg.textContent = "Error: " + err.message;
      msg.style.color = "red";
    }
  });
});

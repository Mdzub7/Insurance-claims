async function populateSidebar() {
  try {
    const res = await fetch("http://localhost:8001/api/v1/users/me", { headers: authHeader() })
    if (!res.ok) return
    const u = await res.json()
    const nameEl = document.getElementById('sbName')
    const idEl = document.getElementById('sbId')
    if (nameEl) nameEl.textContent = u.name || (u.email || 'Member')
    if (idEl) idEl.textContent = u.patient_id ? `Patient ID: ${u.patient_id}` : ''
  } catch {}
  const links = document.querySelectorAll('.sidebar-link')
  links.forEach(l => { if (l.getAttribute('href') && location.pathname.endsWith(l.getAttribute('href'))) l.classList.add('active') })
}

function authHeader() {
  const token = sessionStorage.getItem("token") || localStorage.getItem("token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

document.addEventListener('DOMContentLoaded', populateSidebar)

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.querySelector('.sidebar-toggle')
  const sidebar = document.querySelector('.sidebar')
  const shell = document.querySelector('.patient-shell')
  if (btn && sidebar) {
    btn.addEventListener('click', ()=>{
      sidebar.classList.toggle('collapsed')
      if (shell) shell.classList.toggle('collapsed')
    })
  }
})

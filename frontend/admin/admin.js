const API_BASE = "http://localhost:8001/api/v1";

function authHeader() {
  const token = sessionStorage.getItem("token") || localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchUsers() {
  const res = await fetch(`${API_BASE}/admin/users`, { headers: authHeader() });
  if (!res.ok) throw new Error("Failed to load users");
  return res.json();
}

async function fetchPendingClaims() {
  const res = await fetch(`${API_BASE}/admin/claims/pending`, { headers: authHeader() });
  if (!res.ok) return [];
  return res.json();
}

async function fetchAllClaims() {
  const res = await fetch(`${API_BASE}/admin/claims`, { headers: authHeader() });
  if (!res.ok) return [];
  return res.json();
}

async function approveClaim(id) {
  const res = await fetch(`${API_BASE}/admin/claims/${id}/approve`, { method: "POST", headers: authHeader() });
  if (!res.ok) throw new Error("Approve failed");
  return res.json();
}

async function rejectClaim(id) {
  const res = await fetch(`${API_BASE}/admin/claims/${id}/reject`, { method: "POST", headers: authHeader() });
  if (!res.ok) throw new Error("Reject failed");
  return res.json();
}

document.addEventListener("DOMContentLoaded", async () => {
  const usersDiv = document.getElementById("usersDiv");
  const claimsDiv = document.getElementById("claimsDiv");
  const adminStats = document.getElementById("adminStats");
  const adminMonthly = document.getElementById("adminMonthly");
  const adminStatus = document.getElementById("adminStatus");
  const adminProfile = document.getElementById("adminProfile");
  if (usersDiv) {
    try {
      const users = await fetchUsers();
      function renderUsers(query=''){
        const q = query.toLowerCase();
        let html = "<table style='width:100%'><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Patient ID</th><th>Action</th></tr></thead><tbody>";
        users.filter(u => (u.name||'').toLowerCase().includes(q) || (u.email||'').toLowerCase().includes(q)).forEach(u => {
          html += `<tr><td>${u.name || ''}</td><td>${u.email || ''}</td><td>${u.role}</td><td>${u.patient_id || ''}</td><td><button class='delete-user' data-id='${u.user_id}'>Delete</button></td></tr>`;
        });
        html += "</tbody></table>";
        usersDiv.innerHTML = html;
      }
      renderUsers('');
      const search = document.getElementById('userSearch');
      if (search) search.addEventListener('input', e=> renderUsers(e.target.value));
    } catch (e) {
      usersDiv.textContent = "Failed to load users";
    }
  }
  if (claimsDiv) {
    let claims = [];
    try { claims = await fetchPendingClaims(); } catch {}
    function renderClaims(query=''){
      const q = query.toLowerCase();
      const filtered = claims.filter(c=> (c.description||'').toLowerCase().includes(q) || (c.claim_id||'').toLowerCase().includes(q));
      let html = "<table style='width:100%'><thead><tr><th>ID</th><th>Description</th><th>Amount</th><th>Status</th><th>Document</th><th style='min-width:160px;'>Action</th></tr></thead><tbody>";
      if (!filtered.length) { html += "<tr><td colspan='6'>No pending claims</td></tr>"; }
      filtered.forEach(c => {
        html += `<tr><td>${c.claim_id}</td><td>${c.description||''}</td><td>₹${Number(c.amount||0).toFixed(2)}</td><td>${c.claim_status||''}</td><td>${c.s3_upload_url?`<a href='${c.s3_upload_url}' target='_blank'>View</a>`:'-'}</td>
          <td>
            <button data-id='${c.claim_id}' class='btn-approve approve'>Approve</button>
            <button data-id='${c.claim_id}' class='btn-reject reject'>Reject</button>
          </td></tr>`;
      });
      html += "</tbody></table>";
      claimsDiv.innerHTML = html;
    }
    renderClaims('');
    const csearch = document.getElementById('claimsSearch');
    if (csearch) csearch.addEventListener('input', e=> renderClaims(e.target.value));
    claimsDiv.addEventListener("click", async (e) => {
      const t = e.target;
      if (t.classList.contains("delete-user")) {
        const id = t.dataset.id;
        await fetch(`${API_BASE}/admin/users/${id}`, { method: 'DELETE', headers: authHeader() });
        t.closest('tr').remove();
      }
      if (t.classList.contains("approve")) {
        await approveClaim(t.dataset.id);
        t.closest("tr").querySelector("td:nth-child(4)").textContent = "APPROVED";
      }
      if (t.classList.contains("reject")) {
        await rejectClaim(t.dataset.id);
        t.closest("tr").querySelector("td:nth-child(4)").textContent = "REJECTED";
      }
    });
  }

  // Admin profile details
  if (adminProfile) {
    try {
      const meRes = await fetch(`${API_BASE}/users/me`, { headers: authHeader() });
      if (!meRes.ok) throw new Error('Failed');
      const me = await meRes.json();
      adminProfile.innerHTML = `
        <p><strong>Name:</strong> ${me.name||''}</p>
        <p><strong>Email:</strong> ${me.email||''}</p>
        <p><strong>Role:</strong> ${me.role||''}</p>`;
    } catch { adminProfile.textContent = 'Failed to load profile'; }
  }

  // Admin stats & charts based on all claims with polling for real-time updates
  async function refreshAdmin() {
    try {
      const allClaims = await fetchAllClaims();
      const pending = allClaims.filter(c=> (c.claim_status||'') === 'PENDING').length;
      const approved = allClaims.filter(c=> (c.claim_status||'') === 'APPROVED').length;
      const rejected = allClaims.filter(c=> (c.claim_status||'') === 'REJECTED').length;
      const totalAmt = allClaims.reduce((s,c)=> s + Number(c.amount||0), 0);
      if (adminStats) {
        adminStats.innerHTML = `
          <div class='stat-card'><div class='stat-title'>Total Claims</div><div class='stat-value'>${allClaims.length}</div></div>
          <div class='stat-card'><div class='stat-title'>Total Amount</div><div class='stat-value'>₹${totalAmt.toFixed(2)}</div></div>
          <div class='stat-card'><div class='stat-title'>Total Users</div><div class='stat-value'>${(await fetchUsers()).length}</div></div>`;
      }
      if (adminMonthly && window.Chart) {
        const byMonth = Array(12).fill(0); const amtByMonth = Array(12).fill(0);
        allClaims.forEach(c=>{ const d=new Date(c.created_at); if (!isNaN(d)) { byMonth[d.getMonth()]++; amtByMonth[d.getMonth()]+=Number(c.amount||0); } });
        new Chart(adminMonthly, { type:'bar', data:{ labels:['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'], datasets:[{ label:'Claims', data:byMonth, backgroundColor:'#0926fe', borderRadius:6 }, { label:'Amount (₹)', data:amtByMonth, type:'line', borderColor:'#27ae60', yAxisID:'y1' }] }, options:{ responsive:true, scales:{ y:{ beginAtZero:true }, y1:{ beginAtZero:true, position:'right' } } } });
      }
      if (adminStatus && window.Chart) {
        new Chart(adminStatus, { type:'doughnut', data:{ labels:['Pending','Approved','Rejected'], datasets:[{ data:[pending, approved, rejected], backgroundColor:['#f1c40f','#27ae60','#e74c3c'] }] } });
      }
    } catch {}
  }
  if (adminStats || adminMonthly || adminStatus) {
    await refreshAdmin();
    setInterval(refreshAdmin, 5000);
  }
});

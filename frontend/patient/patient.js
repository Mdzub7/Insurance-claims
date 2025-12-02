const API_BASE = "http://localhost:8001/api/v1";

function authHeader() {
  const token = sessionStorage.getItem("token") || localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchProfile() {
  const res = await fetch(`${API_BASE}/users/me`, { headers: authHeader() });
  if (!res.ok) throw new Error("Failed to load profile");
  return res.json();
}

async function fetchMyClaims() {
  const res = await fetch(`${API_BASE}/claims/my`, { headers: authHeader() });
  if (!res.ok) throw new Error("Failed to load claims");
  return res.json();
}

async function submitClaim(data, file) {
  const res = await fetch(`${API_BASE}/claims/`, {
    method: "POST",
    headers: { ...authHeader(), "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error("Failed to create claim");
  const result = await res.json();
  if (file) {
    const fd = new FormData();
    fd.append("file", file, file.name);
    const up = await fetch(`${API_BASE}/claims/${encodeURIComponent(result.claim_id)}/document`, {
      method: "POST",
      headers: { ...authHeader() },
      body: fd
    });
    if (!up.ok) throw new Error("Upload failed");
  }
  return result;
}

window.addEventListener("DOMContentLoaded", async () => {
  const profileCard = document.getElementById("profileCard");
  const claimsList = document.getElementById("claimsList");
  const submitForm = document.getElementById("submitForm");
  const uploadMsg = document.getElementById("uploadMsg");
  const stats = document.getElementById("stats");
  const statsGrid = document.getElementById("statsGrid");
  const yearSelect = document.getElementById("yearSelect");
  const chartMonthly = document.getElementById("chartMonthly");
  const chartStatus = document.getElementById("chartStatus");
  const recentTable = document.getElementById("recentTable");
  const profileStats = document.getElementById("profileStats");
  const statusFilter = document.getElementById("statusFilter");
  const yearFilter = document.getElementById("yearFilter");
  const lifecycleList = document.getElementById('lifecycleList');

  if (profileCard) {
    try {
      const p = await fetchProfile();
      profileCard.innerHTML = `
        <p><strong>Name:</strong> ${p.name || ""}</p>
        <p><strong>Email:</strong> ${p.email || ""}</p>
        <p><strong>Patient ID:</strong> ${p.patient_id || ""}</p>
        <p><strong>Role:</strong> ${p.role}</p>
      `;
    } catch (e) {
      profileCard.textContent = "Failed to load profile";
    }
  }

  if (claimsList) {
    try {
      const claims = await fetchMyClaims();
      if (!claims.length) {
        claimsList.innerHTML = "<p>No claims found.</p>";
      } else {
        let html = "<ul style='list-style:none; padding:0;'>";
        claims.forEach(c => {
          const doc = c.document_url ? ` • <a href='${c.document_url}' target='_blank' rel='noopener'>View Document</a>` : "";
          html += `<li style='padding:10px 0; border-bottom:1px solid #eee;'>
            <strong>${c.description}</strong> - ₹${Number(c.amount).toFixed(2)}
            <span class='badge badge-${c.claim_status}'>${c.claim_status}</span>${doc}
          </li>`;
        });
        html += "</ul>";
        claimsList.innerHTML = html;
      }
    } catch (e) {
      claimsList.textContent = "Failed to load claims";
    }
  }

  if (stats) {
    try {
      const claims = await fetchMyClaims();
      const total = claims.length;
      const pending = claims.filter(c => c.claim_status === 'PENDING').length;
      const approved = claims.filter(c => c.claim_status === 'APPROVED').length;
      const rejected = claims.filter(c => c.claim_status === 'REJECTED').length;
      stats.innerHTML = `<p><strong>Total:</strong> ${total} | <span class='badge badge-PENDING'>Pending ${pending}</span> <span class='badge badge-APPROVED'>Approved ${approved}</span> <span class='badge badge-REJECTED'>Rejected ${rejected}</span></p>`;
    } catch (e) {
      stats.textContent = 'Failed to load stats';
    }
  }

  if (submitForm) {
    submitForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      uploadMsg.textContent = "Submitting...";
      uploadMsg.style.color = "#0070cd";
      const amount = parseFloat(document.getElementById("amount").value);
      const description = document.getElementById("description").value;
      const policy_number = document.getElementById("policyNumber").value;
      const fileEl = document.getElementById("file");
      const file = fileEl.files[0];
      try {
        const r = await submitClaim({ amount, description, policy_number }, file);
        uploadMsg.textContent = `Success. Claim ID: ${r.claim_id}`;
        uploadMsg.style.color = "green";
      } catch (err) {
        uploadMsg.textContent = "Error: " + err.message;
        uploadMsg.style.color = "red";
      }
    });
  }

  async function loadDashboard() {
    const claims = await fetchMyClaims();
    const years = Array.from(new Set(claims.map(c => new Date(c.created_at).getFullYear()))).sort();
    const currentYear = new Date().getFullYear();
    if (yearSelect) {
      yearSelect.innerHTML = years.map(y => `<option ${y===currentYear?'selected':''}>${y}</option>`).join('');
    }
    const year = yearSelect ? parseInt(yearSelect.value || currentYear) : currentYear;
    const byMonth = Array(12).fill(0);
    const amtByMonth = Array(12).fill(0);
    let pending=0, approved=0, rejected=0, totalAmt=0;
    claims.forEach(c => {
      const d = new Date(c.created_at);
      if (d.getFullYear() === year) {
        byMonth[d.getMonth()]++;
        amtByMonth[d.getMonth()] += Number(c.amount||0);
      }
      totalAmt += Number(c.amount||0);
      if (c.claim_status==='PENDING') pending++;
      if (c.claim_status==='APPROVED') approved++;
      if (c.claim_status==='REJECTED') rejected++;
    });
    if (statsGrid) {
      statsGrid.innerHTML = `
        <div class='stat-card'><div class='stat-title'>Total Claims</div><div class='stat-value'>${claims.length}</div></div>
        <div class='stat-card'><div class='stat-title'>Approved</div><div class='stat-value'>${approved}</div></div>
        <div class='stat-card'><div class='stat-title'>Rejected</div><div class='stat-value'>${rejected}</div></div>
        <div class='stat-card'><div class='stat-title'>Total Amount</div><div class='stat-value'>₹${totalAmt.toFixed(2)}</div></div>`;
    }
    if (chartMonthly && window.Chart) {
      new Chart(chartMonthly, { type:'bar', data:{ labels:['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'], datasets:[{ label:'Claims', data:byMonth, backgroundColor:'#0926fe', borderRadius:6 }, { label:'Amount (₹)', data:amtByMonth, type:'line', borderColor:'#27ae60', yAxisID:'y1' }] }, options:{ responsive:true, scales:{ y:{ beginAtZero:true }, y1:{ beginAtZero:true, position:'right' } } } });
    }
    if (chartStatus && window.Chart) {
      new Chart(chartStatus, { type:'doughnut', data:{ labels:['Pending','Approved','Rejected'], datasets:[{ data:[pending,approved,rejected], backgroundColor:['#ffeeba','#d4edda','#f8d7da'] }] }, options:{ responsive:true } });
    }
    if (recentTable) {
      const r = claims.slice().sort((a,b)=> new Date(b.created_at)-new Date(a.created_at)).slice(0,10);
      recentTable.innerHTML = r.map(c=>`<tr><td>${c.claim_id}</td><td>${new Date(c.created_at).toLocaleDateString()}</td><td>${c.description}</td><td>₹${Number(c.amount).toFixed(2)}</td><td><span class='badge badge-${c.claim_status}'>${c.claim_status}</span></td><td>${c.document_url?`<a href='${c.document_url}' target='_blank' rel='noopener'>View</a>`:'-'}</td></tr>`).join('');
    }
  }

  async function loadProfileKPIs() {
    try {
      const claims = await fetchMyClaims();
      const totalAmt = claims.reduce((s,c)=>s+Number(c.amount||0),0);
      const pending = claims.filter(c=>c.claim_status==='PENDING').length;
      if (profileStats) {
        profileStats.innerHTML = `
          <div class='stat-card'><div class='stat-title'>Claims so far</div><div class='stat-value'>${claims.length}</div></div>
          <div class='stat-card'><div class='stat-title'>Total amount</div><div class='stat-value'>₹${totalAmt.toFixed(2)}</div></div>
          <div class='stat-card'><div class='stat-title'>Pending</div><div class='stat-value'>${pending}</div></div>`;
      }
    } catch {}
  }

  async function loadHistory() {
    const claims = await fetchMyClaims();
    const years = Array.from(new Set(claims.map(c => new Date(c.created_at).getFullYear()))).sort();
    if (yearFilter) yearFilter.innerHTML = years.map(y=>`<option>${y}</option>`).join('');
    function render() {
      const status = statusFilter ? statusFilter.value : 'all';
      const year = yearFilter ? parseInt(yearFilter.value) : new Date().getFullYear();
      const qEl = document.getElementById('searchQuery');
      const q = qEl ? qEl.value.toLowerCase() : '';
      const filtered = claims.filter(c => (status==='all' || c.claim_status===status) && new Date(c.created_at).getFullYear()===year && ((c.description||'').toLowerCase().includes(q) || (c.claim_id||'').toLowerCase().includes(q)));
      const sorted = filtered.slice().sort((a,b)=> new Date(b.created_at)-new Date(a.created_at));
      const tbody = document.getElementById('claimsTable');
      if (tbody) tbody.innerHTML = sorted.map(c=>`<tr><td>${c.claim_id}</td><td>${new Date(c.created_at).toLocaleDateString()}</td><td>${c.description}</td><td>₹${Number(c.amount).toFixed(2)}</td><td><span class='badge badge-${c.claim_status}'>${c.claim_status}</span></td><td>${c.document_url?`<a href='${c.document_url}' target='_blank' rel='noopener'>View</a>`:'-'}</td></tr>`).join('');
      const ctx = document.getElementById('historyTimeline');
      if (ctx && window.Chart) {
        const byMonth = Array(12).fill(0);
        filtered.forEach(c=>{ const d=new Date(c.created_at); byMonth[d.getMonth()]++; });
        new Chart(ctx, { type:'line', data:{ labels:['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'], datasets:[{ label:'Claims', data:byMonth, borderColor:'#0926fe' }] }, options:{ responsive:true } });
      }
    }
    if (statusFilter) statusFilter.addEventListener('change', render);
    if (yearFilter) yearFilter.addEventListener('change', render);
    const qEl2 = document.getElementById('searchQuery');
    if (qEl2) qEl2.addEventListener('input', render);
    render();
  }

  if (statsGrid || chartMonthly || chartStatus || recentTable) {
    try { await loadDashboard(); } catch {}
    if (yearSelect) yearSelect.addEventListener('change', loadDashboard);
  }
  if (profileStats) { await loadProfileKPIs(); }
  if (document.getElementById('claimsTable')) { await loadHistory(); }
  if (lifecycleList) {
    try {
      const claims = await fetchMyClaims();
      lifecycleList.innerHTML = claims.slice().sort((a,b)=> new Date(b.created_at)-new Date(a.created_at)).map(c=>{
        const status = c.claim_status;
        const docLink = c.document_url ? ` • <a href='${c.document_url}' target='_blank' rel='noopener'>View Document</a>` : '';
        return `
          <div class='card' style='margin-bottom:16px;'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
              <strong>${c.description}</strong>
              <span class='badge badge-${status}'>${status}</span>
            </div>
            <div class='progress-line' style='margin-top:12px;'>
              <div class='progress-fill status-${status}'></div>
            </div>
            <div style='margin-top:8px; color:#6b7d8a;'>ID: ${c.claim_id} • ₹${Number(c.amount).toFixed(2)} • ${new Date(c.created_at).toLocaleDateString()}${docLink}</div>
          </div>`;
      }).join('');
    } catch { lifecycleList.textContent = 'Failed to load lifecycle'; }
  }
});

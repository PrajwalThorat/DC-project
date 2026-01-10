// static/main.js - compact client for DC Projects
let currentProjectId = null;
let currentUser = null;
let activeLegendStatuses = new Set();
let cachedArtists = [];
const LS = {
  TIGHT: "dc_layout_tight",
  COMPACT: "dc_layout_compact",
  MOV: "dc_col_mov",
  EXR: "dc_col_exr",
  COLW: "dc_col_w_"
};

async function apiFetch(url, opts = {}) {
  const res = await fetch(url, opts);
  if (!res.ok) {
    // try parse JSON error body, otherwise throw plain text or status
    let body = null;
    try { body = await res.json(); } catch (e) { body = await res.text().catch(()=>null); }
    const msg = (body && body.error) ? body.error : (typeof body === "string" && body) ? body : res.status;
    const err = new Error(msg);
    err.status = res.status;
    err.body = body;
    throw err;
  }
  // some endpoints return no body (204), handle that
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res.text();
}

/* ---------- Session / Auth ---------- */
async function apiSession() { return apiFetch("/api/session"); }
// example: const sess = await apiSession();

async function apiLoginJson(username, password) {
  return apiFetch("/api/login", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({username, password})
  });
}
// example: const r = await apiLoginJson("admin","admin");

async function apiLogout() {
  return apiFetch("/logout", {method: "POST"});
}
// example: await apiLogout();

/* ---------- Users (Admin) ---------- */
async function apiGetUsers() { return apiFetch("/api/users"); }
async function apiCreateUser({username, password="changeme", role="artist", display_name=""}) {
  return apiFetch("/api/users", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({username, password, role, display_name})
  });
}
async function apiUpdateUser(user_id, data) {
  return apiFetch(`/api/users/${user_id}`, {
    method: "PUT",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(data)
  });
}
async function apiDeleteUser(user_id) {
  return apiFetch(`/api/users/${user_id}`, {method: "DELETE"});
}

/* ---------- Projects ---------- */
async function apiGetProjects() { return apiFetch("/api/projects"); }
async function apiCreateProject({name, start_date="", short="", folder_path="", details_text=""}) {
  return apiFetch("/api/projects", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({name, start_date, short, folder_path, details_text})
  });
}
async function apiGetProject(project_id) { return apiFetch(`/api/projects/${project_id}`); }
async function apiUpdateProject(project_id, data) {
  return apiFetch(`/api/projects/${project_id}`, {
    method: "PUT",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(data)
  });
}
async function apiDeleteProject(project_id) {
  return apiFetch(`/api/projects/${project_id}`, {method: "DELETE"});
}

/* ---------- Shots (per project) ---------- */
async function apiGetShots(project_id, params = {}) {
  // params: {reel, code, description, artist, due, status: [..]} - status can be array
  const qs = new URLSearchParams();
  for (const k of ["reel","code","description","artist","due"]) {
    if (params[k]) qs.append(k, params[k]);
  }
  if (params.status) {
    if (Array.isArray(params.status)) params.status.forEach(s => qs.append("status", s));
    else qs.append("status", params.status);
  }
  const url = `/api/projects/${project_id}/shots${qs.toString() ? "?"+qs.toString() : ""}`;
  return apiFetch(url);
}
async function apiCreateShot(project_id, shotData) {
  // shotData: {code, description, assigned_to, due_date, status, plate_path, mov_path, exr_path}
  return apiFetch(`/api/projects/${project_id}/shots`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(shotData)
  });
}
async function apiGetShot(shot_id) { return apiFetch(`/api/shots/${shot_id}`); }
async function apiUpdateShot(shot_id, data) {
  // e.g. {assigned_to: "artist1", status: "In Progress"}
  return apiFetch(`/api/shots/${shot_id}`, {
    method: "PUT",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(data)
  });
}
async function apiDeleteShot(shot_id) {
  return apiFetch(`/api/shots/${shot_id}`, {method: "DELETE"});
}

/* ---------- Comments ---------- */
async function apiGetComments(shot_id) { return apiFetch(`/api/shots/${shot_id}/comments`); }
async function apiAddComment(shot_id, text) {
  return apiFetch(`/api/shots/${shot_id}/comments`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({text})
  });
}
async function apiUpdateComment(comment_id, text) {
  return apiFetch(`/api/comments/${comment_id}`, {
    method: "PUT",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({text})
  });
}
async function apiDeleteComment(comment_id) {
  return apiFetch(`/api/comments/${comment_id}`, {method: "DELETE"});
}

/* ---------- Thumbnails / file access ---------- */
async function apiGetShotThumbUrl(shot_id) {
  // The /api/shot_thumb/<id> endpoint returns the file directly;
  // return the URL to use in <img src="..."> or window.open
  return `/api/shot_thumb/${shot_id}`;
}

/* ---------- Nuke / generate comp / send to client ---------- */
async function apiGetNukePath(shot_id) { return apiFetch(`/api/shots/${shot_id}/nuke_path`); }
async function apiGenerateComp(shot_id) { return apiFetch(`/api/shots/${shot_id}/generate_comp`, {method: "POST"}); }
async function apiSendToClient(shot_id) { return apiFetch(`/api/shots/${shot_id}/send_to_client`, {method: "POST"}); }

/* ---------- Export / raw ---------- */
async function apiExportCSV(project_id, params={}) {
  // opens CSV in new tab - returns URL string so UI can open it
  const qs = new URLSearchParams();
  if (params.status) {
    if (Array.isArray(params.status)) params.status.forEach(s=>qs.append("status", s));
    else qs.append("status", params.status);
  }
  if (params.reel) qs.append("reel", params.reel);
  if (params.code) qs.append("code", params.code);
  return `/api/projects/${project_id}/export_csv${qs.toString() ? "?"+qs.toString() : ""}`;
}
async function apiGetProjectRaw(project_id) { return apiFetch(`/api/projects/${project_id}/raw`); }

/* ---------- Health ---------- */
async function apiHealth() { return apiFetch("/_health"); }


async function fetchJSON(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) {
    const txt = await r.text().catch(()=>"");
    throw new Error(txt || r.status);
  }
  return r.json();
}

// Helper to open local filesystem paths in a cross-platform way
function openFolderPath(p) {
  if (!p) { alert('Path not provided'); return; }
  try {
    let path = String(p);
    if (/^https?:\/\//i.test(path) || /^file:\/\//i.test(path)) { window.open(path); return; }
    path = path.replace(/\\\\/g, '/');
    if (/^[A-Za-z]:\//.test(path)) path = 'file:///' + path;
    else if (path.startsWith('/')) path = 'file://' + path;
    else path = 'file:///' + path;
    window.open(encodeURI(path));
  } catch(e) { console.error('openFolderPath error', e); window.open(p); }
}

function applyColVisibility() {
  const mov = localStorage.getItem(LS.MOV);
  const exr = localStorage.getItem(LS.EXR);
  document.body.classList.toggle("hide-mov", mov === "0");
  document.body.classList.toggle("hide-exr", exr === "0");
  document.getElementById("toggleMovBtn").textContent = (mov === "0") ? "MOV ✗" : "MOV ✓";
  document.getElementById("toggleExrBtn").textContent = (exr === "0") ? "EXR ✗" : "EXR ✓";
  document.getElementById("openUserModal").animate(apiCreateShot())
}

function setTightMode(v) { document.body.classList.toggle("tight", v); document.getElementById("toggleLayoutBtn").textContent = v ? "Tight ✓" : "Tight"; }
function setCompactMode(v) { document.body.classList.toggle("compact", v); document.getElementById("toggleCompactBtn").textContent = v ? "Compact ✓" : "Compact"; }

async function getSession() {
  try {
    const data = await fetchJSON("/api/session");
    if (!data.logged_in) {
      document.getElementById("userLabel").textContent = "";
    } else {
      currentUser = data;
      document.getElementById("userLabel").textContent = `${data.username} (${data.role})`;
    }
  } catch (err) { console.warn("session check failed", err); }
}

async function loadProjects() {
  try {
    const projects = await fetchJSON("/api/projects");
    const ul = document.getElementById("projectList");
    ul.innerHTML = "";
    projects.forEach(p => {
      const li = document.createElement("li"); li.textContent = p.name; li.dataset.id = p.id;
      li.onclick = () => { document.querySelectorAll("#projectList li").forEach(x=>x.classList.remove("active")); li.classList.add("active"); selectProject(p); };
      ul.appendChild(li);
    });
  } catch (err) { console.error(err); }
}

function selectProject(p) {
  currentProjectId = p.id;
  document.getElementById("pdName").textContent = p.name;
  document.getElementById("pdStart").textContent = p.start_date || "";
  document.getElementById("pdDesc").textContent = p.details_text || "";
  if (p.folder_path) document.getElementById("projectLogo").src = p.folder_path + "/Detail/logo.png";
  loadShots();
}

function syncLegendUI() {
  document.querySelectorAll("#legendRow .legend-item").forEach(it => {
    const s = it.getAttribute("data-status");
    if (activeLegendStatuses.has(s)) it.classList.add("active"); else it.classList.remove("active");
  });
}

async function loadShots(queryString = '') {
  if (!currentProjectId) return;
  const qs = new URLSearchParams();
  const reel = (document.getElementById("filterReel") && document.getElementById("filterReel").value||"").trim();
  const version = (document.getElementById("filterVersion") && document.getElementById("filterVersion").value||"").trim();
  const code = (document.getElementById("filterShotCode") && document.getElementById("filterShotCode").value||"").trim();
  // description removed from table filters
  const artist = document.getElementById("filterArtist").value.trim();
  const due = document.getElementById("filterDue").value.trim();
  if (reel) qs.append("reel", reel);
  if (version) qs.append("version", version);
  if (code) qs.append("code", code);
  if (artist) qs.append("artist", artist);
  if (due) qs.append("due", due);
  if (activeLegendStatuses.size > 0) activeLegendStatuses.forEach(s => qs.append("status", s));
  const url = `/api/projects/${currentProjectId}/shots` + (qs.toString() ? "?" + qs.toString() : "");
  try {
    const shots = await fetchJSON(url);
    // if grouped response (array of {reel,count}) then render groups,
    // else render shots list as before
    if (shots.length && shots[0].hasOwnProperty('count') && shots[0].hasOwnProperty('reel')) {
      renderShotGroupsByReel(shots);
    } else {
      renderShotsList(shots);
    }
  } catch (err) { console.error(err); }
}

function isVideoPath(path) { if (!path) return false; const e = path.split(".").pop().toLowerCase(); return e==="mp4"||e==="mov"; }
function isImagePath(path) { if (!path) return false; const e = path.split(".").pop().toLowerCase(); return ["jpg","jpeg","png"].includes(e); }

function renderShots(shots) {
  const tbody = document.querySelector("#shotTable tbody");
  tbody.innerHTML = "";
  // populate reel & artist filters
  const reels = new Set(); const artists = new Set();
  shots.forEach(s => { const r = (s.reel && s.reel.trim()) ? s.reel : (s.code||"").split("_")[1]; if (r) reels.add(r); if (s.assigned_to) artists.add(s.assigned_to); });
  const fr = document.getElementById("filterReel"); if (fr) { fr.innerHTML = '<option value="">All Reels</option>'; Array.from(reels).sort().forEach(r=>{ const o=document.createElement("option"); o.value=r; o.textContent=r; fr.appendChild(o); }); }
  const fa = document.getElementById("filterArtist"); if (fa) { fa.innerHTML = '<option value="">All Artists</option>'; Array.from(artists).sort().forEach(a=>{ const o=document.createElement("option"); o.value=a; o.textContent=a; fa.appendChild(o); }); }

  shots.forEach(s=>{
    if (activeLegendStatuses.size>0 && !activeLegendStatuses.has(s.status)) return;
    const tr = document.createElement("tr"); tr.dataset.id = s.id; tr.className = "";
    const selectTd = document.createElement("td"); selectTd.style.textAlign = 'center';
    const selCb = document.createElement('input'); selCb.type='checkbox'; selCb.className='shot-select'; selCb.dataset.id = s.id; selCb.onclick = (e)=>{ e.stopPropagation(); updateBulkDeleteVisibility(); };
    selectTd.appendChild(selCb);
    tr.appendChild(selectTd);

    const thumbTd = document.createElement("td"); thumbTd.setAttribute("data-col","thumb");
    if (isImagePath(s.plate_path)) {
      const img = document.createElement("img"); img.src = `/api/shot_thumb/${s.id}`; img.className="shot-thumb"; thumbTd.appendChild(img);
    } else {
      const btn = document.createElement("button"); btn.textContent = isVideoPath(s.plate_path)? "▶":"□"; btn.disabled = !s.plate_path; btn.onclick = (e)=>{ e.stopPropagation(); openFolderPath(s.plate_path); };
      thumbTd.appendChild(btn);
    }
    tr.appendChild(thumbTd);

    const codeTd = document.createElement("td"); codeTd.textContent = s.code; tr.appendChild(codeTd);
    const reelTd = document.createElement("td"); reelTd.textContent = (s.reel && s.reel.trim()) ? s.reel : ((s.code||"").split("_")[1] || ""); tr.appendChild(reelTd);
    const verTd = document.createElement("td"); verTd.textContent = s.version || ""; tr.appendChild(verTd);

    const artistTd = document.createElement("td"); const artistSpan=document.createElement("span"); artistSpan.textContent = s.assigned_to||""; artistTd.appendChild(artistSpan); tr.appendChild(artistTd);
    const dueTd = document.createElement("td"); dueTd.textContent = s.due_date||""; tr.appendChild(dueTd);

    const statusTd = document.createElement("td"); const sel = document.createElement("select");
    ["Not Started","In Progress","On Hold","Kickback","In Review","Approved","Final"].forEach(st=>{ const o=document.createElement("option"); o.value=st; o.textContent=st; if (st===s.status) o.selected=true; sel.appendChild(o); });
    sel.onchange = async ()=>{ try{ await fetch(`/api/shots/${s.id}`, {method:"PUT", headers:{"Content-Type":"application/json"}, body: JSON.stringify({status: sel.value})}); tr.className=""; } catch(e){ alert("Error update"); } };
    statusTd.appendChild(sel); tr.appendChild(statusTd);

    const movTd=document.createElement("td"); const movBtn=document.createElement("button"); movBtn.textContent = s.mov_path? "📁":"-"; movBtn.disabled = !s.mov_path; movBtn.onclick=(e)=>{ e.stopPropagation(); openFolderPath(s.mov_path); }; movTd.appendChild(movBtn); tr.appendChild(movTd);

    const exrTd=document.createElement("td"); const exrBtn=document.createElement("button"); exrBtn.textContent = s.exr_path? "📁":"-"; exrBtn.disabled = !s.exr_path; exrBtn.onclick=(e)=>{ e.stopPropagation(); openFolderPath(s.exr_path); }; exrTd.appendChild(exrBtn); tr.appendChild(exrTd);

    const nukeTd=document.createElement("td"); const nukeBtn=document.createElement("button"); nukeBtn.textContent="Nuke"; nukeBtn.onclick=async()=>{ try{ const d=await fetchJSON(`/api/shots/${s.id}/nuke_path`); if (d.path) openFolderPath(d.path); else alert("Nuke path not configured"); }catch(e){alert("Error");} }; nukeTd.appendChild(nukeBtn); tr.appendChild(nukeTd);

    const actionsTd=document.createElement("td");
    const genBtn=document.createElement("button"); genBtn.textContent="GenComp"; genBtn.onclick=async(e)=>{ e.stopPropagation(); try{ const res=await fetch(`/api/shots/${s.id}/generate_comp`, {method:"POST"}); const r=await res.json(); if (!res.ok) alert(r.error||"Generate failed"); else alert("Created: "+r.path); loadShots(); }catch(err){alert("Error");} };
    actionsTd.appendChild(genBtn);
    const delBtn=document.createElement("button"); delBtn.textContent="Del"; delBtn.onclick=async(e)=>{ e.stopPropagation(); if (!confirm("Delete?")) return; try{ await fetch(`/api/shots/${s.id}`, {method:"DELETE"}); loadShots(); }catch(err){alert("Error deleting");} };
    actionsTd.appendChild(delBtn);
    tr.appendChild(actionsTd);

    // attach click to load comments / preview (ignore clicks on checkbox)
    tr.onclick = (e)=>{ if (e.target && e.target.classList && e.target.classList.contains('shot-select')) return; document.querySelectorAll("#shotTable tbody tr").forEach(r=>r.classList.remove("active")); tr.classList.add("active"); loadComments(s.id, s.code); };
    tbody.appendChild(tr);
  });
}

function updateBulkDeleteVisibility(){
  const any = Array.from(document.querySelectorAll('.shot-select')).some(c=>c.checked);
  let btn = document.getElementById('bulkDeleteBtnMain');
  if (!btn) return;
  btn.style.display = any ? '' : 'none';
}

async function loadComments(shotId, shotCode) {
  document.getElementById("commentsInfo").textContent = shotCode || ("Shot " + shotId);
  document.getElementById("commentBox").classList.remove("hidden");
  const list = document.getElementById("commentsList"); list.innerHTML = "";
  try {
    const comments = await fetchJSON(`/api/shots/${shotId}/comments`);
    comments.forEach(c=> {
      const div = document.createElement("div"); div.className="comment-item";
      div.innerHTML = `<div class="comment-meta">${c.author} • ${c.created_at}</div><div class="comment-text">${c.text}</div>`;
      list.appendChild(div);
    });
  } catch(e){ console.error(e); }
}

function applyShotFilters() {
  const reel = document.getElementById('reelFilter').value.trim();
  const group_by = document.getElementById('groupBySelect').value;

  const params = new URLSearchParams();
  if (reel) params.append('reel', reel);
  if (group_by) params.append('group_by', group_by);

  // assume currentProjectId is available in page context
  loadShots(`?${params.toString()}`);
}

function renderShotGroupsByReel(groups) {
  const container = document.getElementById('shots-list');
  container.innerHTML = '';
  groups.forEach(g => {
    const header = document.createElement('h4');
    header.textContent = `Reel: ${g.reel || '(empty)'} — ${g.count} shots`;
    container.appendChild(header);
    // optionally, fetch shots for that reel and render below header:
    fetch(`/api/projects/${currentProjectId}/shots?reel=${encodeURIComponent(g.reel)}`, { credentials: 'same-origin' })
      .then(r => r.json())
      .then(shots => {
        const ul = document.createElement('div');
        shots.forEach(s => {
          const div = document.createElement('div');
          div.className = 'shot-row';
          div.textContent = `${s.code} — ${s.description || ''}`;
          ul.appendChild(div);
        });
        container.appendChild(ul);
      });
  });
}

document.addEventListener("DOMContentLoaded", async ()=>{
  await getSession();
  applyColVisibility();
  setTightMode(localStorage.getItem(LS.TIGHT)==="1");
  setCompactMode(localStorage.getItem(LS.COMPACT)==="1");
  loadProjects();

  document.getElementById("legendRow").querySelectorAll(".legend-item").forEach(it=>{
    it.addEventListener("click", ()=>{
      const s = it.getAttribute("data-status");
      if (activeLegendStatuses.has(s)) activeLegendStatuses.delete(s); else activeLegendStatuses.add(s);
      syncLegendUI(); loadShots();
    });
  });
  document.getElementById("legendSelectAll").addEventListener("click", ()=>{ document.querySelectorAll("#legendRow .legend-item").forEach(it=>activeLegendStatuses.add(it.getAttribute("data-status"))); syncLegendUI(); loadShots(); });
  document.getElementById("legendClearAll").addEventListener("click", ()=>{ activeLegendStatuses.clear(); syncLegendUI(); loadShots(); });

  document.getElementById("toggleMovBtn").addEventListener("click", ()=>{ const cur = localStorage.getItem(LS.MOV); localStorage.setItem(LS.MOV, cur==="0"?"1":"0"); applyColVisibility(); });
  document.getElementById("toggleExrBtn").addEventListener("click", ()=>{ const cur = localStorage.getItem(LS.EXR); localStorage.setItem(LS.EXR, cur==="0"?"1":"0"); applyColVisibility(); });

  document.getElementById("applyFilterBtn").addEventListener("click", (e)=>{ e.preventDefault(); loadShots(); });
  document.getElementById("clearFilterBtn").addEventListener("click", ()=>{ document.getElementById("filterReel").value=""; document.getElementById("filterShotCode").value=""; document.getElementById("filterDesc").value=""; document.getElementById("filterArtist").value=""; document.getElementById("filterDue").value=""; activeLegendStatuses.clear(); syncLegendUI(); loadShots(); });

  document.getElementById("projectForm").addEventListener("submit", async (e)=>{ e.preventDefault(); try{ const name=document.getElementById("projectName").value; const start=document.getElementById("projectStart").value; await fetch("/api/projects",{method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({name, start_date:start})}); document.getElementById("projectForm").reset(); loadProjects(); }catch(err){alert("Error creating project");} });

  document.getElementById("exportCsvBtn").addEventListener("click", ()=>{ if (!currentProjectId) { alert("Select a project"); return; } const qs = new URLSearchParams(); if (activeLegendStatuses.size>0) activeLegendStatuses.forEach(s=>qs.append("status", s)); const url = `/api/projects/${currentProjectId}/export_csv` + (qs.toString() ? "?"+qs.toString() : ""); window.open(url); });

  // bulk delete button for main table view
  (function(){
    const sc = document.querySelector('.shots-controls');
    if (sc) {
      let btn = document.createElement('button'); btn.id = 'bulkDeleteBtnMain'; btn.textContent = 'Delete Selected'; btn.style.background = '#b23131'; btn.style.color = '#fff'; btn.style.display = 'none'; btn.style.padding = '8px 12px'; btn.style.borderRadius = '4px'; btn.style.border = 'none'; btn.style.cursor = 'pointer'; btn.style.fontWeight = 'bold'; btn.onclick = async ()=>{
        const ids = Array.from(document.querySelectorAll('.shot-select:checked')).map(c=>parseInt(c.dataset.id));
        if (!ids.length) { alert('No shots selected'); return; }
        if (!confirm(`Delete ${ids.length} selected shots?`)) return;
        try {
          const res = await fetch('/api/shots/bulk_delete', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ids})});
          const data = await res.json();
          if (!res.ok) throw new Error(data.error||JSON.stringify(data));
          alert('Deleted ' + (data.deleted||0) + ' shots');
          loadShots(currentProjectId);
        } catch (e){ alert('Delete failed: '+e.message); }
      };
      // Update delete button visibility whenever checkboxes change
      document.querySelectorAll('.shot-select').forEach(cb => {
        cb.addEventListener('change', () => { btn.style.display = Array.from(document.querySelectorAll('.shot-select')).some(c=>c.checked) ? '' : 'none'; });
      });
      sc.appendChild(btn);
    }
  })();

  document.getElementById("addCommentBtn").addEventListener("click", async ()=>{ const txt=document.getElementById("commentText").value.trim(); if (!txt) return; const tr = document.querySelector("#shotTable tbody tr.active"); if (!tr) { alert("Select shot"); return; } const sid = tr.dataset.id; try{ await fetch(`/api/shots/${sid}/comments`, {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({text: txt})}); document.getElementById("commentText").value=""; loadComments(sid); }catch(e){alert("Error adding");} });

  document.getElementById("logoutBtn").addEventListener("click", async ()=>{ await fetch("/logout",{method:"POST"}); window.location.href="/login"; });

});

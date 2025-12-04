// app/static/js/app.js

// ========= Config & Helpers =========
const $ = (sel) => document.querySelector(sel);

function setToken(token) {
  const badge = $("#authStatus");
  const logoutBtn = $("#btnLogout");
  if (token) {
    localStorage.setItem("token", token);
    if (badge) badge.textContent = "connecté";
    if (logoutBtn) logoutBtn.style.display = "";
  } else {
    localStorage.removeItem("token");
    if (badge) badge.textContent = "déconnecté";
    if (logoutBtn) logoutBtn.style.display = "none";
  }
}
function getToken() { return localStorage.getItem("token"); }

async function apiFetch(url, opts = {}) {
  let { method="GET", body=null, auth=false, json=true, form=false } = opts;
  const headers = {};
  let payload = body;

  // AUTO-DETECTION : Si le corps est un formulaire, on passe en mode form
  if (body instanceof URLSearchParams || body instanceof FormData) {
      form = true;
      json = false;
  }

  if (auth) {
    const t = getToken();
    if (t) headers["Authorization"] = `Bearer ${t}`;
  }

  if (form) {
    // On laisse le navigateur gérer le Content-Type pour les formulaires
  } else if (json) {
    headers["Content-Type"] = "application/json";
    payload = body != null ? JSON.stringify(body) : null;
  }

  const res = await fetch(url, { method, headers, body: payload });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      // On affiche le détail technique pour débugger
      detail = typeof data?.detail === "string" ? data.detail : JSON.stringify(data?.detail || data);
    } catch {}
    throw new Error(detail);
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : null;
}

function toast(el, msg, ok = true) {
  if (!el) return;
  el.textContent = msg;
  el.className = ok ? "muted ok" : "muted err";
}

// ========= Variables Pagination =========
let currentOffset = 0;
const PAGE_SIZE = 50;

// ========= Players (Marché) =========
async function loadPlayers() {
  const list = $("#playersList");
  const msg = $("#playersMsg");
  const btnPrev = $("#btnPrev");
  const btnNext = $("#btnNext");
  const pageInd = $("#pageIndicator");

  if (list) list.innerHTML = "";
  toast(msg, "Chargement…", true);

  try {
    const url = `/players?skip=${currentOffset}&limit=${PAGE_SIZE}`;
    const data = await apiFetch(url);

    if (!Array.isArray(data)) throw new Error("format inattendu");

    if (!data.length) {
      list.innerHTML = `<div class="muted">Aucun joueur trouvé.</div>`;
      if (btnNext) btnNext.disabled = true;
    } else {
      if (btnNext) btnNext.disabled = (data.length < PAGE_SIZE);

      for (const p of data) {
        const row = document.createElement("div");
        row.className = "player";
        row.innerHTML = `
          <div><strong>${p.name}</strong><div class="muted">${p.club || "-"}</div></div>
          <div class="pill nowrap">${p.position || "-"}</div>
          <div class="pill right">${(p.cost ?? p.price ?? 0).toLocaleString()} €</div>
          <div class="right">
            <button class="add">Ajouter</button>
          </div>
        `;
        // Clic pour Ajouter
        const addBtn = row.querySelector(".add");
        addBtn.onclick = () => addPlayerToTeam(p.id);
        
        list.appendChild(row);
      }
    }
    
    if (btnPrev) btnPrev.disabled = (currentOffset === 0);
    if (pageInd) {
        const pageNum = Math.floor(currentOffset / PAGE_SIZE) + 1;
        pageInd.textContent = `Page ${pageNum}`;
    }
    toast(msg, `OK (${data.length} joueurs)`);

  } catch (e) {
    toast(msg, e.message, false);
  }
}

function prevPage() {
    if (currentOffset >= PAGE_SIZE) {
        currentOffset -= PAGE_SIZE;
        loadPlayers();
    }
}
function nextPage() {
    currentOffset += PAGE_SIZE;
    loadPlayers();
}

// ========= Team (Le Terrain) =========
async function loadTeam() {
  const nameEl = $("#teamTitle");
  const budgetEl = $("#teamBudget");
  const pitchEl = $("#soccerPitch"); // <--- Cible le terrain
  const msg = $("#teamMsg");

  if (pitchEl) pitchEl.innerHTML = "";
  if (nameEl) nameEl.textContent = "–";
  if (budgetEl) budgetEl.textContent = "–";

  try {
    const t = await apiFetch("/team", { auth: true });

    // Infos
    if (nameEl) nameEl.textContent = t?.name ?? "–";
    if (budgetEl)
      budgetEl.textContent = t?.budget_left != null 
        ? `${t.budget_left.toLocaleString()} €` 
        : "–";

    // Barre Budget
    const bar = $("#budgetBar");
    if (bar && t?.total_budget) {
        const pct = Math.max(0, (t.budget_left / t.total_budget) * 100);
        bar.style.width = `${pct}%`;
        bar.style.backgroundColor = (pct < 10) ? "#ff5c5c" : "#7fffb0";
    }

    const players = Array.isArray(t?.players) ? t.players : [];
    if (!pitchEl) return;

    // --- LOGIQUE TERRAIN ---
    // Trier par poste
    const formation = { "FWD": [], "MID": [], "DEF": [], "GK": [] };
    players.forEach(p => {
        const pos = (p.position && formation[p.position]) ? p.position : "MID";
        formation[pos].push(p);
    });

    // Afficher ligne par ligne (Haut vers Bas)
    const rowsOrder = ["FWD", "MID", "DEF", "GK"];
    const limits = { "FWD": 3, "MID": 3, "DEF": 4, "GK": 1 };
    rowsOrder.forEach(posKey => {
        const rowDiv = document.createElement("div");
        rowDiv.className = "pitch-row";
        const rowPlayers = formation[posKey];

        const max = limits[posKey];


        // Espace vide si personne
        if (rowPlayers.length === 0) rowDiv.style.minHeight = "80px";

        rowPlayers.forEach(p => {
            const token = document.createElement("div");
            token.className = "player-token";
            token.innerHTML = `
                <div class="player-pos">${p.position}</div>
                <div class="player-name" title="${p.name}">${p.name}</div>
                <div class="player-cost">${(p.cost || 0).toLocaleString()}</div>
            `;

            // Bouton X (Supprimer)
            const btnX = document.createElement("div");
            btnX.className = "btn-remove-x";
            btnX.textContent = "✕";
            
            // On attache la fonction directement à l'élément DOM created
            btnX.onclick = function() {
                removePlayerFromTeam(p.id);
            };

            token.appendChild(btnX);
            rowDiv.appendChild(token);
        });
        pitchEl.appendChild(rowDiv);
    });

  } catch (e) {
    toast(msg, e.message, false);
  }
}

// ========= Actions =========
async function createTeam(ev) {
  ev.preventDefault();
  const nameInput = $("#teamName");
  const name = nameInput.value.trim();
  const msg = $("#teamMsg");
  if (!name) return toast(msg, "Nom requis", false);

  try {
    await apiFetch("/team", { method: "POST", body: { name }, auth: true });
    toast(msg, "Équipe créée", true);
    nameInput.value = "";
    await loadTeam();
  } catch (e) {
    toast(msg, e.message, false);
  }
}

async function addPlayerToTeam(playerId) {
  const msg = $("#teamMsg");
  try {
    await apiFetch("/team/players", { method: "POST", body: [playerId], auth: true });
    await loadTeam();
    toast(msg, "Joueur ajouté", true);
  } catch (e) {
    toast(msg, e.message, false);
  }
}

async function removePlayerFromTeam(playerId) {
  const msg = $("#teamMsg");
  try {
    // console.log("Suppression joueur", playerId);
    await apiFetch(`/team/players/${playerId}`, { method: "DELETE", auth: true });
    await loadTeam();
    toast(msg, "Joueur retiré", true);
   } catch (e) {
    toast(msg, e.message, false);
  }
}

// ========= Auth =========
async function register() {
  const email = $("#regEmail")?.value.trim();
  const password = $("#regPassword")?.value;
  const msg = $("#regMsg");
  if (!email || !password) return toast(msg, "Email/MDP requis", false);

  try {
    await apiFetch("/auth/register", { method: "POST", body: { email, password } });
    toast(msg, "Compte créé ✅", true);
  } catch (e) {
    toast(msg, e.message, false);
  }
}

async function login() {
  const email = $("#loginEmail")?.value.trim();
  const password = $("#loginPassword")?.value;
  const msg = $("#loginMsg");
  if (!email || !password) return toast(msg, "Email/MDP requis", false);

  try {
    const fd = new URLSearchParams();
    fd.set("username", email);
    fd.set("password", password);

    const data = await apiFetch("/auth/login", { method: "POST", body: fd, form: true });
    setToken(data?.access_token || "");
    toast(msg, "Connecté ✅", true);
    switchTab('game'); // Bascule auto
    await loadTeam();
  } catch (e) {
    setToken("");
    toast(msg, e.message, false);
  }
}

// ========= Init & Tabs =========
function switchTab(tabName) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

  const contentId = (tabName === 'auth') ? 'viewAuth' : 'viewGame';
  document.getElementById(contentId).classList.add('active');

  const btns = document.querySelectorAll('.tab-btn');
  if (btns.length >= 2) {
      if (tabName === 'auth') btns[0].classList.add('active');
      else btns[1].classList.add('active');
  }
}
window.switchTab = switchTab; // Pour le HTML onclick

function boot() {
  setToken(getToken());

  // Listeners
  $("#btnRegister")?.addEventListener("click", register);
  $("#btnLogin")?.addEventListener("click", login);
  $("#btnCreateTeam")?.addEventListener("click", createTeam);
  $("#btnRefreshPlayers")?.addEventListener("click", () => {
      currentOffset = 0;
      loadPlayers();
  });
  $("#btnLogout")?.addEventListener("click", () => {
      setToken("");
      switchTab('auth');
  });

  $("#btnPrev")?.addEventListener("click", prevPage);
  $("#btnNext")?.addEventListener("click", nextPage);

  const nameInput = $("#teamName");
  const createBtn = $("#btnCreateTeam");
  if(nameInput && createBtn) {
    nameInput.addEventListener("input", () => {
        createBtn.disabled = !nameInput.value.trim();
    });
    createBtn.disabled = !nameInput.value.trim();
  }

  // Premier chargement
  loadPlayers();
  if (getToken()) {
      switchTab('game');
      loadTeam();
  } else {
      switchTab('auth');
  }
}

document.addEventListener("DOMContentLoaded", boot);
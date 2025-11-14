// ========= Config =========
const API = ""; // même origine
const $ = (sel) => document.querySelector(sel);

// ========= Token handling =========
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
function getToken() {
  return localStorage.getItem("token");
}

// ========= Fetch helper =========
async function apiFetch(url, opts = {}) {
  const { method="GET", body=null, auth=false, json=true, form=false } = opts;
  const headers = {};
  let payload = body;

  if (auth) {
    const t = getToken();
    if (t) headers["Authorization"] = `Bearer ${t}`;
  }
  if (form) {
    // ne rien faire, le navigateur mettra le bon Content-Type
  } else if (json) {
    headers["Content-Type"] = "application/json";
    payload = body != null ? JSON.stringify(body) : null;
  }

  const res = await fetch(url, { method, headers, body: payload });
  if (!res.ok) {
  let detail = `HTTP ${res.status}`;
  try {
    const data = await res.json();
    detail = typeof data?.detail === "string" ? data.detail : JSON.stringify(data);
  } catch {}
  throw new Error(detail);
}
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : null;
}


// ========= UI helpers =========
function toast(el, msg, ok = true) {
  if (!el) return;
  el.textContent = msg;
  el.className = ok ? "muted ok" : "muted err";
}

// ========= Players =========
async function loadPlayers() {
  const list = $("#playersList");
  const msg = $("#playersMsg");
  if (list) list.innerHTML = "";
  toast(msg, "Chargement…", true);
  try {
    const data = await apiFetch("/players");
    if (!Array.isArray(data) || !list) throw new Error("format inattendu");

    if (!data.length) {
      list.innerHTML = `<div class="muted">Aucun joueur pour l’instant.</div>`;
    } else {
      for (const p of data) {
        const row = document.createElement("div");
        row.className = "player";
        row.innerHTML = `
          <div><strong>${p.name}</strong><div class="muted">${p.club || "-"}</div></div>
          <div class="pill nowrap">${p.position || "-"}</div>
          <div class="pill right">${(p.cost ?? p.price ?? 0).toLocaleString()} €</div>
          <div class="right">
            <button data-id="${p.id}" class="add">Ajouter</button>
          </div>
        `;
        row.querySelector(".add").addEventListener("click", () => addPlayerToTeam(p.id));
        list.appendChild(row);
      }
    }
    toast(msg, `OK (${data.length})`);
  } catch (e) {
  const errText = (e && e.message) ? e.message : String(e);
  toast(msg, errText, false);
}

}

// ========= Team =========
async function loadTeam() {
  const nameEl = $("#teamTitle");
  const budgetEl = $("#teamBudget");
  const playersEl = $("#teamPlayers");
  const msg = $("#teamMsg");

  if (playersEl) playersEl.innerHTML = "";
  if (nameEl) nameEl.textContent = "–";
  if (budgetEl) budgetEl.textContent = "–";
  toast(msg, "Chargement…", true);

  try {
    const t = await apiFetch("/team", { auth: true });
    if (nameEl) nameEl.textContent = t?.name ?? "–";
    if (budgetEl)
      budgetEl.textContent =
        t?.budget_left != null ? `${t.budget_left.toLocaleString()} €` : "–";

    const arr = Array.isArray(t?.players) ? t.players : [];
    if (!playersEl) return;
    if (!arr.length) {
      playersEl.innerHTML = `<div class="muted">Aucun joueur dans l’équipe.</div>`;
    } else {
      for (const p of arr) {
        const item = document.createElement("div");
        item.className = "player";
        item.innerHTML = `
          <div><strong>${p.name}</strong><div class="muted">${p.club || "-"}</div></div>
          <div class="pill nowrap">${p.position || "-"}</div>
          <div class="pill right">${(p.cost ?? p.price ?? 0).toLocaleString()} €</div>
          <div class="right"><button class="ghost remove" data-id="${p.id}">Retirer</button></div>
        `;
        item.querySelector(".remove").addEventListener("click", () => removePlayerFromTeam(p.id));
        playersEl.appendChild(item);
      }
    }
    toast(msg, "OK");
  } catch (e) {
  const errText = (e && e.message) ? e.message : String(e);
  toast(msg, errText, false);
}

}

async function createTeam(ev) {
  ev.preventDefault();
  const name = $("#teamName").value.trim();
  const msg = $("#teamMsg");
  if (!name) return toast(msg, "Nom requis", false);

  try {
    await apiFetch("/team", { method: "POST", body: { name }, auth: true }); // ✅ pas de ?local_kw=
    toast(msg, "Équipe créée", true);
    $("#teamName").value = "";
    await loadTeam();
  } catch (e) {
    const errText = (e && e.message) ? e.message : String(e);
    toast(msg, errText, false);  // pas d’[object Object]
  }
}

async function addPlayerToTeam(playerId) {
  const msg = $("#teamMsg");
  try {
    // backend attend List[int] -> on envoie [playerId]
    await apiFetch("/team/players", { method: "POST", body: [playerId], auth: true });
    await loadTeam();
    toast(msg, "Joueur ajouté", true);
  } catch (e) {
  const errText = (e && e.message) ? e.message : String(e);
  toast(msg, errText, false);
}

}

async function removePlayerFromTeam(playerId) {
  const msg = $("#teamMsg");
  try {
    await apiFetch(`/team/players/${playerId}`, { method: "DELETE", auth: true });
    await loadTeam();
    toast(msg, "Joueur retiré", true);
   } catch (e) {
  const errText = (e && e.message) ? e.message : String(e);
  toast(msg, errText, false);
}

}

// ========= Auth =========
async function register() {
  const email = $("#regEmail")?.value.trim();
  const password = $("#regPassword")?.value;
  const msg = $("#regMsg");
  if (!email || !password) return toast(msg, "Email et mot de passe requis", false);

  try {
    await apiFetch("/auth/register", { method: "POST", body: { email, password } });
    toast(msg, "Compte créé ✅", true);
  } catch (e) {
  const errText = (e && e.message) ? e.message : String(e);
  toast(msg, errText, false);
}

}

async function login() {
  const email = $("#loginEmail")?.value.trim();
  const password = $("#loginPassword")?.value;
  const msg = $("#loginMsg");
  if (!email || !password) return toast(msg, "Email et mot de passe requis", false);

  try {
    // OAuth2PasswordRequestForm -> x-www-form-urlencoded
    const fd = new URLSearchParams();
    fd.set("username", email);
    fd.set("password", password);

    const data = await apiFetch("/auth/login", {
      method: "POST",
      body: fd,
      form: true,
    });

    setToken(data?.access_token || "");
    toast(msg, "Connecté ✅", true);
    await loadTeam();
  } catch (e) {
    setToken("");
    toast(msg, e.message, false);
  }
}

// ========= Init =========
function boot() {
  setToken(getToken());

  // Boutons (on ne s'appuie plus sur les <form> submit)
  $("#btnRegister")?.addEventListener("click", register);
  $("#btnLogin")?.addEventListener("click", login);
  $("#btnCreateTeam")?.addEventListener("click", createTeam);
  $("#btnRefreshPlayers")?.addEventListener("click", loadPlayers);
  $("#btnLogout")?.addEventListener("click", () => setToken(""));

  // Activer/désactiver le bouton créer en fonction du champ
  const nameInput = $("#teamName");
  const createBtn = $("#btnCreateTeam");
  function updateCreateBtn() {
    if (createBtn) createBtn.disabled = !(nameInput && nameInput.value.trim());
  }
  nameInput?.addEventListener("input", updateCreateBtn);
  updateCreateBtn();

  // Premier chargement
  loadPlayers();
  if (getToken()) loadTeam();
}

document.addEventListener("DOMContentLoaded", boot);

const API = (window.APP_CONFIG || {}).API_BASE || "";
const $ = id => document.getElementById(id);
const S = { scenes: [], title: "", approved: false, job: null };
const SHORT = "Hello, and welcome! I am B. Hallison F. Thomas, a mathematics educator, problem solver, and mathematics Olympiad trainer. Let's begin!";
const FULL = "Hello, and welcome! I am B. Hallison F. Thomas, a mathematics educator, problem solver, and mathematics Olympiad trainer.\n\nWelcome to this lesson, where we will explore mathematical ideas step by step, understand the reasoning behind the methods, and develop the skills to solve problems with confidence.\n\nGet your notebook ready, pay close attention, and let's begin!";
const tok = () => sessionStorage.getItem("tok") || "";
const say = (id, t, err) => { const e = $(id); e.textContent = t; e.className = "msg" + (err ? " err" : ""); };

async function api(path, o = {}) {
  o.headers = Object.assign({ Authorization: "Bearer " + tok() }, o.headers || {});
  let r; try { r = await fetch(API + "/api" + path, o); } catch { throw new Error("Cannot reach the backend. Check Settings and your connection."); }
  if (!r.ok) { let d = ""; try { d = (await r.json()).detail; } catch {} throw new Error(typeof d === "string" && d ? d : "Error " + r.status); }
  return r;
}
const json = (b) => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) });

function show(p) { document.querySelectorAll("main section").forEach(s => s.hidden = s.id !== p); if (p === "dash" || p === "voice") refresh(); if (p === "video") estimate(); }
document.querySelectorAll("[data-p]").forEach(b => b.onclick = () => show(b.dataset.p));
document.querySelectorAll("[data-go]").forEach(b => b.onclick = () => show(b.dataset.go));
$("theme").onclick = () => { const d = document.documentElement; d.dataset.t = d.dataset.t === "dark" ? "light" : "dark"; };

async function refresh() {
  try {
    const s = await (await api("/status")).json();
    const t = `AI provider: ${s.ai ? "✅ configured" : "❌ not configured"}\nVoice provider: ${s.voice_provider ? "✅ connected" : "❌ not configured"}\nYour voice: ${s.voice_ready ? "✅ created (listen to a preview before trusting it)" : "⚠️ setup required"}\nFFmpeg: ${s.ffmpeg ? "✅" : "❌ missing"}\nManim: ${s.manim ? "✅ available" : "➖ not installed (simple renderer used)"}`;
    $("st").innerText = t; $("vst").innerText = t;
  } catch (e) { $("st").textContent = e.message; $("vst").textContent = e.message; }
}

$("gen").onclick = async () => {
  say("msg1", "Generating script… (uses AI credit)");
  try {
    const topic = `${$("topic").value} [Area: ${$("area").value}]`;
    const d = await (await api("/script", json({ topic, level: $("level").value, objective: $("obj").value, minutes: +$("min").value,
      difficulty: $("diff").value, style: $("style").value, language: $("lang").value }))).json();
    S.title = d.title; S.scenes = d.scenes; S.approved = false; drawScenes(); say("msg1", "Done. Review it in Script."); show("script");
  } catch (e) { say("msg1", e.message, 1); }
};

$("jload").onclick = () => {
  try { const d = JSON.parse($("jin").value); if (!Array.isArray(d.scenes) || !d.scenes.length) throw 0;
    S.title = d.title || "Lesson"; S.scenes = d.scenes.map(x => ({ title: x.title || "", math: x.math || [], narration: x.narration || "", checks: x.checks || [], kind: x.kind || "steps", visual: x.visual || {} }));
    S.approved = false; drawScenes(); show("script"); } catch { say("msg1", "That is not a valid lesson JSON.", 1); }
};
function drawScenes() {
  const c = $("scenes"); c.innerHTML = `<label>Lesson title<input id="ltitle" value=""></label>`; $("ltitle").value = S.title;
  S.scenes.forEach((s, i) => {
    const d = document.createElement("div"); d.className = "sc";
    d.innerHTML = `<b>Scene ${i + 1}</b> <button data-del="${i}">Delete</button><label>Title<input class="t"></label>
      <label>On-screen math (one line each)<textarea class="m" rows="3"></textarea></label>
      <label>Narration<textarea class="n" rows="5"></textarea></label><label>Checks (lhs == rhs)<textarea class="k" rows="2"></textarea></label>\n      <label>Visual<select class="kd"><option value="steps">Steps (text only)</option><option value="graph">Graph</option><option value="numberline">Number line</option><option value="geometry">Geometry</option></select></label>\n      <label>Visual settings (JSON, Manim only)<textarea class="vj" rows="3"></textarea></label>`;
    d.querySelector(".t").value = s.title; d.querySelector(".m").value = (s.math || []).join("\n");
    d.querySelector(".n").value = s.narration; d.querySelector(".k").value = (s.checks || []).join("\n");
    d.querySelector(".kd").value = s.kind || "steps"; d.querySelector(".vj").value = s.visual && Object.keys(s.visual).length ? JSON.stringify(s.visual) : "";
    d.querySelector("[data-del]").onclick = () => { collect(); S.scenes.splice(i, 1); drawScenes(); };
    c.appendChild(d);
  });
}
function pj(t) { try { return t.trim() ? JSON.parse(t) : {}; } catch { say("msg2", "A visual settings box has invalid JSON and was ignored.", 1); return {}; } }
function collect() {
  if (!$("ltitle")) return; S.title = $("ltitle").value; S.approved = false;
  const lines = v => v.split("\n").map(x => x.trim()).filter(Boolean);
  S.scenes = [...document.querySelectorAll(".sc")].map(d => ({ title: d.querySelector(".t").value, math: lines(d.querySelector(".m").value),
    narration: d.querySelector(".n").value, checks: lines(d.querySelector(".k").value), kind: d.querySelector(".kd").value, visual: pj(d.querySelector(".vj").value) }));
}
$("addsc").onclick = () => { collect(); S.scenes.push({ title: "New scene", math: [], narration: "", checks: [] }); drawScenes(); };
$("check").onclick = async () => {
  collect();
  try {
    const d = await (await api("/verify", json({ scenes: S.scenes }))).json();
    $("checks").innerHTML = "<div class='card'>" + (d.results.map(r => `${r.result === "pass" ? "✅" : r.result === "fail" ? "❌" : "❔"} Scene ${r.scene + 1}: ${r.check}`).join("<br>") || "No checks listed.") + `<br><small>${d.note}</small></div>`;
  } catch (e) { say("msg2", e.message, 1); }
};
$("approve").onclick = () => {
  collect();
  if (!S.scenes.length || S.scenes.some(s => !s.narration.trim())) return say("msg2", "Every scene needs narration.", 1);
  if (!$("proofok").checked) return say("msg2", "Tick the manual-review box first.", 1);
  S.approved = true; say("msg2", "Approved. Set up voice and intro, then generate the video.");
};

$("vgo").onclick = async () => {
  const f = $("vfiles").files; if (!f.length) return say("msg3", "Choose recordings.", 1);
  const fd = new FormData(); fd.append("name", $("vname").value); fd.append("consent", $("consent").checked);
  [...f].forEach(x => fd.append("files", x));
  say("msg3", "Uploading…");
  try { const d = await (await api("/voice/clone", { method: "POST", body: fd })).json(); say("msg3", d.message); refresh(); }
  catch (e) { say("msg3", e.message, 1); }
};

$("iscript").value = FULL;
$("ikind").onchange = () => $("iscript").value = $("ikind").value === "full" ? FULL : SHORT;
const tpls = () => JSON.parse(localStorage.getItem("tpl") || "[]");
function drawTpl() { $("itpl").innerHTML = "<option value=''>Saved templates…</option>" + tpls().map((t, i) => `<option value="${i}">${t.name}</option>`).join(""); }
$("isave").onclick = () => { const n = prompt("Template name?"); if (!n) return; const a = tpls(); a.push({ name: n, script: $("iscript").value, pname: $("iname").value, ptitle: $("ititle").value }); localStorage.setItem("tpl", JSON.stringify(a)); drawTpl(); };
$("itpl").onchange = () => { const t = tpls()[$("itpl").value]; if (t) { $("iscript").value = t.script; $("iname").value = t.pname; $("ititle").value = t.ptitle; } };
drawTpl();
const intro = () => ({ enabled: $("ien").checked, name: $("iname").value, title: $("ititle").value, script: $("iscript").value });
$("iprev").onclick = async () => {
  say("msg4", "Generating (cached if unchanged)…");
  try { const b = await (await api("/intro", json(intro()))).blob(); const a = $("iaud"); a.src = URL.createObjectURL(b); a.hidden = false; a.play(); say("msg4", "Listen: is this your voice?"); }
  catch (e) { say("msg4", e.message, 1); }
};

function estimate() {
  const ch = S.scenes.reduce((n, s) => n + s.narration.length, 0) + ($("ien").checked ? $("iscript").value.length : 0);
  $("est").textContent = `Narration ≈ ${ch} characters (~${Math.round(ch / 900)} min of audio). Voice cost depends on your provider plan; unchanged text is reused from cache and not billed again.`;
}
$("render").onclick = async () => {
  if (!$("ltitle")) return say("msg5", "Create a lesson first.", 1);
  if (!S.approved) return say("msg5", "Approve the script first.", 1);
  estimate(); if (!confirm("Generating narration and rendering uses voice credit. Continue?")) return;
  say("msg5", "Starting…"); $("prog").hidden = false;
  try {
    const { job } = await (await api("/render", json({ title: S.title, scenes: S.scenes, intro: intro(), approved: true, orientation: $("orient").value, engine: $("engine").value,
      voice: { stability: .5, similarity: .8, speed: +$("speed").value } }))).json();
    for (;;) {
      await new Promise(r => setTimeout(r, 2500));
      const j = await (await api("/jobs/" + job)).json(); $("prog").value = j.progress; say("msg5", j.message, j.state === "error");
      if (j.state === "error") return;
      if (j.state === "done") { const b = await (await api("/videos/" + job)).blob(), u = URL.createObjectURL(b);
        $("player").src = u; $("player").hidden = false; $("dl").href = u; $("dl").hidden = false; return; }
    }
  } catch (e) { say("msg5", e.message, 1); }
};

$("api").value = API || "(set in config.js)"; $("tok").value = tok();
$("savetok").onclick = () => { sessionStorage.setItem("tok", $("tok").value); refresh(); };
show("dash");

const boot = window.WRITERS_ROOM_BOOT || { modes: {}, defaultMode: "dnd" };
const modeCatalog = boot.modes || {};
const modePresets = {
  dnd: {
    prompt: "A cursed roller disco opens one last time beneath the city cemetery.",
    notes:
      "Keep it spooky, fast, and playable. Give the party concrete tactical choices, physical space to exploit, and one memorable reveal per round.",
  },
  horror: {
    prompt: "The night janitor finds fresh muddy footprints in a locked ballroom no one has opened since the fire.",
    notes:
      "Aim for sensory dread and escalation. Keep the prose specific, grounded, and unnervingly patient.",
  },
  fantasy: {
    prompt: "A city built around a sleeping dragon wakes to find its dreams leaking into the streets.",
    notes:
      "Lean into wonder, consequence, and coherent magic. Give the room a strong mythic image to chase.",
  },
  literary: {
    prompt: "Two estranged siblings catalog their late mother's house and keep discovering evidence of a life she never confessed.",
    notes:
      "Favor interiority, restraint, and loaded detail. Let every turn sharpen character before plot.",
  },
  noir: {
    prompt: "A private investigator takes a missing-person job that arrives with tomorrow's newspaper already folded to the obituary page.",
    notes:
      "Work the shadows, bad choices, and quiet menace. Make every clue feel expensive.",
  },
  "sci-fi": {
    prompt: "A lunar emergency operator starts receiving distress calls from a colony that was declared empty twelve years ago.",
    notes:
      "Balance the speculative idea with human stakes. Let the room keep the science weird but emotionally legible.",
  },
  comedy: {
    prompt: "A small-town council accidentally elects an eldritch crab as interim mayor and has to keep the budget meeting on track.",
    notes:
      "Prioritize timing, escalation, and callbacks. Let the absurdity stay disciplined enough to land.",
  },
};

let socket = null;
let sessionActive = false;
let audioQueue = [];
let isPlayingAudio = false;
let reconnectTimer = null;
let reconnectAttempts = 0;
let voiceAvailable = true;
let currentMode = boot.defaultMode || "dnd";
let currentSessionId = window.localStorage.getItem("writers-room.session-id") || "";
let connectedSessionId = "";
let skipNextCloseReconnect = false;
const MAX_RECONNECT_DELAY_MS = 5000;
const SESSION_ID_STORAGE_KEY = "writers-room.session-id";
const LAST_EVENT_ID_PREFIX = "writers-room.last-event-id";

function currentModeInfo() {
  return modeCatalog[currentMode] || modeCatalog.horror || {};
}

function eventCursorKey(sessionId) {
  return `${LAST_EVENT_ID_PREFIX}:${sessionId}`;
}

function setCurrentSessionId(sessionId) {
  currentSessionId = sessionId || "";
  if (currentSessionId) {
    window.localStorage.setItem(SESSION_ID_STORAGE_KEY, currentSessionId);
    return;
  }
  window.localStorage.removeItem(SESSION_ID_STORAGE_KEY);
}

function clearLastEventId(sessionId = currentSessionId) {
  if (!sessionId) {
    return;
  }
  window.localStorage.removeItem(eventCursorKey(sessionId));
}

function getLastEventId(sessionId = currentSessionId) {
  if (!sessionId) {
    return null;
  }
  const rawValue = window.localStorage.getItem(eventCursorKey(sessionId));
  if (!rawValue) {
    return null;
  }
  const parsed = parseInt(rawValue, 10);
  return Number.isNaN(parsed) ? null : parsed;
}

function rememberLastEventId(eventId, sessionId = currentSessionId) {
  if (!sessionId || !Number.isInteger(eventId)) {
    return;
  }
  const current = getLastEventId(sessionId);
  if (current !== null && eventId <= current) {
    return;
  }
  window.localStorage.setItem(eventCursorKey(sessionId), String(eventId));
}

function sessionAwarePath(path, sessionId = currentSessionId) {
  if (!sessionId) {
    return path;
  }
  const url = new URL(path, window.location.origin);
  url.searchParams.set("session_id", sessionId);
  return `${url.pathname}${url.search}`;
}

function reconnectSocket() {
  if (!currentSessionId) {
    return;
  }

  if (socket) {
    skipNextCloseReconnect = true;
    socket.close();
    return;
  }

  initSocket();
}

function initSocket() {
  if (!currentSessionId) {
    return;
  }

  if (
    socket &&
    (socket.readyState === WebSocket.OPEN ||
      socket.readyState === WebSocket.CONNECTING)
  ) {
    return;
  }

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socketUrl = new URL(`${protocol}://${window.location.host}/ws`);
  socketUrl.searchParams.set("session_id", currentSessionId);
  const lastEventId = getLastEventId();
  if (lastEventId !== null) {
    socketUrl.searchParams.set("last_event_id", String(lastEventId));
  }
  socket = new WebSocket(socketUrl.toString());
  connectedSessionId = currentSessionId;

  socket.addEventListener("open", () => {
    reconnectAttempts = 0;
    if (reconnectTimer) {
      window.clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    if (sessionActive) {
      updateStatusBanner(true, "Session live", "Connection restored. Waiting for fresh beats.");
    }
    rehydrateSessionState();
  });

  socket.addEventListener("message", (event) => {
    try {
      const message = JSON.parse(event.data);
      if (message && message.session_id && message.session_id !== currentSessionId) {
        return;
      }
      if (message && message.session_id && !currentSessionId) {
        setCurrentSessionId(message.session_id);
      }
      if (message && Number.isInteger(message.event_id)) {
        rememberLastEventId(message.event_id, message.session_id || currentSessionId);
      }
      if (message && message.event) {
        handleEvent(message.event, message.data || {});
      }
    } catch (error) {
      console.error("WebSocket message parse failed:", error);
    }
  });

  socket.addEventListener("close", () => {
    const shouldSkipReconnect = skipNextCloseReconnect;
    skipNextCloseReconnect = false;
    socket = null;
    connectedSessionId = "";
    if (shouldSkipReconnect) {
      initSocket();
      return;
    }
    scheduleReconnect();
  });
  socket.addEventListener("error", (error) => {
    console.error("WebSocket error:", error);
  });
}

function scheduleReconnect() {
  if (!currentSessionId) {
    return;
  }

  if (reconnectTimer) {
    return;
  }

  const delay = Math.min(1000 * 2 ** reconnectAttempts, MAX_RECONNECT_DELAY_MS);
  reconnectAttempts += 1;

  if (sessionActive) {
    updateStatusBanner(
      true,
      "Connection dropped",
      `Reconnecting in ${Math.round(delay / 1000)}s...`,
    );
  }

  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null;
    initSocket();
  }, delay);
}

function showSessionNote(message, links = []) {
  const note = document.getElementById("session-note");
  if (!note) {
    return;
  }

  note.textContent = "";
  const messageNode = document.createElement("span");
  messageNode.textContent = message;
  note.appendChild(messageNode);

  const normalized = Array.isArray(links)
    ? links
    : links && links.href
      ? [links]
      : [];

  normalized
    .filter((entry) => entry && entry.href)
    .forEach((entry) => {
      note.appendChild(document.createTextNode(" "));
      const link = document.createElement("a");
      link.href = entry.href;
      link.textContent = entry.label || "Open";
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      note.appendChild(link);
    });

  note.classList.remove("hidden");
}

function buildArtifactLinks({ briefPath, finalDraftPath }) {
  const links = [];
  if (briefPath) {
    links.push({ href: sessionAwarePath("/briefs/latest"), label: "Open brief" });
  }
  if (finalDraftPath) {
    links.push({ href: sessionAwarePath("/drafts/latest"), label: "Open final draft" });
  }
  return links;
}

function artifactNoteMessage({ briefPath, finalDraftPath, transcriptPath }) {
  if (finalDraftPath && briefPath) {
    return "Session artifacts saved. Final draft ready.";
  }
  if (finalDraftPath) {
    return "Final draft saved. Brief rendering was skipped or failed.";
  }
  if (briefPath) {
    return "Session artifacts saved.";
  }
  if (transcriptPath) {
    return `Transcript saved to ${transcriptPath}`;
  }
  return "Session ended without saved artifacts.";
}

function clearSessionNote() {
  const note = document.getElementById("session-note");
  if (!note) {
    return;
  }
  note.textContent = "";
  note.classList.add("hidden");
}

function setStartButtonState(active) {
  const startBtn = document.getElementById("start-btn");
  if (!startBtn) {
    return;
  }

  startBtn.disabled = active;
  if (active) {
    startBtn.innerHTML = '<span class="spinner"></span> Launching...';
    return;
  }

  startBtn.textContent = currentMode === "dnd" ? "Launch the table" : "Start the room";
}

function normalizeAgentId(agentName) {
  return agentName
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function ensureAgentCard(agentName, color, specialty = "Agent") {
  const grid = document.getElementById("agent-grid");
  const emptyRoster = grid.querySelector(".empty-roster");
  if (emptyRoster) {
    grid.innerHTML = "";
  }
  const agentId = normalizeAgentId(agentName);
  let card = document.getElementById(`agent-${agentId}`);
  if (!card) {
    card = document.createElement("article");
    card.className = "agent-card";
    card.id = `agent-${agentId}`;

    const header = document.createElement("div");
    header.className = "agent-header";

    const identity = document.createElement("div");
    identity.className = "agent-identity";

    const nameEl = document.createElement("div");
    nameEl.className = "agent-name";
    nameEl.id = `name-${agentId}`;

    const specialtyEl = document.createElement("div");
    specialtyEl.className = "agent-specialty";
    specialtyEl.id = `specialty-${agentId}`;

    identity.appendChild(nameEl);
    identity.appendChild(specialtyEl);

    const status = document.createElement("div");
    status.className = "agent-status";
    status.id = `status-${agentId}`;
    status.textContent = "Waiting";

    header.appendChild(identity);
    header.appendChild(status);

    const responsesDiv = document.createElement("div");
    responsesDiv.className = "agent-responses";
    responsesDiv.id = `responses-${agentId}`;
    responsesDiv.innerHTML =
      '<p class="placeholder-text">This seat is ready when the session begins.</p>';

    card.appendChild(header);
    card.appendChild(responsesDiv);
    grid.appendChild(card);
  }

  const nameEl = document.getElementById(`name-${agentId}`);
  const specialtyEl = document.getElementById(`specialty-${agentId}`);
  const status = document.getElementById(`status-${agentId}`);
  const responsesDiv = document.getElementById(`responses-${agentId}`);

  nameEl.textContent = agentName;
  specialtyEl.textContent = specialty;
  if (color) {
    card.style.setProperty("--agent-accent", color);
    nameEl.style.color = color;
  }

  return { card, status, responsesDiv };
}

function renderRosterPlaceholder() {
  const grid = document.getElementById("agent-grid");
  if (!grid) {
    return;
  }
  grid.innerHTML = `
    <div class="empty-roster">
      <h3>The room is empty.</h3>
      <p>Launch a session to seat the DM, the players, or the author roster.</p>
    </div>
  `;
}

function applyAgentRoster(agentRoster) {
  if (!Array.isArray(agentRoster) || agentRoster.length === 0) {
    renderRosterPlaceholder();
    return;
  }

  const grid = document.getElementById("agent-grid");
  grid.innerHTML = "";

  agentRoster.forEach((entry) => {
    ensureAgentCard(entry.name, entry.color, entry.specialty || "Agent");
  });
}

function clearActivityFeed() {
  const feed = document.getElementById("activity-feed");
  if (!feed) {
    return;
  }
  feed.innerHTML = `
    <div class="empty-state">
      <h3>Nothing rolling yet.</h3>
      <p>When the room starts, scene beats, player actions, and verdicts will stack here live.</p>
    </div>
  `;
}

function appendFeedEntry(kind, title, body, meta = "") {
  const feed = document.getElementById("activity-feed");
  if (!feed) {
    return;
  }

  const emptyState = feed.querySelector(".empty-state");
  if (emptyState) {
    feed.innerHTML = "";
  }

  const item = document.createElement("article");
  item.className = `feed-item feed-item--${kind}`;

  const itemTitle = document.createElement("h3");
  itemTitle.textContent = title;

  const itemBody = document.createElement("p");
  itemBody.textContent = body;

  item.appendChild(itemTitle);
  item.appendChild(itemBody);

  if (meta) {
    const itemMeta = document.createElement("div");
    itemMeta.className = "feed-meta";
    itemMeta.textContent = meta;
    item.appendChild(itemMeta);
  }

  feed.prepend(item);
}

function updateStatusBanner(active, title = "", detail = "") {
  const banner = document.getElementById("status-banner");
  const titleEl = document.getElementById("status-title");
  const detailEl = document.getElementById("status-detail");

  if (!banner || !titleEl || !detailEl) {
    return;
  }

  if (active) {
    banner.classList.add("active");
    titleEl.textContent = title || "Session live";
    detailEl.textContent = detail || "The room is working.";
    return;
  }

  banner.classList.remove("active");
  titleEl.textContent = "Studio idle";
  detailEl.textContent = "Choose a mode, frame the premise, and launch the room.";
}

function syncProducerControls() {
  const producerEnabled = document.getElementById("producer-enabled");
  const fireWorst = document.getElementById("fire-worst");

  if (!producerEnabled || !fireWorst) {
    return;
  }

  if (producerEnabled.disabled || !producerEnabled.checked) {
    fireWorst.checked = false;
    fireWorst.disabled = true;
  } else {
    fireWorst.disabled = false;
  }
}

function applyModeCopy() {
  const info = currentModeInfo();
  const promptLabel = document.getElementById("prompt-label");
  const notesLabel = document.getElementById("notes-label");
  const prompt = document.getElementById("prompt");
  const notes = document.getElementById("notes");
  const loadExampleBtn = document.getElementById("load-example-btn");

  document.getElementById("mode-brief-title").textContent = info.name || "Mode";
  document.getElementById("mode-brief-description").textContent =
    info.description || "";
  document.getElementById("mode-brief-atmosphere").textContent =
    info.atmosphere || "";
  document.getElementById("mode-brief-pacing").textContent = info.pacing || "";
  document.getElementById("mode-brief-criteria").textContent =
    info.producer_criteria || "";

  document.getElementById("feed-title").textContent =
    currentMode === "dnd" ? "Encounter Reel" : "Draft Reel";
  document.getElementById("feed-subtitle").textContent =
    currentMode === "dnd"
      ? "Scene framing, party declarations, and fallout stack here in order."
      : "Each contribution lands here so you can track momentum without losing the room.";
  document.getElementById("roster-title").textContent =
    currentMode === "dnd" ? "Seats at the Table" : "Seats in the Room";
  document.getElementById("roster-subtitle").textContent =
    currentMode === "dnd"
      ? "DM and party roles appear here once the session launches."
      : "Each writer keeps an individual lane so you can see who is building and who is stalling.";
  document.getElementById("state-heading").textContent =
    currentMode === "dnd" ? "Encounter Pressure" : "Center Table State";
  document.getElementById("state-subtitle").textContent =
    currentMode === "dnd"
      ? "What the table knows, how hot the scene is, and what pressure is still live."
      : "Shared pressure, pace, and the next thing the story still needs.";

  if (currentMode === "dnd") {
    promptLabel.textContent = "Adventure hook";
    notesLabel.textContent = "Table brief";
    prompt.placeholder =
      "A haunted roller disco opens one last time beneath the city cemetery.";
    notes.placeholder =
      "Desired vibe, encounter rules, set pieces, monsters, or the kind of choices the party should face.";
    loadExampleBtn.textContent = "Load an adventure spark";
  } else {
    promptLabel.textContent = "Core premise";
    notesLabel.textContent = "Creative brief";
    prompt.placeholder =
      "A locked room, a bad secret, and the one person who knows why the lights keep going out.";
    notes.placeholder =
      "Voice, constraints, emotional target, craft goals, or what the Producer should be ruthless about.";
    loadExampleBtn.textContent = "Load a writing spark";
  }
}

function updateModeSelection(mode) {
  currentMode = modeCatalog[mode] ? mode : boot.defaultMode || "dnd";

  document.getElementById("mode").value = currentMode;

  document.querySelectorAll(".mode-card").forEach((card) => {
    card.classList.toggle("is-active", card.dataset.mode === currentMode);
  });

  const producerEnabled = document.getElementById("producer-enabled");
  const includeCustomAgents = document.getElementById("include-custom-agents");
  const produceFinalDraft = document.getElementById("produce-final-draft");
  const producerNote = document.getElementById("producer-note");
  const customAgentNote = document.getElementById("custom-agent-note");
  const finalDraftNote = document.getElementById("final-draft-note");

  if (currentMode === "dnd") {
    producerEnabled.checked = false;
    producerEnabled.disabled = true;
    includeCustomAgents.checked = false;
    includeCustomAgents.disabled = true;
    if (produceFinalDraft) {
      produceFinalDraft.checked = false;
      produceFinalDraft.disabled = true;
    }
    producerNote.textContent =
      "D&D mode runs without the Producer. The DM and party own the pressure without an external judge.";
    customAgentNote.textContent =
      "D&D mode keeps the table coherent: one DM, one fixed party, no drop-in custom seats.";
    if (finalDraftNote) {
      finalDraftNote.textContent =
        "D&D mode doesn't produce a synthesized short story. The transcript and encounter log are the artifact.";
    }
  } else {
    producerEnabled.disabled = false;
    includeCustomAgents.disabled = false;
    if (produceFinalDraft) {
      produceFinalDraft.disabled = false;
    }
    producerNote.textContent =
      "Producer scoring stays on for fiction rooms where critique sharpens the draft.";
    customAgentNote.textContent =
      "Custom agents can join non-D&D rooms if you want a line editor, lore fiend, or continuity cop in the mix.";
    if (finalDraftNote) {
      finalDraftNote.textContent =
        "After the last round, the Editor runs a two-pass synthesis (structural then line) and saves a publishable short story alongside the brief. Adds time and tokens.";
    }
  }

  applyModeCopy();
  syncProducerControls();
  setStartButtonState(sessionActive);
}

function updateStoryStatePanel(state) {
  if (!state) {
    return;
  }

  document.getElementById("story-state-panel").classList.remove("hidden");
  document.getElementById("state-mode").textContent = state.mode
    ? state.mode.toUpperCase()
    : "-";

  const actNames = { 1: "SETUP", 2: "CONFRONTATION", 3: "RESOLUTION" };
  document.getElementById("state-act").textContent =
    actNames[state.current_act] || state.current_act || "-";

  const tension = state.tension_level || 3;
  document.getElementById("state-tension").textContent = `${tension}/10`;
  document.getElementById("tension-fill").style.width = `${tension * 10}%`;

  const tensionFill = document.getElementById("tension-fill");
  if (tension <= 3) {
    tensionFill.style.background = "var(--success)";
  } else if (tension <= 6) {
    tensionFill.style.background = "var(--warning)";
  } else {
    tensionFill.style.background = "var(--error)";
  }

  document.getElementById("state-pacing").textContent =
    state.pacing || "steady";
  document.getElementById("state-words").textContent = state.word_count || 0;

  const needsRow = document.getElementById("state-needs-row");
  const needsLabel = document.getElementById("state-needs-label");
  const needsValue = document.getElementById("state-needs");
  if (state.mode === "dnd") {
    needsRow.classList.add("hidden");
  } else {
    needsRow.classList.remove("hidden");
    needsLabel.textContent = "Story need";
    const needs =
      Array.isArray(state.story_needs) && state.story_needs.length
        ? state.story_needs[0]
        : "Keep building momentum.";
    needsValue.textContent = needs;
  }
}

function updateLeaderboard(leaderboard) {
  const leaderboardDiv = document.getElementById("leaderboard");
  const leaderboardList = document.getElementById("leaderboard-list");

  if (!leaderboard || leaderboard.length === 0) {
    leaderboardDiv.classList.add("hidden");
    leaderboardList.innerHTML = "";
    return;
  }

  leaderboardDiv.classList.remove("hidden");
  leaderboardList.innerHTML = "";
  const medals = ["1st", "2nd", "3rd"];

  leaderboard.forEach((item, index) => {
    const li = document.createElement("li");
    li.className = "leaderboard-item";

    const rank = document.createElement("span");
    rank.className = "leaderboard-rank";
    rank.textContent = index < 3 ? medals[index] : `${index + 1}th`;

    const name = document.createElement("span");
    name.className = "leaderboard-name";
    name.textContent = item.name;

    const score = document.createElement("span");
    score.className = "leaderboard-score";
    score.textContent = `${item.average}/10`;

    const history = document.createElement("span");
    history.className = "leaderboard-history";
    history.textContent = item.scores.join(", ");

    li.appendChild(rank);
    li.appendChild(name);
    li.appendChild(score);
    li.appendChild(history);
    leaderboardList.appendChild(li);
  });
}

function showWinner(winner) {
  const banner = document.getElementById("winner-banner");
  document.getElementById("winner-name").textContent = winner.name;
  document.getElementById("winner-score").textContent = `${winner.average}/10 average`;
  banner.classList.remove("hidden");
}

function showFired(worst) {
  const banner = document.getElementById("fired-banner");
  document.getElementById("fired-name").textContent = worst.name;
  document.getElementById("fired-score").textContent = `${worst.average}/10 average`;
  banner.classList.remove("hidden");
}

const ARTIFACT_LINK_SPECS = [
  {
    key: "finalDraftPath",
    href: "/drafts/latest",
    label: "Final draft",
    hint: "markdown",
  },
  {
    key: "pipelineDir",
    href: "/pipelines/latest",
    label: "Pipeline index",
    hint: "markdown",
  },
  {
    key: "briefPath",
    href: "/briefs/latest",
    label: "Session brief",
    hint: "html",
  },
  {
    key: "transcriptPath",
    href: "/transcripts/latest",
    label: "Transcript",
    hint: "text",
  },
];

function updateArtifactLinks(state) {
  const panel = document.getElementById("artifact-links");
  const list = document.getElementById("artifact-links-list");
  if (!panel || !list) {
    return;
  }

  list.textContent = "";
  const entries = ARTIFACT_LINK_SPECS.filter((spec) => Boolean(state[spec.key]));

  if (entries.length === 0) {
    panel.classList.add("hidden");
    return;
  }

  entries.forEach((spec) => {
    const li = document.createElement("li");
    const link = document.createElement("a");
    link.href = sessionAwarePath(spec.href);
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.title = state[spec.key];

    const label = document.createElement("span");
    label.className = "artifact-links__label";
    label.textContent = spec.label;
    link.appendChild(label);

    const hint = document.createElement("span");
    hint.className = "artifact-links__hint";
    hint.textContent = spec.hint;
    link.appendChild(hint);

    li.appendChild(link);
    list.appendChild(li);
  });

  panel.classList.remove("hidden");
}

function clearArtifactLinks() {
  const panel = document.getElementById("artifact-links");
  const list = document.getElementById("artifact-links-list");
  if (list) {
    list.textContent = "";
  }
  if (panel) {
    panel.classList.add("hidden");
  }
}

function queueAudio(audioPayload) {
  if (!audioPayload) {
    return;
  }
  audioQueue.push(audioPayload);
  playNextAudio();
}

function playNextAudio() {
  if (isPlayingAudio || audioQueue.length === 0) {
    return;
  }

  isPlayingAudio = true;
  const audioPayload = audioQueue.shift();
  const audioData =
    typeof audioPayload === "string" ? audioPayload : audioPayload.data;
  const audioMime =
    typeof audioPayload === "string"
      ? "audio/mpeg"
      : audioPayload.mime || "audio/mpeg";

  if (!audioData) {
    isPlayingAudio = false;
    playNextAudio();
    return;
  }

  const audioPlayer = document.getElementById("audio-player");
  audioPlayer.src = `data:${audioMime};base64,${audioData}`;
  audioPlayer.onended = () => {
    isPlayingAudio = false;
    playNextAudio();
  };
  audioPlayer.onerror = () => {
    isPlayingAudio = false;
    playNextAudio();
  };

  audioPlayer.play().catch((error) => {
    console.error("Audio playback failed:", error);
    isPlayingAudio = false;
    playNextAudio();
  });
}

function clearPreviousSession() {
  audioQueue = [];
  isPlayingAudio = false;
  clearSessionNote();
  clearActivityFeed();
  hideContinueControls();
  renderRosterPlaceholder();
  document.getElementById("leaderboard").classList.add("hidden");
  document.getElementById("leaderboard-list").innerHTML = "";
  document.getElementById("winner-banner").classList.add("hidden");
  document.getElementById("fired-banner").classList.add("hidden");
  document.getElementById("story-state-panel").classList.add("hidden");
  clearArtifactLinks();
}

function handleEvent(eventName, data) {
  switch (eventName) {
    case "connected":
      if (data.session_id && data.session_id !== currentSessionId) {
        setCurrentSessionId(data.session_id);
      }
      break;
    case "session_started":
      sessionActive = true;
      clearSessionNote();
      clearActivityFeed();
      updateModeSelection(data.mode || currentMode);
      applyAgentRoster(data.agent_roster || []);
      updateStatusBanner(
        true,
        currentMode === "dnd" ? "Table live" : "Room live",
        `Round 1 of ${data.rounds} is loading.`,
      );
      appendFeedEntry(
        "system",
        currentMode === "dnd" ? "Adventure launched" : "Session launched",
        data.prompt || "The room is up.",
        currentModeInfo().name || currentMode,
      );
      break;
    case "story_state_update":
      updateStoryStatePanel(data.state);
      break;
    case "round_started":
      updateStatusBanner(
        true,
        currentMode === "dnd" ? "Table live" : "Room live",
        `Round ${data.round} of ${data.total}.`,
      );
      appendFeedEntry(
        "round",
        `Round ${data.round}`,
        currentMode === "dnd"
          ? "Fresh pressure hits the table."
          : "The room leans into the next drafting beat.",
      );
      break;
    case "agent_thinking": {
      const { card, status } = ensureAgentCard(data.agent, data.color, "Agent");
      card.classList.add("thinking");
      status.innerHTML = '<span class="spinner"></span> Thinking';
      break;
    }
    case "agent_response": {
      const { card, status, responsesDiv } = ensureAgentCard(
        data.agent,
        data.color,
        "Agent",
      );

      card.classList.remove("thinking");
      status.textContent = `Round ${data.round}`;

      const placeholder = responsesDiv.querySelector(".placeholder-text");
      if (placeholder) {
        responsesDiv.innerHTML = "";
      }

      const responseItem = document.createElement("div");
      responseItem.className = "response-item";

      const roundLabel = document.createElement("div");
      roundLabel.className = "response-round";
      roundLabel.textContent = `Round ${data.round}`;

      const responseText = document.createElement("div");
      responseText.className = "response-text";
      responseText.textContent = data.response;

      responseItem.appendChild(roundLabel);
      responseItem.appendChild(responseText);
      responsesDiv.appendChild(responseItem);
      responsesDiv.scrollTop = responsesDiv.scrollHeight;

      appendFeedEntry("turn", data.agent, data.response, `Round ${data.round}`);

      if (data.audio) {
        queueAudio({ data: data.audio, mime: data.audio_mime });
      }
      break;
    }
    case "editor_thinking": {
      const stage = data.stage || "structural";
      const title =
        stage === "structural"
          ? "Editor drafting structure..."
          : "Editor polishing prose...";
      updateStatusBanner(
        true,
        title,
        stage === "structural"
          ? "The Structural Editor is synthesizing the transcript into a cohesive draft."
          : "The Line Editor is polishing the structural draft.",
      );
      appendFeedEntry(
        "system",
        title,
        stage === "structural"
          ? "Pass 1: merging scenes, fixing continuity, resolving threads."
          : "Pass 2: tightening prose, trimming filler, preserving voices.",
      );
      break;
    }
    case "editor_response": {
      const stage = data.stage || "structural";
      const label =
        stage === "structural" ? "Structural pass complete" : "Line pass complete";
      const preview = (data.preview || "").trim();
      const length = data.length || 0;
      appendFeedEntry(
        "turn",
        label,
        preview ? preview + (length > preview.length ? "..." : "") : "(no preview)",
        length ? `${length} characters` : "",
      );
      break;
    }
    case "producer_thinking": {
      const { card, status } = ensureAgentCard(
        "The Producer",
        "#98C379",
        "Quality control",
      );
      card.classList.add("thinking");
      status.innerHTML = '<span class="spinner"></span> Judging';
      updateStatusBanner(true, "Producer evaluating", `Round ${data.round} is under review.`);
      break;
    }
    case "producer_verdict": {
      const { card, status, responsesDiv } = ensureAgentCard(
        "The Producer",
        "#98C379",
        "Quality control",
      );
      card.classList.remove("thinking");
      status.textContent = `Round ${data.round}`;

      const placeholder = responsesDiv.querySelector(".placeholder-text");
      if (placeholder) {
        responsesDiv.innerHTML = "";
      }

      const responseItem = document.createElement("div");
      responseItem.className = "response-item producer-response";

      const roundLabel = document.createElement("div");
      roundLabel.className = "response-round";
      roundLabel.textContent = `Round ${data.round} verdict`;

      const responseText = document.createElement("div");
      responseText.className = "response-text";
      responseText.textContent = data.response;

      responseItem.appendChild(roundLabel);
      responseItem.appendChild(responseText);
      responsesDiv.appendChild(responseItem);

      updateLeaderboard(data.leaderboard);
      appendFeedEntry("verdict", "Producer", data.response, `Round ${data.round}`);

      if (data.audio) {
        queueAudio({ data: data.audio, mime: data.audio_mime });
      }
      break;
    }
    case "session_resumed":
      sessionActive = true;
      setStartButtonState(true);
      hideContinueControls();
      updateStatusBanner(
        true,
        currentMode === "dnd" ? "Table live" : "Room live",
        `Continuing from round ${data.starting_round} (+${data.additional_rounds} rounds).`,
      );
      appendFeedEntry(
        "system",
        currentMode === "dnd" ? "Adventure continues" : "Session continues",
        `Adding ${data.additional_rounds} more round${data.additional_rounds > 1 ? "s" : ""} to the session.`,
      );
      break;
    case "session_completed":
      sessionActive = false;
      updateStatusBanner(
        false,
        "",
        "",
      );
      setStartButtonState(false);
      if (data.story_state) {
        updateStoryStatePanel(data.story_state);
      }
      if (data.leaderboard) {
        updateLeaderboard(data.leaderboard);
      }
      if (data.winner) {
        showWinner(data.winner);
      }
      if (data.worst) {
        showFired(data.worst);
      }
      {
        const artifactState = {
          briefPath: data.brief_path,
          finalDraftPath: data.final_draft_path,
          transcriptPath: data.transcript_path,
          pipelineDir: data.pipeline_dir,
        };
        updateArtifactLinks(artifactState);
        const links = buildArtifactLinks(artifactState);
        if (links.length || data.transcript_path) {
          showSessionNote(artifactNoteMessage(artifactState), links);
        }
      }
      appendFeedEntry(
        "system",
        "Session complete",
        currentMode === "dnd"
          ? "The table wrapped and the artifacts are ready."
          : "The room wrapped and the draft artifacts are ready.",
      );
      showContinueControls();
      break;
    case "error":
      sessionActive = false;
      setStartButtonState(false);
      updateStatusBanner(false);
      showSessionNote(`Session error: ${data.message}`);
      appendFeedEntry("error", "Session error", data.message || "Unknown error.");
      break;
    default:
      console.log("Unhandled event:", eventName, data);
  }
}

async function rehydrateSessionState() {
  try {
    const response = await fetch(sessionAwarePath("/api/status"));
    if (!response.ok) {
      throw new Error(`Status request failed with ${response.status}`);
    }

    const status = await response.json();
    if (status.session_id) {
      setCurrentSessionId(status.session_id);
    } else if (
      !status.active &&
      !status.last_transcript &&
      !status.last_brief &&
      !status.last_final_draft &&
      !status.last_pipeline_dir
    ) {
      setCurrentSessionId("");
    }
    sessionActive = Boolean(status.active);

    if (status.config && status.config.mode) {
      updateModeSelection(status.config.mode);
    } else {
      updateModeSelection(currentMode);
    }

    if (sessionActive) {
      setStartButtonState(true);
      updateStatusBanner(
        true,
        currentMode === "dnd" ? "Table live" : "Room live",
        "Session in progress. Waiting for live updates...",
      );
      applyAgentRoster(status.agent_roster || []);
      if (status.story_state) {
        updateStoryStatePanel(status.story_state);
      }
      if (currentSessionId && connectedSessionId !== currentSessionId) {
        reconnectSocket();
      }
      return;
    }

    setStartButtonState(false);
    updateStatusBanner(false);

    {
      const artifactState = {
        briefPath: status.last_brief,
        finalDraftPath: status.last_final_draft,
        transcriptPath: status.last_transcript,
        pipelineDir: status.last_pipeline_dir,
      };
      updateArtifactLinks(artifactState);
      const links = buildArtifactLinks(artifactState);
      if (links.length || status.last_transcript) {
        showSessionNote(artifactNoteMessage(artifactState), links);
      } else {
        clearSessionNote();
      }
    }

    if (currentSessionId && connectedSessionId !== currentSessionId) {
      reconnectSocket();
    }
  } catch (error) {
    console.error("Failed to rehydrate session state:", error);
  }
}

async function startSession() {
  if (sessionActive) {
    return;
  }

  const prompt = document.getElementById("prompt").value.trim();
  const notes = document.getElementById("notes").value.trim();
  const rounds = parseInt(document.getElementById("rounds").value, 10);
  const temperature = parseFloat(document.getElementById("temperature").value);
  const producerEnabled = document.getElementById("producer-enabled").checked;
  const fireWorst = document.getElementById("fire-worst").checked;
  const voiceEnabled = document.getElementById("voice-enabled").checked;
  const includeCustomAgents = document.getElementById(
    "include-custom-agents",
  ).checked;
  const produceFinalDraftEl = document.getElementById("produce-final-draft");
  const produceFinalDraft = produceFinalDraftEl
    ? produceFinalDraftEl.checked
    : false;

  if (!prompt) {
    showSessionNote("Give the room a premise before you launch it.");
    return;
  }

  if (Number.isNaN(rounds) || rounds < 1 || rounds > 10) {
    showSessionNote("Rounds must be between 1 and 10.");
    return;
  }

  clearPreviousSession();
  setStartButtonState(true);

  try {
    const response = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        notes,
        mode: currentMode,
        rounds,
        temperature,
        producer_enabled: producerEnabled,
        fire_worst: fireWorst,
        voice_enabled: voiceEnabled,
        include_custom_agents: includeCustomAgents,
        produce_final_draft: produceFinalDraft,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Failed to start session");
    }
    if (data.session_id) {
      setCurrentSessionId(data.session_id);
      clearLastEventId(data.session_id);
      reconnectSocket();
    }
  } catch (error) {
    console.error("Failed to start session:", error);
    setStartButtonState(false);
    showSessionNote(`Failed to start session: ${error.message}`);
  }
}

function showContinueControls() {
  const wrap = document.getElementById("continue-controls");
  if (wrap) {
    wrap.classList.remove("hidden");
  }
}

function hideContinueControls() {
  const wrap = document.getElementById("continue-controls");
  if (wrap) {
    wrap.classList.add("hidden");
  }
}

async function continueSession() {
  if (sessionActive) {
    return;
  }

  if (!currentSessionId) {
    showSessionNote("There isn't a resumable session selected.");
    return;
  }

  const roundsInput = document.getElementById("continue-rounds");
  const rounds = roundsInput ? parseInt(roundsInput.value, 10) : 3;

  if (Number.isNaN(rounds) || rounds < 1 || rounds > 10) {
    showSessionNote("Additional rounds must be between 1 and 10.");
    return;
  }

  hideContinueControls();
  setStartButtonState(true);

  try {
    const response = await fetch("/api/continue", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: currentSessionId, rounds }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Failed to continue session");
    }
  } catch (error) {
    console.error("Failed to continue session:", error);
    setStartButtonState(false);
    showContinueControls();
    showSessionNote(`Failed to continue session: ${error.message}`);
  }
}

function loadExamplePrompt() {
  const preset = modePresets[currentMode];
  if (!preset) {
    return;
  }

  document.getElementById("prompt").value = preset.prompt;
  document.getElementById("notes").value = preset.notes;
}

function checkVoiceAvailability() {
  fetch("/api/voice/available")
    .then((response) => response.json())
    .then((data) => {
      voiceAvailable = Boolean(data.available);
      const voiceCheckbox = document.getElementById("voice-enabled");
      const voiceNote = document.getElementById("voice-note");

      if (voiceNote && data.message) {
        voiceNote.textContent = data.available
          ? `${data.message} Available providers: ${data.providers.join(", ")}.`
          : `${data.message} Configure OPENAI_API_KEY or ELEVENLABS_API_KEY to enable it.`;
      }

      if (!voiceAvailable) {
        voiceCheckbox.checked = false;
        voiceCheckbox.disabled = true;
      }
    })
    .catch((error) => {
      console.log("Voice check failed:", error);
    });
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".mode-card").forEach((card) => {
    card.addEventListener("click", () => {
      updateModeSelection(card.dataset.mode);
    });
  });

  document
    .getElementById("producer-enabled")
    .addEventListener("change", syncProducerControls);
  document
    .getElementById("load-example-btn")
    .addEventListener("click", loadExamplePrompt);

  updateModeSelection(currentMode);
  clearPreviousSession();
  Promise.resolve(rehydrateSessionState()).finally(() => {
    initSocket();
    checkVoiceAvailability();
  });
});

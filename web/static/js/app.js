// Writers Room Web Interface - Client-side JavaScript

let socket = null;
let sessionActive = false;
let audioQueue = [];
let isPlayingAudio = false;
let reconnectTimer = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_DELAY_MS = 5000;

// Initialize WebSocket connection
function initSocket() {
  if (
    socket &&
    (socket.readyState === WebSocket.OPEN ||
      socket.readyState === WebSocket.CONNECTING)
  ) {
    return;
  }

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const wsUrl = `${protocol}://${window.location.host}/ws`;
  socket = new WebSocket(wsUrl);

  socket.addEventListener("open", () => {
    console.log("Connected to server");
    reconnectAttempts = 0;
    if (reconnectTimer) {
      window.clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    if (sessionActive) {
      updateStatusBanner(true, "Connection restored. Waiting for live updates...");
    }
    rehydrateSessionState();
  });

  socket.addEventListener("message", (event) => {
    try {
      const message = JSON.parse(event.data);
      if (message && message.event) {
        handleEvent(message.event, message.data || {});
      }
    } catch (err) {
      console.error("WebSocket message parse failed:", err);
    }
  });

  socket.addEventListener("close", () => {
    console.log("Disconnected from server");
    scheduleReconnect();
  });

  socket.addEventListener("error", (err) => {
    console.error("WebSocket error:", err);
  });
}

function scheduleReconnect() {
  if (reconnectTimer) {
    return;
  }

  const delay = Math.min(1000 * 2 ** reconnectAttempts, MAX_RECONNECT_DELAY_MS);
  reconnectAttempts += 1;

  if (sessionActive) {
    updateStatusBanner(
      true,
      `Connection lost. Reconnecting in ${Math.round(delay / 1000)}s...`,
    );
  }

  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null;
    initSocket();
  }, delay);
}

function showSessionNote(message) {
  const note = document.getElementById("session-note");
  if (!note) {
    return;
  }
  note.textContent = message;
  note.classList.remove("hidden");
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
  startBtn.textContent = active ? "Session Running..." : "Start Writers Room";
}

async function rehydrateSessionState() {
  try {
    const response = await fetch("/api/status");
    if (!response.ok) {
      throw new Error(`Status request failed with ${response.status}`);
    }

    const status = await response.json();
    sessionActive = Boolean(status.active);

    if (sessionActive) {
      setStartButtonState(true);
      updateStatusBanner(true, "Session in progress. Waiting for live updates...");

      if (status.config && status.config.producer_enabled) {
        document.getElementById("agent-the-producer").classList.remove("hidden");
      }
      if (status.story_state) {
        updateStoryStatePanel(status.story_state);
      }
      clearSessionNote();
      return;
    }

    setStartButtonState(false);
    updateStatusBanner(false);

    if (status.last_transcript) {
      showSessionNote(`Transcript saved to ${status.last_transcript}`);
    } else {
      clearSessionNote();
    }
  } catch (error) {
    console.error("Failed to rehydrate session state:", error);
  }
}

function handleEvent(eventName, data) {
  switch (eventName) {
    case "connected":
      console.log("Server acknowledged connection:", data);
      break;
    case "session_started":
      console.log("Session started:", data);
      sessionActive = true;
      clearSessionNote();
      updateStatusBanner(true, `Round 1 of ${data.rounds} starting...`);
      document.getElementById("story-state-panel").classList.remove("hidden");
      if (data.mode_info) {
        document.getElementById("state-mode").textContent =
          data.mode_info.name || data.mode;
      }
      if (data.config && data.config.producer_enabled) {
        document.getElementById("agent-the-producer").classList.remove("hidden");
      }
      break;
    case "story_state_update":
      console.log("Story state update:", data);
      updateStoryStatePanel(data.state);
      break;
    case "round_started":
      console.log("Round started:", data);
      updateStatusBanner(true, `Round ${data.round} of ${data.total}`);
      break;
    case "agent_thinking": {
      console.log("Agent thinking:", data.agent);
      const { card, status } = ensureAgentCard(data.agent, data.color);
      if (card) {
        card.classList.add("thinking");
      }
      if (status) {
        status.innerHTML = '<span class="spinner"></span> Thinking...';
      }
      break;
    }
    case "agent_response": {
      console.log("Agent response:", data.agent, data.response);
      const { card, status, responsesDiv } = ensureAgentCard(
        data.agent,
        data.color,
      );

      if (card) {
        card.classList.remove("thinking");
      }
      if (status) {
        status.textContent = `Round ${data.round}`;
      }
      if (responsesDiv) {
        const placeholder = responsesDiv.querySelector(".placeholder-text");
        if (placeholder) {
          responsesDiv.innerHTML = "";
        }

        const responseItem = document.createElement("div");
        responseItem.className = "response-item";
        responseItem.style.borderLeftColor = data.color;

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
      }

      if (data.audio) {
        queueAudio({ data: data.audio, mime: data.audio_mime });
      }
      break;
    }
    case "producer_thinking": {
      console.log("Producer thinking...");
      const card = document.getElementById("agent-the-producer");
      const status = document.getElementById("status-the-producer");
      if (card) {
        card.classList.add("thinking");
      }
      if (status) {
        status.innerHTML = '<span class="spinner"></span> Judging...';
      }
      updateStatusBanner(true, `The Producer is evaluating Round ${data.round}...`);
      break;
    }
    case "producer_verdict": {
      console.log("Producer verdict:", data);
      const card = document.getElementById("agent-the-producer");
      const status = document.getElementById("status-the-producer");
      const responsesDiv = document.getElementById("responses-the-producer");

      if (card) {
        card.classList.remove("thinking");
      }
      if (status) {
        status.textContent = `Round ${data.round}`;
      }
      if (responsesDiv) {
        const placeholder = responsesDiv.querySelector(".placeholder-text");
        if (placeholder) {
          responsesDiv.innerHTML = "";
        }

        const responseItem = document.createElement("div");
        responseItem.className = "response-item producer-response";

        const roundLabel = document.createElement("div");
        roundLabel.className = "response-round";
        roundLabel.textContent = `Round ${data.round} Verdict`;

        const responseText = document.createElement("div");
        responseText.className = "response-text";
        responseText.textContent = data.response;

        responseItem.appendChild(roundLabel);
        responseItem.appendChild(responseText);
        responsesDiv.appendChild(responseItem);
        responsesDiv.scrollTop = responsesDiv.scrollHeight;
      }

      updateLeaderboard(data.leaderboard);

      if (data.audio) {
        queueAudio({ data: data.audio, mime: data.audio_mime });
      }
      break;
    }
    case "round_completed":
      console.log("Round completed:", data.round);
      break;
    case "session_completed": {
      console.log("Session completed:", data);
      sessionActive = false;
      updateStatusBanner(false);
      if (data.transcript_path) {
        showSessionNote(`Transcript saved to ${data.transcript_path}`);
      }

      if (data.story_state) {
        updateStoryStatePanel(data.story_state);
      }
      if (data.winner) {
        showWinner(data.winner);
      }
      if (data.worst) {
        showFired(data.worst);
      }

      const startBtn = document.getElementById("start-btn");
      startBtn.disabled = false;
      startBtn.textContent = "Start Writers Room";
      break;
    }
    case "error": {
      console.error("Error:", data.message);
      alert("Error: " + data.message);
      sessionActive = false;
      updateStatusBanner(false);
      showSessionNote(`Session error: ${data.message}`);

      const startBtn = document.getElementById("start-btn");
      startBtn.disabled = false;
      startBtn.textContent = "Start Writers Room";
      break;
    }
    default:
      console.log("Unhandled event:", eventName, data);
  }
}
// Normalize agent name to valid ID
function normalizeAgentId(agentName) {
  return agentName
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function ensureAgentCard(agentName, color) {
  const agentId = normalizeAgentId(agentName);
  let card = document.getElementById(`agent-${agentId}`);
  if (card) {
    return {
      card,
      status: document.getElementById(`status-${agentId}`),
      responsesDiv: document.getElementById(`responses-${agentId}`),
    };
  }

  const grid = document.getElementById("agent-grid");
  card = document.createElement("div");
  card.className = "agent-card custom-agent";
  card.id = `agent-${agentId}`;

  const header = document.createElement("div");
  header.className = "agent-header";

  const nameEl = document.createElement("div");
  nameEl.className = "agent-name text-cyan";
  nameEl.textContent = agentName;

  const specialty = document.createElement("div");
  specialty.className = "agent-specialty";
  specialty.textContent = "Custom Agent";

  const status = document.createElement("div");
  status.className = "agent-status";
  status.id = `status-${agentId}`;
  status.textContent = "Waiting...";

  header.appendChild(nameEl);
  header.appendChild(specialty);
  header.appendChild(status);

  const responsesDiv = document.createElement("div");
  responsesDiv.className = "agent-responses";
  responsesDiv.id = `responses-${agentId}`;
  responsesDiv.innerHTML = '<p class="placeholder-text">Waiting...</p>';

  card.appendChild(header);
  card.appendChild(responsesDiv);
  if (grid) {
    grid.appendChild(card);
  }

  if (color) {
    card.style.borderColor = color;
  }

  return { card, status, responsesDiv };
}

// Update status banner
function updateStatusBanner(active, message = "") {
  const banner = document.getElementById("status-banner");
  const detail = document.getElementById("status-detail");

  if (active) {
    banner.classList.add("active");
    if (message) {
      detail.textContent = message;
    }
  } else {
    banner.classList.remove("active");
  }
}

// Update story state panel
function updateStoryStatePanel(state) {
  if (!state) return;

  const panel = document.getElementById("story-state-panel");
  panel.classList.remove("hidden");

  // Update individual fields
  document.getElementById("state-mode").textContent = state.mode
    ? state.mode.toUpperCase()
    : "-";

  // Act names
  const actNames = { 1: "SETUP", 2: "CONFRONTATION", 3: "RESOLUTION" };
  document.getElementById("state-act").textContent =
    actNames[state.current_act] || state.current_act;

  // Tension
  const tension = state.tension_level || 3;
  document.getElementById("state-tension").textContent = `${tension}/10`;
  document.getElementById("tension-fill").style.width = `${tension * 10}%`;

  // Color the tension bar based on level
  const tensionFill = document.getElementById("tension-fill");
  if (tension <= 3) {
    tensionFill.style.background = "var(--accent-green)";
  } else if (tension <= 6) {
    tensionFill.style.background = "var(--accent-amber)";
  } else {
    tensionFill.style.background = "var(--accent-red)";
  }

  document.getElementById("state-pacing").textContent =
    state.pacing || "steady";
  document.getElementById("state-words").textContent = state.word_count || 0;

  // Story needs - would need to be calculated client-side or sent from server
  // For now, just show a placeholder based on act
  let needs = "Continue building momentum";
  if (state.current_act === 1) {
    needs = "Establish characters and conflict";
  } else if (state.current_act === 2) {
    needs = "Increase tension and complications";
  } else if (state.current_act === 3) {
    needs = "Build toward resolution";
  }
  document.getElementById("state-needs").textContent = needs;
}

// Update leaderboard
function updateLeaderboard(leaderboard) {
  const leaderboardDiv = document.getElementById("leaderboard");
  const leaderboardList = document.getElementById("leaderboard-list");

  if (!leaderboard || leaderboard.length === 0) {
    leaderboardDiv.classList.add("hidden");
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
    history.textContent = `(${item.scores.join(", ")})`;

    li.appendChild(rank);
    li.appendChild(name);
    li.appendChild(score);
    li.appendChild(history);

    leaderboardList.appendChild(li);
  });
}

// Show winner banner
function showWinner(winner) {
  const banner = document.getElementById("winner-banner");
  const name = document.getElementById("winner-name");
  const score = document.getElementById("winner-score");

  name.textContent = winner.name;
  score.textContent = `${winner.average}/10 Average Score`;

  banner.classList.remove("hidden");

  // Scroll to winner
  banner.scrollIntoView({ behavior: "smooth", block: "center" });
}

// Show fired banner
function showFired(worst) {
  const banner = document.getElementById("fired-banner");
  const name = document.getElementById("fired-name");
  const score = document.getElementById("fired-score");

  name.textContent = worst.name;
  score.textContent = `Lowest Score: ${worst.average}/10`;

  banner.classList.remove("hidden");
}

// Queue audio for playback
function queueAudio(audioPayload) {
  if (!audioPayload) {
    return;
  }
  audioQueue.push(audioPayload);
  playNextAudio();
}

// Play next audio in queue
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

  try {
    const audioPlayer = document.getElementById("audio-player");
    audioPlayer.src = `data:${audioMime};base64,${audioData}`;
    audioPlayer.onended = () => {
      isPlayingAudio = false;
      playNextAudio();
    };
    audioPlayer.onerror = () => {
      console.error("Audio playback error");
      isPlayingAudio = false;
      playNextAudio();
    };
    audioPlayer.play().catch((err) => {
      console.error("Failed to play audio:", err);
      isPlayingAudio = false;
      playNextAudio();
    });
  } catch (error) {
    console.error("Audio error:", error);
    isPlayingAudio = false;
    playNextAudio();
  }
}

// Start a new session
async function startSession() {
  if (sessionActive) {
    alert("A session is already running!");
    return;
  }

  const prompt = document.getElementById("prompt").value.trim();
  const mode = document.getElementById("mode").value;
  const rounds = parseInt(document.getElementById("rounds").value);
  const temperature = parseFloat(document.getElementById("temperature").value);
  const producerEnabled = document.getElementById("producer-enabled").checked;
  const fireWorst = document.getElementById("fire-worst").checked;
  const voiceEnabled = document.getElementById("voice-enabled").checked;
  const includeCustomAgents = document.getElementById(
    "include-custom-agents",
  ).checked;

  if (!prompt) {
    alert("Please enter a story prompt!");
    return;
  }

  if (rounds < 1 || rounds > 10) {
    alert("Please enter between 1 and 10 rounds");
    return;
  }

  // Clear previous results
  clearPreviousSession();
  clearSessionNote();

  // Disable start button
  const startBtn = document.getElementById("start-btn");
  startBtn.disabled = true;
  startBtn.innerHTML = '<span class="spinner"></span> Starting...';

  try {
    const response = await fetch("/api/start", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        prompt: prompt,
        mode: mode,
        rounds: rounds,
        temperature: temperature,
        producer_enabled: producerEnabled,
        fire_worst: fireWorst,
        voice_enabled: voiceEnabled,
        include_custom_agents: includeCustomAgents,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Failed to start session");
    }

    console.log("Session started successfully");
  } catch (error) {
    console.error("Failed to start session:", error);
    alert("Failed to start session: " + error.message);

    startBtn.disabled = false;
    startBtn.textContent = "Start Writers Room";
  }
}

// Clear previous session
function clearPreviousSession() {
  // Clear audio queue
  audioQueue = [];
  isPlayingAudio = false;
  clearSessionNote();

  // Clear all agent responses
  const agentIds = [
    "rod-serling",
    "stephen-king",
    "hp-lovecraft",
    "jorge-borges",
    "robert-stack",
    "rip-tequila-bot",
    "the-producer",
  ];

  agentIds.forEach((id) => {
    const responsesDiv = document.getElementById(`responses-${id}`);
    if (responsesDiv) {
      responsesDiv.innerHTML = '<p class="placeholder-text">Waiting...</p>';
    }

    const status = document.getElementById(`status-${id}`);
    if (status) {
      status.textContent = "Waiting...";
    }

    const card = document.getElementById(`agent-${id}`);
    if (card) {
      card.classList.remove("thinking");
    }
  });

  // Remove dynamically created custom agent cards
  document.querySelectorAll(".agent-card.custom-agent").forEach((card) => {
    card.remove();
  });

  // Hide results
  document.getElementById("leaderboard").classList.add("hidden");
  document.getElementById("winner-banner").classList.add("hidden");
  document.getElementById("fired-banner").classList.add("hidden");
  document.getElementById("agent-the-producer").classList.add("hidden");
  document.getElementById("story-state-panel").classList.add("hidden");
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  initSocket();
  console.log("Writers Room Web Interface initialized");

  // Check voice availability
  fetch("/api/voice/available")
    .then((response) => response.json())
    .then((data) => {
      const voiceCheckbox = document.getElementById("voice-enabled");
      const voiceNote = document.getElementById("voice-note");
      if (voiceNote && data.message) {
        voiceNote.textContent = data.available
          ? `${data.message} Available providers: ${data.providers.join(", ")}.`
          : `${data.message} Configure OPENAI_API_KEY or ELEVENLABS_API_KEY to enable it.`;
      }
      if (!data.available || data.providers.length === 0) {
        voiceCheckbox.disabled = true;
        voiceCheckbox.parentElement.style.opacity = "0.5";
        voiceCheckbox.parentElement.title =
          "TTS not available (no providers configured)";
      }
    })
    .catch((err) => console.log("Voice check failed:", err));
});

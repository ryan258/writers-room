// Writers Room Web Interface - Client-side JavaScript

let socket = null;
let sessionActive = false;

// Initialize SocketIO connection
function initSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('connected', (data) => {
        console.log('Server acknowledged connection:', data);
    });

    socket.on('session_started', (data) => {
        console.log('Session started:', data);
        sessionActive = true;
        updateStatusBanner(true, `Round 1 of ${data.rounds} starting...`);

        // Show Producer card if enabled
        if (data.config.producer_enabled) {
            document.getElementById('agent-the-producer').classList.remove('hidden');
        }
    });

    socket.on('round_started', (data) => {
        console.log('Round started:', data);
        updateStatusBanner(true, `Round ${data.round} of ${data.total}`);
    });

    socket.on('agent_thinking', (data) => {
        console.log('Agent thinking:', data.agent);
        const agentId = normalizeAgentId(data.agent);
        const card = document.getElementById(`agent-${agentId}`);
        const status = document.getElementById(`status-${agentId}`);

        if (card) {
            card.classList.add('thinking');
        }
        if (status) {
            status.innerHTML = '<span class="spinner"></span> Thinking...';
        }
    });

    socket.on('agent_response', (data) => {
        console.log('Agent response:', data.agent, data.response);
        const agentId = normalizeAgentId(data.agent);
        const card = document.getElementById(`agent-${agentId}`);
        const status = document.getElementById(`status-${agentId}`);
        const responsesDiv = document.getElementById(`responses-${agentId}`);

        // Remove thinking state
        if (card) {
            card.classList.remove('thinking');
        }

        // Update status
        if (status) {
            status.textContent = `Round ${data.round}`;
        }

        // Add response
        if (responsesDiv) {
            // Clear placeholder on first response
            const placeholder = responsesDiv.querySelector('p[style*="italic"]');
            if (placeholder) {
                responsesDiv.innerHTML = '';
            }

            const responseItem = document.createElement('div');
            responseItem.className = 'response-item';
            responseItem.style.borderLeftColor = data.color;

            const roundLabel = document.createElement('div');
            roundLabel.className = 'response-round';
            roundLabel.textContent = `Round ${data.round}`;

            const responseText = document.createElement('div');
            responseText.className = 'response-text';
            responseText.textContent = data.response;

            responseItem.appendChild(roundLabel);
            responseItem.appendChild(responseText);
            responsesDiv.appendChild(responseItem);

            // Scroll to bottom
            responsesDiv.scrollTop = responsesDiv.scrollHeight;
        }
    });

    socket.on('producer_thinking', (data) => {
        console.log('Producer thinking...');
        const card = document.getElementById('agent-the-producer');
        const status = document.getElementById('status-the-producer');

        if (card) {
            card.classList.add('thinking');
        }
        if (status) {
            status.innerHTML = '<span class="spinner"></span> Judging...';
        }

        updateStatusBanner(true, `The Producer is evaluating Round ${data.round}...`);
    });

    socket.on('producer_verdict', (data) => {
        console.log('Producer verdict:', data);
        const card = document.getElementById('agent-the-producer');
        const status = document.getElementById('status-the-producer');
        const responsesDiv = document.getElementById('responses-the-producer');

        // Remove thinking state
        if (card) {
            card.classList.remove('thinking');
        }

        // Update status
        if (status) {
            status.textContent = `Round ${data.round}`;
        }

        // Add verdict
        if (responsesDiv) {
            // Clear placeholder on first response
            const placeholder = responsesDiv.querySelector('p[style*="italic"]');
            if (placeholder) {
                responsesDiv.innerHTML = '';
            }

            const responseItem = document.createElement('div');
            responseItem.className = 'response-item';
            responseItem.style.borderLeftColor = '#00ff00';

            const roundLabel = document.createElement('div');
            roundLabel.className = 'response-round';
            roundLabel.textContent = `Round ${data.round} Verdict`;

            const responseText = document.createElement('div');
            responseText.className = 'response-text';
            responseText.textContent = data.response;

            responseItem.appendChild(roundLabel);
            responseItem.appendChild(responseText);
            responsesDiv.appendChild(responseItem);

            // Scroll to bottom
            responsesDiv.scrollTop = responsesDiv.scrollHeight;
        }

        // Update leaderboard
        updateLeaderboard(data.leaderboard);
    });

    socket.on('round_completed', (data) => {
        console.log('Round completed:', data.round);
    });

    socket.on('session_completed', (data) => {
        console.log('Session completed:', data);
        sessionActive = false;
        updateStatusBanner(false);

        // Show final results
        if (data.winner) {
            showWinner(data.winner);
        }

        if (data.worst) {
            showFired(data.worst);
        }

        // Re-enable start button
        const startBtn = document.getElementById('start-btn');
        startBtn.disabled = false;
        startBtn.textContent = '🎬 Start Writers Room';
    });

    socket.on('error', (data) => {
        console.error('Error:', data.message);
        alert('Error: ' + data.message);
        sessionActive = false;
        updateStatusBanner(false);

        const startBtn = document.getElementById('start-btn');
        startBtn.disabled = false;
        startBtn.textContent = '🎬 Start Writers Room';
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
    });
}

// Normalize agent name to valid ID
function normalizeAgentId(agentName) {
    return agentName.toLowerCase()
        .replace(/\./g, '')
        .replace(/\s+/g, '-');
}

// Update status banner
function updateStatusBanner(active, message = '') {
    const banner = document.getElementById('status-banner');
    const detail = document.getElementById('status-detail');

    if (active) {
        banner.classList.add('active');
        if (message) {
            detail.textContent = message;
        }
    } else {
        banner.classList.remove('active');
    }
}

// Update leaderboard
function updateLeaderboard(leaderboard) {
    const leaderboardDiv = document.getElementById('leaderboard');
    const leaderboardList = document.getElementById('leaderboard-list');

    if (!leaderboard || leaderboard.length === 0) {
        leaderboardDiv.classList.add('hidden');
        return;
    }

    leaderboardDiv.classList.remove('hidden');
    leaderboardList.innerHTML = '';

    const medals = ['🥇', '🥈', '🥉'];

    leaderboard.forEach((item, index) => {
        const li = document.createElement('li');
        li.className = 'leaderboard-item';

        const rank = document.createElement('span');
        rank.className = 'leaderboard-rank';
        rank.textContent = index < 3 ? medals[index] : `${index + 1}.`;

        const name = document.createElement('span');
        name.className = 'leaderboard-name';
        name.textContent = item.name;

        const score = document.createElement('span');
        score.className = 'leaderboard-score';
        score.textContent = `${item.average}/10`;

        const history = document.createElement('span');
        history.className = 'leaderboard-history';
        history.textContent = `(${item.scores.join(', ')})`;

        li.appendChild(rank);
        li.appendChild(name);
        li.appendChild(score);
        li.appendChild(history);

        leaderboardList.appendChild(li);
    });
}

// Show winner banner
function showWinner(winner) {
    const banner = document.getElementById('winner-banner');
    const name = document.getElementById('winner-name');
    const score = document.getElementById('winner-score');

    name.textContent = winner.name;
    score.textContent = `${winner.average}/10 Average Score`;

    banner.classList.remove('hidden');

    // Scroll to winner
    banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Show fired banner
function showFired(worst) {
    const banner = document.getElementById('fired-banner');
    const name = document.getElementById('fired-name');
    const score = document.getElementById('fired-score');

    name.textContent = worst.name;
    score.textContent = `Lowest Score: ${worst.average}/10`;

    banner.classList.remove('hidden');
}

// Start a new session
async function startSession() {
    if (sessionActive) {
        alert('A session is already running!');
        return;
    }

    const prompt = document.getElementById('prompt').value.trim();
    const rounds = parseInt(document.getElementById('rounds').value);
    const temperature = parseFloat(document.getElementById('temperature').value);
    const producerEnabled = document.getElementById('producer-enabled').checked;
    const fireWorst = document.getElementById('fire-worst').checked;

    if (!prompt) {
        alert('Please enter a story prompt!');
        return;
    }

    if (rounds < 1 || rounds > 10) {
        alert('Please enter between 1 and 10 rounds');
        return;
    }

    // Clear previous results
    clearPreviousSession();

    // Disable start button
    const startBtn = document.getElementById('start-btn');
    startBtn.disabled = true;
    startBtn.innerHTML = '<span class="spinner"></span> Starting...';

    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: prompt,
                rounds: rounds,
                temperature: temperature,
                producer_enabled: producerEnabled,
                fire_worst: fireWorst
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to start session');
        }

        console.log('Session started successfully');
    } catch (error) {
        console.error('Failed to start session:', error);
        alert('Failed to start session: ' + error.message);

        startBtn.disabled = false;
        startBtn.textContent = '🎬 Start Writers Room';
    }
}

// Clear previous session
function clearPreviousSession() {
    // Clear all agent responses
    const agentIds = [
        'rod-serling', 'stephen-king', 'hp-lovecraft',
        'jorge-borges', 'robert-stack', 'rip-tequila-bot', 'the-producer'
    ];

    agentIds.forEach(id => {
        const responsesDiv = document.getElementById(`responses-${id}`);
        if (responsesDiv) {
            responsesDiv.innerHTML = '<p style="color: #666; font-style: italic;">Waiting...</p>';
        }

        const status = document.getElementById(`status-${id}`);
        if (status) {
            status.textContent = 'Waiting...';
        }

        const card = document.getElementById(`agent-${id}`);
        if (card) {
            card.classList.remove('thinking');
        }
    });

    // Hide results
    document.getElementById('leaderboard').classList.add('hidden');
    document.getElementById('winner-banner').classList.add('hidden');
    document.getElementById('fired-banner').classList.add('hidden');
    document.getElementById('agent-the-producer').classList.add('hidden');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initSocket();
    console.log('Writers Room Web Interface initialized');
});

# Writers Room Development Roadmap

## Phase 1: MVP - The Basic Writers Room

**Goal**: Get three agents arguing in your terminal

### 1.1 Environment Setup
- [x] Create virtual environment
- [x] Install dependencies (`openai`, `python-dotenv`)
- [x] Create `.env` file with OpenRouter API key
- [x] Test OpenRouter connection with a simple API call

### 1.2 Core Agent System
- [x] Build `Agent` class in `agents.py`
  - [x] Constructor: name, model, system_prompt
  - [x] Method: `generate_response(context)`
  - [x] OpenRouter API integration with proper headers
- [x] Create `personalities.py` with the system prompts
  - [x] Cosmic Horror ("H.P. Lovecraft")
  - [x] Sitcom/Twist ("Rod Serling")
  - [x] Marketing Exec ("RIP Tequila Bot")
  - [x] *Expanded Roster: King, Borges, Stack*

### 1.3 Basic Orchestration
- [x] Build `main.py` game loop
  - [x] Initialize agents
  - [x] Get user's starting prompt
  - [x] Run 3 rounds of agent turns (round-robin)
  - [x] Pass conversation history to each agent
  - [x] Print responses to terminal

### 1.4 Terminal Output
- [x] Add colored output for each agent
  - [x] Distinct colors for all 6 agents
- [x] Format conversation clearly in terminal

**Deliverable**: You can run `python main.py`, enter a prompt, and watch six agents argue for 3 rounds in color.

---

## Phase 2: Enhanced Experience

**Goal**: Make it more fun and usable

### 2.1 Transcript Saving
- [x] Create `transcripts/` directory
- [x] Save each session to timestamped file
- [x] Format saved transcripts nicely

### 2.2 Configurable Rounds
- [x] Let user choose number of rounds
- [x] Add option to continue after rounds complete
- [ ] Add "interrupt" command to stop mid-session (Ctrl+C works)

### 2.3 Error Handling
- [x] Handle API failures gracefully (retries in Agent class)
- [x] Validate OpenRouter API key on startup
- [x] Better error messages

### 2.4 Agent Improvements
- [x] Add temperature/creativity controls per agent
- [x] Allow swapping models via command-line args
- [x] Max token limits already set (80 tokens per response)

**Deliverable**: ✅ COMPLETE - Enhanced terminal experience with CLI args, validation, and better UX.

---

## Phase 3: The Producer Agent

**Goal**: Add a judge to the chaos

### 3.1 Producer Agent
- [ ] Create seventh agent: "The Producer"
- [ ] System prompt: Judges which writer is "winning"
- [ ] Runs after each round or at the end
- [ ] Provides snarky commentary on each agent's contribution

### 3.2 Scoring System (Optional)
- [ ] Producer rates each contribution (1-10)
- [ ] Track scores across rounds
- [ ] Declare a "winner" at the end
- [ ] Producer can "fire" the worst performer

**Deliverable**: A meta-agent that provides commentary and judges the others.

---

## Phase 4: Audio Experience

**Goal**: Hear them argue out loud

### 4.1 Text-to-Speech Integration
- [ ] Choose TTS provider (ElevenLabs, OpenAI TTS, or local)
- [ ] Assign unique voices to each agent
- [ ] Stream or play audio after each response
- [ ] Add toggle to enable/disable TTS

### 4.2 Audio Improvements
- [ ] Save audio transcripts alongside text
- [ ] Add background music/ambiance (optional)

**Deliverable**: Optional audio playback where you can hear the agents argue.

---

## Phase 5: Custom Web Interface (Based on ui.png Design)

**Goal**: Build the dark-themed card-based UI

### 5.1 Frontend Framework Setup
- [ ] Choose stack: Flask/FastAPI backend + HTML/CSS/JS frontend OR React
- [ ] Set up dark theme CSS

### 5.2 UI Implementation
- [ ] Header Section
- [ ] Prompt Input Area
- [ ] Agent Cards (Grid Layout for 6 agents)
- [ ] Controller Section

**Deliverable**: A polished dark-themed web interface.

---

## Phase 6: Experimental Features

**Goal**: Wild ideas to try

### 6.1 More Agents
- [x] Expand agent roster (Added Serling, King, Borges, Stack)
- [ ] Make agent roster configurable via UI/CLI

### 6.2 Dynamic Personalities
- [ ] Let user create custom agents via UI
- [ ] Save/load personality presets

### 6.3 Story Modes
- [ ] **Conflict Mode**: Agents actively try to sabotage each other
- [ ] **Collaboration Mode**: Agents try to build on each other's ideas
- [ ] **Chaos Mode**: Random agent order, random interruptions

**Deliverable**: Experimental features to make it even more chaotic and fun.

---

## Technical Debt & Maintenance

### Ongoing Tasks
- [ ] Add unit tests for Agent class
- [ ] Add integration tests for OpenRouter API
- [ ] Document model performance
- [ ] Track OpenRouter costs

---

## Current Status

**Phase**: Phase 2 Complete ✅
**Next Step**: Choose Phase 3 (Producer Agent), Phase 4 (Audio/TTS), or Phase 5 (Web UI)

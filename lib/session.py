"""
Session Orchestration for Writers Room.
"""
import threading
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from .story_state import StoryStateManager
from .agents import Agent
from .artifacts import build_artifact_paths, extract_markdown_title
from .custom_agents import CustomAgentManager
from .personalities import (
    PRODUCER,
    DEFAULT_MODEL,
    STORY_MODES,
    get_agent_roster,
    get_producer_mode_criteria,
    get_session_opening_prompt,
    is_dnd_mode,
)
from .final_draft import generate_final_draft
from .pipeline import generate_pipeline_report_from_draft
from .session_briefing import render_session_brief
from .session_turns import build_dnd_story_context, generate_dnd_turn, generate_story_turn

# Optional voice support
try:
    from .voice import generate_agent_audio
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

class SessionEvent:
    SESSION_STARTED = "session_started"
    SESSION_RESUMED = "session_resumed"
    ROUND_STARTED = "round_started"
    STORY_STATE_UPDATE = "story_state_update"
    AGENT_THINKING = "agent_thinking"
    AGENT_RESPONSE = "agent_response"
    PRODUCER_THINKING = "producer_thinking"
    PRODUCER_VERDICT = "producer_verdict"
    EDITOR_THINKING = "editor_thinking"
    EDITOR_RESPONSE = "editor_response"
    ROUND_COMPLETED = "round_completed"
    SESSION_COMPLETED = "session_completed"
    ERROR = "error"

def parse_producer_scores(producer_response: str, agent_names: List[str]) -> Dict[str, int]:
    """Parse scores from Producer's response with robust fallbacks."""
    scores = {}
    response_lines = [line.strip() for line in producer_response.splitlines() if line.strip()]

    def extract_score(patterns: List[str], text: str) -> Optional[int]:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                continue
            try:
                return max(1, min(10, int(match.group(1))))
            except (ValueError, IndexError):
                continue
        return None

    # Define aliases for agents with complex names
    aliases = {
        "RIP Tequila Bot": ["TM Bot", "Tequila Bot", "Tequila", "RIP Tequila", "Marketing Exec"],
        "H.P. Lovecraft": ["HP Lovecraft", "Lovecraft"],
        "Jorge Luis Borges": ["Borges", "Jorge Borges"],
        "Rod Serling": ["Serling", "Rod"],
        "Stephen King": ["King", "Stephen"],
        "Robert Stack": ["Stack", "Robert"]
    }

    for agent_name in agent_names:
        names_to_check = [agent_name]
        if agent_name in aliases:
            names_to_check.extend(aliases[agent_name])

        found_score_for_agent = False

        for name_variant in names_to_check:
            if found_score_for_agent:
                break

            patterns = [
                rf"(?:\*\*)?{re.escape(name_variant)}(?:\*\*)?\s*:\s*(\d+)\s*/\s*10\b",
                rf"(?:\*\*)?{re.escape(name_variant)}(?:\*\*)?.*?\b(\d+)\s*/\s*10\b",
                rf"(?:\*\*)?{re.escape(name_variant)}(?:\*\*)?.*?\bscore(?:d)?\D*(\d+)\b",
                rf"(?:\*\*)?{re.escape(name_variant)}(?:\*\*)?.*?\b(\d+)\s*out of\s*10\b",
            ]

            for line in response_lines:
                score = extract_score(patterns, line)
                if score is not None:
                    scores[agent_name] = score
                    found_score_for_agent = True
                    break

    # Fallback patterns
    for i, agent_name in enumerate(agent_names):
        if agent_name not in scores:
            writer_patterns = [
                rf"Writer\s*#?{i+1}\b.*?:\s*(\d+)\s*/\s*10\b",
                rf"Writer\s*#?{i+1}\b.*?\b(\d+)\s*out of\s*10\b",
            ]
            for line in response_lines:
                score = extract_score(writer_patterns, line)
                if score is not None:
                    scores[agent_name] = score
                    break

    # Fallback: assign neutral scores if absolutely nothing found
    if not scores and agent_names:
        scores = {name: 5 for name in agent_names}

    return scores

class SessionOrchestrator:
    def __init__(self, event_callback: Callable[[str, Dict[str, Any]], None]):
        self.emit = event_callback
        self.active = False
        self.agents = []
        self.producer = None
        self.conversation_history = []
        self.producer_feedback = []
        self.agent_scores = {}
        self.config = {}
        self.story_manager = None
        self.voice_enabled = False
        self.stop_event = threading.Event()
        self.transcript_path = None
        self.brief_path = None
        self.final_draft_path = None
        self.final_draft_markdown = None
        self.pipeline_dir = None

    def initialize(self, prompt: str, config: Dict[str, Any]):
        self.config = config
        self.active = True
        self.stop_event.clear()
        self.producer_feedback = []
        self.transcript_path = None
        self.brief_path = None
        self.final_draft_path = None
        self.final_draft_markdown = None
        self.pipeline_dir = None
        story_mode = config.get('mode', 'horror')
        if is_dnd_mode(story_mode):
            self.config['include_custom_agents'] = False
            self.config['producer_enabled'] = False
            self.config['produce_final_draft'] = False

        opening_prompt = get_session_opening_prompt(story_mode, prompt)
        notes = (config.get("notes") or "").strip()
        if notes:
            opening_prompt = f"{opening_prompt}\n\nCreative brief: {notes}"

        self.conversation_history = [{"role": "user", "content": opening_prompt}]

        self.story_manager = StoryStateManager(premise=prompt, mode=story_mode)
        
        self.agents, self.producer = self._initialize_agents(config)
        self.agent_scores = {agent['name']: [] for agent in self.agents}
        self.voice_enabled = config.get('voice_enabled', False) and VOICE_AVAILABLE
        
        # Initial emit
        self.emit(SessionEvent.SESSION_STARTED, {
            'prompt': prompt,
            'rounds': config.get('rounds', 3),
            'config': config,
            'mode': story_mode,
            'mode_info': STORY_MODES.get(story_mode, {}),
            'agent_roster': self._get_agent_roster_payload(),
        })

    def stop(self):
        self.active = False
        self.stop_event.set()

    def _initialize_agents(self, config):
        model_override = config.get('model') or DEFAULT_MODEL
        temperature = config.get('temperature', 0.9)
        producer_enabled = config.get('producer_enabled', True)
        story_mode = config.get('mode', 'horror')
        include_custom_agents = config.get('include_custom_agents', True)
        
        agents = []
        agent_configs = get_agent_roster(story_mode)

        dnd_mode = is_dnd_mode(story_mode)
        for agent_config in agent_configs:
            max_tokens = 300
            window_size = 15
            response_format = None
            json_key = None
            if dnd_mode:
                max_tokens = 400 if agent_config['name'] == "Dungeon Master" else 300
                window_size = 8
                response_format = {"type": "json_object"}
                json_key = "line"
            agent = Agent(
                name=agent_config['name'],
                model=model_override,
                system_prompt=agent_config['system_prompt'],
                temperature=temperature,
                max_tokens=max_tokens,
                window_size=window_size,
                response_format=response_format,
                json_key=json_key,
            )
            agents.append(
                {
                    'agent': agent,
                    'name': agent_config['name'],
                    'color': agent_config['color'],
                    'specialty': agent_config.get('specialty', ''),
                    'voice_id': None,
                }
            )

        # Append active custom agents if requested
        if include_custom_agents:
            manager = CustomAgentManager()
            for custom in manager.get_active_agents():
                custom_agent = Agent(
                    name=custom.name,
                    model=model_override,
                    system_prompt=custom.to_system_prompt(""),
                    temperature=temperature,
                )
                agents.append({
                    'agent': custom_agent,
                    'name': custom.name,
                    'color': custom.color,
                    'specialty': custom.specialty,
                    'voice_id': custom.voice_id
                })
            
        producer = None
        if producer_enabled:
             try:
                producer_prompt = (
                    PRODUCER
                    + "\n\nWhen structured output is requested, respond with a JSON object only."
                    + '\nUse this shape: {"assessment": "2-3 sentence overview", "scores": {"Exact Writer Name": 7}}.'
                    + "\nUse the exact writer names provided in the request as score keys and integer values from 1 to 10."
                    + "\nDo not include markdown fences or extra commentary outside the JSON object."
                    + f"\n\nMode-specific focus: {get_producer_mode_criteria(story_mode)}"
                )
                producer = Agent(
                    name="The Producer",
                    model=model_override,
                    system_prompt=producer_prompt,
                    temperature=0.7,
                    max_tokens=600,
                    response_format={"type": "json_object"},
                )
             except Exception as e:
                self.emit(SessionEvent.ERROR, {'message': f"Could not initialize Producer: {e}"})
                producer = None
        return agents, producer

    def run_session(self, rounds: int):
        try:
            for round_num in range(1, rounds + 1):
                if self.stop_event.is_set(): break
                
                self._run_round(round_num, rounds)
                
            self._finalize_session()
        except Exception as e:
            self.emit(SessionEvent.ERROR, {'message': str(e)})
            import traceback
            traceback.print_exc()
        finally:
             self.active = False
             self._persist_session_artifacts()
             self.emit(SessionEvent.SESSION_COMPLETED, self._get_session_summary())

    def _completed_rounds(self) -> int:
        """Return the highest round number recorded so far."""
        return max(
            (msg.get("round", 0) for msg in self.conversation_history if msg.get("round")),
            default=0,
        )

    def resume(self, additional_rounds: int):
        """Continue an already-completed session for more rounds."""
        start = self._completed_rounds() + 1
        self.active = True
        self.stop_event.clear()
        self.transcript_path = None
        self.brief_path = None
        self.final_draft_path = None
        self.final_draft_markdown = None
        self.pipeline_dir = None

        self.emit(SessionEvent.SESSION_RESUMED, {
            'additional_rounds': additional_rounds,
            'starting_round': start,
            'config': self.config,
            'agent_roster': self._get_agent_roster_payload(),
        })

        try:
            for round_num in range(start, start + additional_rounds):
                if self.stop_event.is_set():
                    break
                self._run_round(round_num, start + additional_rounds - 1)
            self._finalize_session()
        except Exception as e:
            self.emit(SessionEvent.ERROR, {'message': str(e)})
            import traceback
            traceback.print_exc()
        finally:
            self.active = False
            self._persist_session_artifacts()
            self.emit(SessionEvent.SESSION_COMPLETED, self._get_session_summary())

    def _build_story_state_payload(self, state=None):
         if state is None and self.story_manager:
             state = self.story_manager.get_state()
         if state is None:
             return None

         payload = state.to_dict()
         payload['open_threads'] = len(state.get_active_threads())
         payload['story_needs'] = [] if is_dnd_mode(state.mode) else state.get_story_needs()
         return payload

    def _run_round(self, round_num, total_rounds):
         state = self.story_manager.get_state()
         self.emit(SessionEvent.STORY_STATE_UPDATE, {
             'round': round_num,
             'state': self._build_story_state_payload(state)
         })
         
         self.emit(SessionEvent.ROUND_STARTED, {'round': round_num, 'total': total_rounds})
         
         # Agents turn
         for agent_info in self.agents:
             if self.stop_event.is_set(): return
             
             agent = agent_info['agent']
             name = agent_info['name']
             color = agent_info['color']
             
             self.emit(SessionEvent.AGENT_THINKING, {'agent': name, 'color': color})
             
             if is_dnd_mode(self.story_manager.state.mode):
                 story_context = build_dnd_story_context(
                     self.story_manager,
                     self.conversation_history,
                     name,
                     round_num,
                 )
                 response = generate_dnd_turn(
                     agent,
                     self.conversation_history,
                     story_context,
                     name,
                 )
             else:
                 story_context = self.story_manager.state.to_prompt_context()
                 response = generate_story_turn(
                     agent,
                     self.conversation_history,
                     story_context,
                     name,
                 )
             
             self.story_manager.process_contribution(response, name, round_num)
             
             self.conversation_history.append({
                 "role": "assistant",
                 "content": response,
                 "name": name,
                 "round": round_num,
             })
             
             audio_data = None
             if self.voice_enabled:
                 try:
                     audio_data = generate_agent_audio(
                         response,
                         name,
                         voice_id_override=agent_info.get('voice_id')
                     )
                 except Exception:
                     pass
                     
             self.emit(SessionEvent.AGENT_RESPONSE, {
                 'agent': name,
                 'response': response,
                 'color': color,
                 'round': round_num,
                 'audio': audio_data[0] if audio_data else None,
                 'audio_mime': audio_data[1] if audio_data else None
             })
             
         # Producer turn
         if self.producer:
             self._run_producer_turn(round_num)
             
         self.emit(SessionEvent.ROUND_COMPLETED, {'round': round_num})

    def _run_producer_turn(self, round_num):
         self.emit(SessionEvent.PRODUCER_THINKING, {'round': round_num})
         
         round_context = []
         for msg in self.conversation_history:
             if msg['role'] == 'assistant' and 'name' in msg:
                 new_msg = msg.copy()
                 new_msg['content'] = f"{msg['name']}: {msg['content']}"
                 round_context.append(new_msg)
             else:
                 round_context.append(msg)
                 
         agent_names = [a['name'] for a in self.agents]
         agent_names_str = ", ".join(agent_names)
         mode_criteria = get_producer_mode_criteria(self.config.get('mode', 'horror'))
         
         score_example = ", ".join(f'"{n}": 7' for n in agent_names[:2]) + ", ..."
         round_context.append({
             "role": "user",
             "content": (
                 f"Judge round {round_num}. Score these writers: [{agent_names_str}].\n"
                 f"Mode-specific criteria: {mode_criteria}\n"
                 f'Reply as JSON: {{"assessment": "2-3 sentence overview", "scores": {{{score_example}}}}}'
             ),
         })

         producer_story_context = self.story_manager.get_producer_context()
         producer_response = self.producer.generate_response(
             round_context,
             story_context=producer_story_context
         )

         # Try structured JSON first, fall back to regex parsing
         round_scores = self._parse_producer_json(producer_response, agent_names)
         if not round_scores:
             round_scores = parse_producer_scores(producer_response, agent_names)
         for agent_name, score in round_scores.items():
            if agent_name in self.agent_scores:
                self.agent_scores[agent_name].append(score)

         # Extract a display-friendly string from JSON or use the raw response
         display_response = producer_response
         parsed = Agent.parse_json_response(producer_response)
         if parsed and "assessment" in parsed:
             assessment = parsed["assessment"]
             score_lines = [f"{n}: {s}/10" for n, s in round_scores.items()]
             display_response = f"{assessment}\n\n" + "\n".join(score_lines)

         # Calculate leaderboard
         leaderboard = self._calculate_leaderboard()

         producer_audio = None
         if self.voice_enabled:
             try:
                producer_audio = generate_agent_audio(display_response, "The Producer")
             except Exception:
                pass

         self.emit(SessionEvent.PRODUCER_VERDICT, {
             'response': display_response,
             'scores': round_scores,
             'leaderboard': leaderboard,
             'round': round_num,
             'audio': producer_audio[0] if producer_audio else None,
             'audio_mime': producer_audio[1] if producer_audio else None
         })
         self.producer_feedback.append({
             'round': round_num,
             'response': display_response,
             'scores': round_scores,
         })

    @staticmethod
    def _parse_producer_json(raw: str, agent_names: List[str]) -> Optional[Dict[str, int]]:
        """Try to extract scores from a structured JSON producer response."""
        data = Agent.parse_json_response(raw)
        if not data:
            return None
        scores_obj = data.get("scores")
        if not isinstance(scores_obj, dict):
            return None
        scores: Dict[str, int] = {}
        for name in agent_names:
            val = scores_obj.get(name)
            if isinstance(val, (int, float)):
                scores[name] = max(1, min(10, int(val)))
        return scores if scores else None

    def _calculate_leaderboard(self):
         leaderboard = []
         for agent_name, scores in self.agent_scores.items():
             if scores:
                 avg_score = sum(scores) / len(scores)
                 leaderboard.append({
                     'name': agent_name,
                     'average': round(avg_score, 1),
                     'scores': scores,
                     'total_rounds': len(scores)
                 })
         leaderboard.sort(key=lambda x: x['average'], reverse=True)
         return leaderboard

    def _get_agent_roster_payload(self) -> List[Dict[str, str]]:
         return [
             {
                 'name': agent['name'],
                 'color': agent['color'],
                 'specialty': agent.get('specialty', ''),
             }
             for agent in self.agents
         ]

    def _finalize_session(self):
         # Generate the optional final draft before the artifact persistence step
         # in ``finally`` so transcript/brief saving is not responsible for
         # triggering long-running editor work.
         self.final_draft_markdown = self._maybe_generate_final_draft()

    def _persist_session_artifacts(self) -> None:
        """Generate and persist transcript, brief, final draft, and pipeline."""
        self.transcript_path = None
        self.brief_path = None
        self.final_draft_path = None
        self.pipeline_dir = None

        title = (
            extract_markdown_title(self.final_draft_markdown or "")
            or self.config.get("prompt")
            or "untitled-session"
        )
        artifact_paths = build_artifact_paths(
            title=title,
            transcript_dir=self.config.get("transcript_dir", "transcripts"),
            final_dir=self.config.get("final_dir", "final"),
            pipeline_dir=self.config.get("pipeline_dir", "pipelines"),
        )

        try:
            self.transcript_path = self.save_transcript(artifact_paths.transcript_path)
        except Exception as exc:
            self.emit(SessionEvent.ERROR, {'message': f"Transcript save failed: {exc}"})

        if self.final_draft_markdown:
            try:
                self.final_draft_path = self._save_final_draft_markdown(
                    artifact_paths.final_draft_path,
                    self.final_draft_markdown,
                )
            except Exception as exc:
                self.emit(
                    SessionEvent.ERROR,
                    {'message': f"Final draft save failed: {exc}"},
                )
                self.final_draft_path = None

        try:
            self.brief_path = render_session_brief(
                prompt=self.config.get('prompt', ''),
                mode=self.config.get('mode', 'horror'),
                story_state=self.story_manager.get_state() if self.story_manager else None,
                conversation_history=self.conversation_history,
                leaderboard=self._calculate_leaderboard(),
                transcript_path=self.transcript_path,
                output_path=artifact_paths.brief_path,
                final_draft_markdown=self.final_draft_markdown,
            )
        except Exception as exc:
            self.emit(SessionEvent.ERROR, {'message': f"Brief render failed: {exc}"})
            self.brief_path = None

        if self.final_draft_path:
            try:
                self.pipeline_dir = generate_pipeline_report_from_draft(
                    draft_path=self.final_draft_path,
                    model=self.config.get("model") or DEFAULT_MODEL,
                    output_dir=artifact_paths.pipeline_dir,
                )
            except Exception as exc:
                self.emit(
                    SessionEvent.ERROR,
                    {'message': f"Pipeline generation failed: {exc}"},
                )
                self.pipeline_dir = None

    def save_transcript(self, output_path: str | Path) -> Optional[str]:
        """Persist the web session transcript and return the file path."""
        if not self.conversation_history:
            return None

        transcript_path = Path(output_path)
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        prompt = self.config.get("prompt") or self.conversation_history[0]["content"]

        with transcript_path.open("w", encoding="utf-8") as handle:
            handle.write("=" * 60 + "\n")
            if self.story_manager and is_dnd_mode(self.story_manager.get_state().mode):
                handle.write("WRITERS ROOM D&D TABLE TRANSCRIPT\n")
            else:
                handle.write("WRITERS ROOM WEB TRANSCRIPT\n")
            handle.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            handle.write(f"Prompt: {prompt}\n")
            handle.write(f"Mode: {self.config.get('mode', 'horror')}\n")
            handle.write(f"Rounds Requested: {self.config.get('rounds', 0)}\n")
            if self.story_manager:
                state = self.story_manager.get_state()
                handle.write(f"Final Act: {state.current_act.name}\n")
                handle.write(f"Word Count: {state.word_count}\n")
            handle.write("=" * 60 + "\n\n")

            if self.story_manager and is_dnd_mode(self.story_manager.get_state().mode):
                handle.write(f"ADVENTURE HOOK: {self.config.get('prompt', prompt)}\n\n")
                current_round = None
                for message in self.conversation_history:
                    if message.get("role") != "assistant":
                        continue
                    message_round = message.get("round")
                    if message_round != current_round:
                        current_round = message_round
                        handle.write("-" * 60 + "\n")
                        handle.write(f"ROUND {current_round}\n")
                        handle.write("-" * 60 + "\n\n")
                    handle.write(f"{message.get('name', 'Agent')}: {message.get('content', '')}\n\n")
            else:
                for message in self.conversation_history:
                    role = message.get("role")
                    if role == "user":
                        handle.write(f"[USER] {message.get('content', '')}\n\n")
                    elif role == "assistant":
                        author = message.get("name", "Agent")
                        handle.write(f"[{author}] {message.get('content', '')}\n\n")

            if self.producer_feedback:
                handle.write("-" * 60 + "\n")
                handle.write("PRODUCER VERDICTS\n")
                handle.write("-" * 60 + "\n\n")
                for verdict in self.producer_feedback:
                    handle.write(f"[ROUND {verdict['round']}] {verdict['response']}\n")
                    if verdict["scores"]:
                        score_summary = ", ".join(
                            f"{name}: {score}/10" for name, score in verdict["scores"].items()
                        )
                        handle.write(f"Scores: {score_summary}\n")
                    handle.write("\n")

        return str(transcript_path)

    def _maybe_generate_final_draft(self) -> Optional[str]:
        """Run the two-pass Editor if the toggle is on and mode allows it."""
        if not self.config.get('produce_final_draft'):
            return None
        if is_dnd_mode(self.config.get('mode', 'horror')):
            return None
        if not self.conversation_history:
            return None

        try:
            return generate_final_draft(
                config=self.config,
                conversation_history=self.conversation_history,
                story_state=self.story_manager.get_state() if self.story_manager else None,
                emit=self.emit,
            )
        except Exception as exc:
            self.emit(SessionEvent.ERROR, {'message': f"Final draft failed: {exc}"})
            return None

    @staticmethod
    def _save_final_draft_markdown(output_path: str | Path, markdown: str) -> str:
        """Persist the final draft to its canonical location."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markdown, encoding="utf-8")
        return str(target)

    def _get_session_summary(self):
        leaderboard = self._calculate_leaderboard()
        winner = leaderboard[0] if leaderboard else None
        worst = leaderboard[-1] if len(leaderboard) > 1 and self.config.get('fire_worst', False) else None
        final_state = self._build_story_state_payload()

        return {
            'leaderboard': leaderboard,
            'winner': winner,
            'worst': worst,
            'story_state': final_state,
            'transcript_path': self.transcript_path,
            'brief_path': getattr(self, 'brief_path', None),
            'final_draft_path': getattr(self, 'final_draft_path', None),
            'pipeline_dir': getattr(self, 'pipeline_dir', None),
        }

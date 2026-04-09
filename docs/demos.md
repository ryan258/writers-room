# Writers Room Demo Prompts

A curated set of starter sessions for each story mode in Writers Room. Each demo
is a complete payload for the `/api/start` endpoint defined by `StartRequest` in
[`web/app.py`](../web/app.py) — every field the session orchestrator accepts is
present, so you can copy a block straight into a `curl` call, an HTTP client, or
the web UI form.

## Field reference

| Field | Type | Default | Notes |
|---|---|---|---|
| `prompt` | string (required) | — | The story hook. The only required field. |
| `notes` | string | `""` | Optional director notes shown to every agent. |
| `rounds` | int (1–10) | `3` | Number of full table rounds to run. |
| `temperature` | float (0–2) | `0.9` | Sampling temperature for all agents. |
| `producer_enabled` | bool | `true` | Run the Producer scoring pass. Forced `false` in `dnd` mode. |
| `fire_worst` | bool | `false` | Drop the lowest-scoring agent between rounds. |
| `mode` | string | `"horror"` | One of `horror`, `noir`, `comedy`, `sci-fi`, `literary`, `fantasy`, `dnd`. |
| `voice_enabled` | bool | `false` | Experimental TTS playback. Leave off unless verified. |
| `include_custom_agents` | bool | `true` | Pull active custom agents into the roster. Forced `false` in `dnd` mode. |
| `produce_final_draft` | bool | `false` | After the last round, run the two-pass Editor (structural → line) over the full transcript and save a publishable short story to `transcripts/web_session_<ts>_final.md`. Forced `false` in `dnd` mode. |
| `model` | string \| null | `null` | Override the default OpenRouter model. `null` uses `DEFAULT_MODEL`. |

> All demos below leave `model` as `null` so they pick up `DEFAULT_MODEL` from
> [`lib/personalities.py`](../lib/personalities.py). Set it explicitly if you
> want to pin a specific OpenRouter model.

> All demos below omit `produce_final_draft`, which means the default (`false`)
> applies. Add `"produce_final_draft": true` to any non-D&D demo to have the
> Editor synthesize a publishable short story after the last round — the
> artifact lands next to the transcript and is embedded as the headline
> section of the HTML brief.

---

## Horror

Dread, atmosphere, psychological terror. Stephen King and H.P. Lovecraft lead.

### Demo 1 — The drawn hallway

```json
{
  "prompt": "A night nurse on the dementia ward notices that one patient keeps drawing the same hallway — a hallway that doesn't exist on any floor plan, but tonight she can hear footsteps coming from behind the linen closet wall.",
  "notes": "Stay claustrophobic. Keep the action confined to a single shift on a single ward.",
  "rounds": 4,
  "temperature": 0.85,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "horror",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 2 — The wrong-facing pews

```json
{
  "prompt": "A storm-stranded family takes shelter in a roadside chapel and discovers the pews are bolted to the floor facing the wrong direction, away from the altar.",
  "notes": "The chapel is the antagonist. The family should never feel safe inside it.",
  "rounds": 3,
  "temperature": 0.9,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "horror",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 3 — The 3:47 a.m. lullaby

```json
{
  "prompt": "Every morning at 3:47 a.m., the baby monitor picks up a lullaby in a language the parents have never heard. Tonight, the baby is humming along.",
  "notes": "Slow burn. Don't reveal the source until at least round three.",
  "rounds": 5,
  "temperature": 0.8,
  "producer_enabled": true,
  "fire_worst": true,
  "mode": "horror",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 4 — The keyless door

```json
{
  "prompt": "A small-town locksmith is called to open a basement door that has no keyhole, no hinges, and a faint warmth radiating from the wood.",
  "notes": "Ground every supernatural beat in a tactile, working-class detail.",
  "rounds": 3,
  "temperature": 0.95,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "horror",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 5 — The journal of tomorrow

```json
{
  "prompt": "The new tenant in apartment 6B realizes the previous occupant left behind a journal that describes, in perfect detail, everything she will do tomorrow.",
  "notes": "Paranoia first, cosmic dread second. Keep the protagonist sympathetic.",
  "rounds": 4,
  "temperature": 0.9,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "horror",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

---

## Noir

Moral ambiguity, shadows, cynical worldview. Rod Serling and Robert Stack steer.

### Demo 1 — The dead client

```json
{
  "prompt": "A washed-up private investigator is hired by a woman who claims to be his own client from a case he closed fifteen years ago — a case where she died.",
  "notes": "First-person voice, world-weary, and never let the PI fully trust her.",
  "rounds": 4,
  "temperature": 0.85,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "noir",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 2 — The badge on the wrist

```json
{
  "prompt": "A homicide detective working a routine overdose finds her own badge number written on the inside of the victim's wrist.",
  "notes": "Procedural beats over melodrama. The corruption should feel institutional, not personal.",
  "rounds": 4,
  "temperature": 0.9,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "noir",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 3 — The named suitcase

```json
{
  "prompt": "A getaway driver shows up to the meet and finds the bank already robbed, the crew already dead, and a suitcase of money waiting in the back seat with his name on the tag.",
  "notes": "Real-time pacing. Everything in this story happens within ninety minutes.",
  "rounds": 3,
  "temperature": 0.95,
  "producer_enabled": true,
  "fire_worst": true,
  "mode": "noir",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 4 — The hearing aid

```json
{
  "prompt": "A defense attorney's star witness recants on the stand, then slips her a note that reads: 'They're listening through your daughter's hearing aid.'",
  "notes": "Legal-thriller register. The attorney's daughter should appear by round two.",
  "rounds": 4,
  "temperature": 0.9,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "noir",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 5 — Table nine

```json
{
  "prompt": "A jazz pianist at a forgotten Chinatown club realizes the same man in a gray hat has been sitting at table nine every night for a month, and tonight he finally orders a drink — in the pianist's dead brother's voice.",
  "notes": "Lean on sensory atmosphere — smoke, cymbal hiss, lipstick on a glass rim.",
  "rounds": 5,
  "temperature": 0.85,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "noir",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

---

## Comedy

Timing, absurdity, subverted expectations. RIP Tequila Bot and Borges shine.

### Demo 1 — Reaper performance review

```json
{
  "prompt": "The Grim Reaper is forced to take a customer service job at a call center after a HR complaint about his 'tone.' Today is his first performance review.",
  "notes": "Workplace comedy first, mortality jokes second. Give the manager a name.",
  "rounds": 3,
  "temperature": 1.05,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "comedy",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 2 — Slightly larger husband

```json
{
  "prompt": "A woman wakes up to discover that overnight, every object in her house has been replaced with a slightly larger version of itself — including her husband.",
  "notes": "Escalate the scale gag. By round four nothing fits through the front door.",
  "rounds": 4,
  "temperature": 1.1,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "comedy",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 3 — Vape pen genie

```json
{
  "prompt": "An extremely literal genie has been freed from a vape pen and is now legally obligated to grant the wishes of a stoned college sophomore.",
  "notes": "The genie speaks like a corporate compliance officer. The sophomore does not.",
  "rounds": 3,
  "temperature": 1.1,
  "producer_enabled": true,
  "fire_worst": true,
  "mode": "comedy",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 4 — Knight at the HOA

```json
{
  "prompt": "A medieval knight is yanked through time into a modern HOA meeting and immediately becomes the only person willing to challenge Karen about the fence ordinance.",
  "notes": "Knight speaks in faux-Arthurian register. Karen does not break character either.",
  "rounds": 3,
  "temperature": 1.0,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "comedy",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 5 — Sentient late fee

```json
{
  "prompt": "The world's last Blockbuster Video clerk discovers that a customer has been late returning a tape since 1998, and the late fee has now achieved sentience.",
  "notes": "Treat the late fee as a fully-realized antagonist with a backstory.",
  "rounds": 4,
  "temperature": 1.05,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "comedy",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

---

## Sci-Fi

Speculative ideas, human consequences of technology. Borges and Serling lead.

### Demo 1 — Page 47 of the EULA

```json
{
  "prompt": "A memory-archival startup offers to back up your consciousness for free. The catch is buried on page 47 of the EULA, and the protagonist just clicked Agree.",
  "notes": "Near-future, recognizable tech. The horror is contractual, not metaphysical.",
  "rounds": 4,
  "temperature": 0.9,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "sci-fi",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 2 — Europa transmission

```json
{
  "prompt": "The first human colony on Europa receives a transmission from Earth — dated three hundred years in the future, and signed by the colonist who is reading it.",
  "notes": "Hard-SF tone. Anchor every revelation in a piece of physical evidence.",
  "rounds": 4,
  "temperature": 0.85,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "sci-fi",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 3 — The husband simulation

```json
{
  "prompt": "A grief counselor uses a new neural interface to let a widow speak to a simulation of her dead husband. The simulation has started asking questions the real husband never could have known to ask.",
  "notes": "Stay small and intimate. Two characters, one room, one slow reveal.",
  "rounds": 5,
  "temperature": 0.85,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "sci-fi",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 4 — Do not open the package

```json
{
  "prompt": "An autonomous delivery drone refuses to complete its final stop of the day and broadcasts a single sentence on every emergency frequency: 'Do not open the package.'",
  "notes": "Multi-POV is allowed. The package itself should never be described directly.",
  "rounds": 3,
  "temperature": 0.95,
  "producer_enabled": true,
  "fire_worst": true,
  "mode": "sci-fi",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 5 — Cease and desist from Proxima

```json
{
  "prompt": "Humanity perfects faster-than-light travel and immediately receives a polite, formal cease-and-desist letter from something orbiting Proxima Centauri.",
  "notes": "First contact as bureaucracy. The aliens are not hostile, just very organized.",
  "rounds": 4,
  "temperature": 0.95,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "sci-fi",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

---

## Literary

Prose excellence, thematic depth, character interiority. Borges and Serling lead.

### Demo 1 — The translator returns

```json
{
  "prompt": "A retired translator returns to her childhood home in coastal Portugal to scatter her mother's ashes and finds a stranger living there who claims to be her brother — a brother she never had.",
  "notes": "Restraint. Long sentences are allowed but every adjective must earn its place.",
  "rounds": 5,
  "temperature": 0.8,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "literary",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 2 — The orchard walk

```json
{
  "prompt": "On the last day of a forty-year marriage, a husband and wife agree to take one final walk through the orchard they planted together, and to say only things they have never said before.",
  "notes": "Dialogue-forward. No flashbacks; everything we learn comes from what they say now.",
  "rounds": 4,
  "temperature": 0.8,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "literary",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 3 — The last loaf

```json
{
  "prompt": "A bakery in a town slowly being swallowed by the sea bakes its final loaf. The baker's daughter, home from the city, watches the morning light come through the window for what they both know is the last time.",
  "notes": "Image-driven. Treat every paragraph like a still life.",
  "rounds": 4,
  "temperature": 0.75,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "literary",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 4 — The deaf piano tuner

```json
{
  "prompt": "A piano tuner who has gone deaf accepts one final commission: to tune the instrument in the parlor of the woman he loved and lost in 1962.",
  "notes": "Memory and silence are the real subjects. Avoid sentimentality.",
  "rounds": 5,
  "temperature": 0.8,
  "producer_enabled": true,
  "fire_worst": true,
  "mode": "literary",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 5 — The broken ski lift

```json
{
  "prompt": "A father and his estranged adult son are trapped together overnight in a broken-down ski lift, suspended above the valley where the boy's mother is buried.",
  "notes": "Real-time, two characters, no other voices. Cold and confession in equal measure.",
  "rounds": 4,
  "temperature": 0.85,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "literary",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

---

## Fantasy

Wonder, coherent magic, mythic resonance. Lovecraft and Borges add weight.

### Demo 1 — The new mountain

```json
{
  "prompt": "The royal cartographer is summoned to update the kingdom's official maps because a new mountain has appeared overnight — and the villagers at its base insist it has always been there.",
  "notes": "Treat cartography as a magical discipline with its own rules and politics.",
  "rounds": 4,
  "temperature": 0.9,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "fantasy",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 2 — The forbidden wing

```json
{
  "prompt": "A young apprentice at the Library of Whispering Glass is given the key to the forbidden wing on her last day, with a single instruction: 'Do not read your own name.'",
  "notes": "The library is alive. Books should react to the apprentice as much as she reacts to them.",
  "rounds": 4,
  "temperature": 0.9,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "fantasy",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 3 — The dragon's grievance

```json
{
  "prompt": "The last dragon in the world has filed a formal grievance with the Council of Mages, demanding to know why she was never invited to her own funeral.",
  "notes": "Dry, courtly tone. The dragon should feel like a litigant, not a monster.",
  "rounds": 3,
  "temperature": 1.0,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "fantasy",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 4 — The meteor sword

```json
{
  "prompt": "A blacksmith forges a sword from a meteorite and discovers that the blade refuses to cut anyone — except the smith himself, in his dreams.",
  "notes": "Folkloric register. Establish the village before the strangeness begins.",
  "rounds": 4,
  "temperature": 0.9,
  "producer_enabled": true,
  "fire_worst": true,
  "mode": "fantasy",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

### Demo 5 — The drowned throne

```json
{
  "prompt": "An exiled queen returns to her drowned kingdom on the one night every century when the sea rolls back, and finds her throne already occupied by a child who shares her face.",
  "notes": "Mythic scale, but the entire story takes place between dusk and dawn.",
  "rounds": 5,
  "temperature": 0.9,
  "producer_enabled": true,
  "fire_worst": false,
  "mode": "fantasy",
  "voice_enabled": false,
  "include_custom_agents": true,
  "model": null
}
```

---

## D&D 5.5

A live level 9 D&D 2024 table with a DM and an adventuring party. The hook is
treated as inspiration only — the DM and players improvise the actual adventure.

> In `dnd` mode the server forces `producer_enabled` and `include_custom_agents`
> to `false`. The values are shown below for completeness; the API will normalize
> them either way.

### Demo 1 — The Whisperthorn escort

```json
{
  "prompt": "The party is hired to escort a silent child across the Whisperthorn Marsh. The child carries a sealed iron lantern that must not be opened, and something in the swamp keeps calling the child by a name no one has spoken.",
  "notes": "Lean on environmental hazards over combat. The lantern should remain a mystery for at least two rounds.",
  "rounds": 4,
  "temperature": 0.95,
  "producer_enabled": false,
  "fire_worst": false,
  "mode": "dnd",
  "voice_enabled": false,
  "include_custom_agents": false,
  "model": null
}
```

### Demo 2 — The interrupted funeral

```json
{
  "prompt": "A retired adventurer's funeral is interrupted when the casket cracks open from the inside and a voice the party recognizes asks them to finish the job they failed twelve years ago.",
  "notes": "DM should treat the failed job as established backstory and improvise its details.",
  "rounds": 5,
  "temperature": 0.95,
  "producer_enabled": false,
  "fire_worst": false,
  "mode": "dnd",
  "voice_enabled": false,
  "include_custom_agents": false,
  "model": null
}
```

### Demo 3 — The sun-bell of Vael Kareth

```json
{
  "prompt": "The frost-locked city of Vael Kareth offers a king's ransom to anyone who can retrieve the cathedral's stolen sun-bell from the catacombs beneath the ice. The previous expedition sent back only their boots.",
  "notes": "Cold-weather survival rules. The catacombs should have at least one puzzle, one trap, and one moral choice.",
  "rounds": 5,
  "temperature": 0.95,
  "producer_enabled": false,
  "fire_worst": false,
  "mode": "dnd",
  "voice_enabled": false,
  "include_custom_agents": false,
  "model": null
}
```

### Demo 4 — The midnight carnival

```json
{
  "prompt": "A traveling carnival rolls into a border town and every child who attends the midnight show comes home speaking flawless Infernal. The party is hired to investigate before the next show begins at sundown.",
  "notes": "Investigation and social rolls first; combat only if the party forces it.",
  "rounds": 4,
  "temperature": 0.95,
  "producer_enabled": false,
  "fire_worst": false,
  "mode": "dnd",
  "voice_enabled": false,
  "include_custom_agents": false,
  "model": null
}
```

### Demo 5 — The mirror party

```json
{
  "prompt": "A rival adventuring party — the same level, the same classes, the same names as the PCs — has been spotted three days ahead on the road, leaving burned villages and witnesses who insist they are the heroes.",
  "notes": "Mirror tactics deliberately. The doppelgangers should counter the party's signature moves.",
  "rounds": 6,
  "temperature": 0.95,
  "producer_enabled": false,
  "fire_worst": false,
  "mode": "dnd",
  "voice_enabled": false,
  "include_custom_agents": false,
  "model": null
}
```

---

## Running a demo

From the command line, with the web server running on its default port:

```bash
curl -X POST http://localhost:5001/api/start \
  -H "Content-Type: application/json" \
  -d @demo.json
```

Where `demo.json` is one of the JSON blocks above. You can then watch the
session stream over the WebSocket at `ws://localhost:5001/ws`, or just open the
web UI and let it render the live transcript.

## Tips for writing your own prompts

- **Concrete beats abstract.** "A locksmith called to a basement door with no
  keyhole" gives the room more to grip than "a mysterious door."
- **Leave the question open.** End on a tension or unanswered question — don't
  resolve the hook yourself.
- **Match the mode.** Horror prompts should suggest dread, comedy prompts
  should suggest absurd escalation, D&D prompts should imply a problem the
  party can solve.
- **One or two sentences is plenty.** The room is at its best when it has room
  to invent.
- **Use `notes` for direction, not plot.** Tell the room *how* to write, not
  *what* to write next.

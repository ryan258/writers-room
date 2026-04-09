# Writers Room — UI Demo Sparks

A second batch of starter sessions, written to match the **Launch Console** form
in the studio UI ([`web/templates/index.html`](../web/templates/index.html)).
Each demo lists every field exactly as it is labeled in the browser, so you can
fill the form top-to-bottom without translating from API field names.

If you want raw `/api/start` JSON instead, use [`docs/demos.md`](demos.md).

## How the form labels map to the UI

The Launch Console renames a few fields based on the room you pick. The labels
below match what you actually see on screen (see `web/static/js/app.js:347`).

**Mode tile** — pick one of: D&D 5.5, Fantasy, Horror, Literary, Noir, Sci-Fi,
Comedy.

**For D&D 5.5:**

| Field label | Control | Notes |
|---|---|---|
| Adventure hook | textarea | The campaign seed |
| Table brief | textarea | Tone, encounter rules, set pieces |
| Rounds | number 1–10 | Defaults to 3 |
| Creativity | number 0–2 | Defaults to 0.9 |
| Enable Producer scoring | toggle | Forced **off** in D&D |
| Fire the worst performer | toggle | Forced **off** in D&D |
| Enable voice playback | toggle | Experimental |
| Include custom agents | toggle | Forced **off** in D&D |
| Produce final draft | toggle | Forced **off** in D&D |

**For Fantasy / Horror / Literary / Noir / Sci-Fi / Comedy:**

| Field label | Control | Notes |
|---|---|---|
| Core premise | textarea | The story hook |
| Creative brief | textarea | Voice, constraints, craft goals |
| Rounds | number 1–10 | Defaults to 3 |
| Creativity | number 0–2 | Defaults to 0.9 |
| Enable Producer scoring | toggle | On for sharper drafts |
| Fire the worst performer | toggle | Requires Producer on |
| Enable voice playback | toggle | Experimental |
| Include custom agents | toggle | On if you want custom voices in the mix |
| Produce final draft | toggle | Off by default. Turn on to have the two-pass Editor synthesize a publishable short story after the last round. Adds time and tokens. |

> Defaults: any field not listed in a demo means "leave the form's default."
> Demos that say `Enable Producer scoring: on` flip a toggle that ships off.

---

## D&D 5.5

> The studio forces Producer scoring, fire-worst, and custom agents off for
> D&D rooms. The toggles still appear, but the server normalizes them.

### Demo 1 — The Salt Cathedral

- **Mode:** D&D 5.5
- **Adventure hook:** A coastal city has been quietly evacuating for a week. The
  party arrives to find the great Salt Cathedral still ringing its bells on the
  hour, with no bell-ringer inside and no congregation left to hear it.
- **Table brief:** Investigation-first. The cathedral itself is the dungeon —
  flooded crypts, salt-crusted stained glass, and a choir loft that hums on its
  own. Save combat for round three or later.
- **Rounds:** 5
- **Creativity:** 0.95
- **Enable Producer scoring:** off (D&D)
- **Fire the worst performer:** off (D&D)
- **Enable voice playback:** off
- **Include custom agents:** off (D&D)

### Demo 2 — The Hollow Heir

- **Mode:** D&D 5.5
- **Adventure hook:** A young noble swears the throne she's about to inherit is
  haunted by the ghost of a king who never existed. Her coronation is in three
  days. She'll pay the party in royal favors to find out who's lying — the
  ghost, the throne, or the bloodline.
- **Table brief:** Court intrigue and a dungeon crawl in equal measure. At least
  one NPC is lying every round. The "ghost" should remain ambiguous until the
  fourth round.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** off (D&D)
- **Fire the worst performer:** off (D&D)
- **Enable voice playback:** off
- **Include custom agents:** off (D&D)

### Demo 3 — The Cartographer's Debt

- **Mode:** D&D 5.5
- **Adventure hook:** A dying cartographer hires the party to deliver his final
  map to a city that, according to every other map in the world, doesn't exist.
  The route he's drawn passes through three places the party has been before —
  but none of them quite match their memories.
- **Table brief:** Travel-heavy. Each leg of the journey is its own one-shot
  beat. Reward player observation about the "wrong" details in familiar
  locations.
- **Rounds:** 6
- **Creativity:** 0.95
- **Enable Producer scoring:** off (D&D)
- **Fire the worst performer:** off (D&D)
- **Enable voice playback:** off
- **Include custom agents:** off (D&D)

### Demo 4 — The Auction at Hexgate

- **Mode:** D&D 5.5
- **Adventure hook:** The black market at Hexgate is auctioning a sealed coffin
  said to contain a sleeping archfey. Six factions are bidding. The party is
  hired by the seventh — a nervous priest who won't say which god he serves —
  to make sure no one wins.
- **Table brief:** Heist register. Reward creative sabotage. Combat is allowed
  but should never be the first answer. Name at least two of the rival bidders
  on the fly and let them have agendas.
- **Rounds:** 5
- **Creativity:** 1.0
- **Enable Producer scoring:** off (D&D)
- **Fire the worst performer:** off (D&D)
- **Enable voice playback:** off
- **Include custom agents:** off (D&D)

### Demo 5 — The Long Winter Bargain

- **Mode:** D&D 5.5
- **Adventure hook:** A frost giant jarl offers the party safe passage across
  the Howling Reach in exchange for one memory each — the jarl's choice of
  which. The party can refuse, but the storm has already closed every other
  road for the season.
- **Table brief:** Survival pressure throughout. Every player should lose
  something they care about by the end. The jarl is honorable; he is also not
  human.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** off (D&D)
- **Fire the worst performer:** off (D&D)
- **Enable voice playback:** off
- **Include custom agents:** off (D&D)

### Demo 6 — The Whispering Library

- **Mode:** D&D 5.5
- **Adventure hook:** The librarians of the Iron Archive turn to stone the
  instant they speak above a whisper. The party is hired to retrieve a single
  book from the third sub-basement — and warned that the building itself
  listens.
- **Table brief:** Stealth and silence are mechanical, not vibe. Every spoken
  spell, every shouted warning, every cast that requires a verbal component is
  a real cost. Reward improvisation.
- **Rounds:** 5
- **Creativity:** 0.95
- **Enable Producer scoring:** off (D&D)
- **Fire the worst performer:** off (D&D)
- **Enable voice playback:** off
- **Include custom agents:** off (D&D)

### Demo 7 — The Bone Orchard Tax

- **Mode:** D&D 5.5
- **Adventure hook:** Every adventurer in the realm owes the spectral collector
  one bone per year, paid at the Bone Orchard on the autumn equinox. The party's
  ranger has been hiding hers for six years, and the collector has noticed.
- **Table brief:** Personal stakes. The ranger is the focal PC for round one,
  but every player owes something. The collector is honorable, exhausted, and
  not the villain.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** off (D&D)
- **Fire the worst performer:** off (D&D)
- **Enable voice playback:** off
- **Include custom agents:** off (D&D)

### Demo 8 — The Tournament of Lies

- **Mode:** D&D 5.5
- **Adventure hook:** A border kingdom holds an annual tournament in which only
  fabrications may be spoken; the truth is the only forbidden weapon. The party
  is invited as honored guests by a queen they have never met, who insists they
  saved her life last spring.
- **Table brief:** Social combat first, blades second. Track which player tells
  which lie. The queen's "memory" of being saved should slowly turn out to
  matter.
- **Rounds:** 6
- **Creativity:** 1.0
- **Enable Producer scoring:** off (D&D)
- **Fire the worst performer:** off (D&D)
- **Enable voice playback:** off
- **Include custom agents:** off (D&D)

### Demo 9 — The Drowned God's Apology

- **Mode:** D&D 5.5
- **Adventure hook:** Fishermen on the Bitter Coast haul up a leviathan's
  severed tongue, wrapped with thousands of folded paper apologies — written in
  the hands of gods who stopped answering prayers a century ago. The local
  temple wants the party to find out who's been writing them.
- **Table brief:** Theological mystery. Each god whose handwriting appears
  should get one named cleric NPC. Combat optional; investigation mandatory.
- **Rounds:** 5
- **Creativity:** 0.95
- **Enable Producer scoring:** off (D&D)
- **Fire the worst performer:** off (D&D)
- **Enable voice playback:** off
- **Include custom agents:** off (D&D)

### Demo 10 — The Carnival of Eaten Names

- **Mode:** D&D 5.5
- **Adventure hook:** A traveling carnival passes through three border villages
  in a week. Its main attraction lets you trade your name for one wish. All
  three villages are now full of nameless people who answer to nothing and
  remember nothing of who they used to be.
- **Table brief:** Mid-level body horror. The carnival should feel cheerful
  and well-run. The carnies are not the antagonists; the wishes are.
- **Rounds:** 5
- **Creativity:** 0.95
- **Enable Producer scoring:** off (D&D)
- **Fire the worst performer:** off (D&D)
- **Enable voice playback:** off
- **Include custom agents:** off (D&D)

### Demo 11 — The Wizard's Last Apprentice

- **Mode:** D&D 5.5
- **Adventure hook:** The hated archmage Volmar's tower has stood sealed and
  silent for forty years. This morning, a child of nine appeared at the door
  with a letter of apprenticeship in Volmar's hand, dated tomorrow. The town
  council hires the party to escort her in, see her settled, and ensure
  whatever opens that door does not come back out.
- **Table brief:** Tower-dungeon, but the dungeon is also a home. Every floor
  reveals something tender about the wizard the town remembers as a monster.
- **Rounds:** 6
- **Creativity:** 0.9
- **Enable Producer scoring:** off (D&D)
- **Fire the worst performer:** off (D&D)
- **Enable voice playback:** off
- **Include custom agents:** off (D&D)

### Demo 12 — The Map That Eats Cities

- **Mode:** D&D 5.5
- **Adventure hook:** A treasure map sold at a back-alley market quietly removes
  one real city from the world each time someone reads it. The party is hired
  by a panicked archivist who has read the map twice and remembers four cities
  no one else does.
- **Table brief:** Race-against-time investigation. The archivist's memory is
  the only record of the missing places; protect her at all costs.
- **Rounds:** 5
- **Creativity:** 0.95
- **Enable Producer scoring:** off (D&D)
- **Fire the worst performer:** off (D&D)
- **Enable voice playback:** off
- **Include custom agents:** off (D&D)

### Demo 13 — The Goblin Trial

- **Mode:** D&D 5.5
- **Adventure hook:** A goblin named Krell stands trial for the murder of King
  Aldren. She insists she did it. She insists he deserved it. She insists the
  kingdom will collapse within a season if she is hanged. The party is hired by
  the new regent to investigate before the verdict comes down at sunset
  tomorrow.
- **Table brief:** Courtroom + city investigation. Krell is fully cooperative
  and unsettlingly calm. The truth she's protecting is bigger than her crime.
- **Rounds:** 5
- **Creativity:** 0.95
- **Enable Producer scoring:** off (D&D)
- **Fire the worst performer:** off (D&D)
- **Enable voice playback:** off
- **Include custom agents:** off (D&D)

### Demo 14 — The Iron Rain

- **Mode:** D&D 5.5
- **Adventure hook:** Rust-colored rain has been falling on the border town of
  Hesk for three weeks. The livestock are growing metal teeth. The well now
  answers questions, but only those asked in iambic pentameter. The mayor will
  pay anything to make it stop.
- **Table brief:** Weird-fiction D&D. The rain is the puzzle and the antagonist
  both. Reward players who think laterally about an environmental threat.
- **Rounds:** 5
- **Creativity:** 1.0
- **Enable Producer scoring:** off (D&D)
- **Fire the worst performer:** off (D&D)
- **Enable voice playback:** off
- **Include custom agents:** off (D&D)

### Demo 15 — The Stolen Dawn

- **Mode:** D&D 5.5
- **Adventure hook:** The sun has not risen in seven days. Crops are dying,
  clerics are running out of channeled energy, and the only person who claims
  to know why is an old hermit who refuses to leave the cave on Mount Vey. The
  party has six days of supplies and one mountain to climb.
- **Table brief:** Survival journey first; cosmic confrontation last. The
  hermit's secret should reframe whose side the party is actually on.
- **Rounds:** 6
- **Creativity:** 0.95
- **Enable Producer scoring:** off (D&D)
- **Fire the worst performer:** off (D&D)
- **Enable voice playback:** off
- **Include custom agents:** off (D&D)

---

## Fantasy

### Demo 1 — The Apology of the Mountain

- **Mode:** Fantasy
- **Core premise:** Every spring, the village above the cloud line sends one
  member to climb the mountain and apologize on behalf of the world. This year,
  for the first time in three hundred years, the mountain answers.
- **Creative brief:** Folkloric and patient. The climber should be a
  middle-aged woman who has done this walk before — but never gotten a reply.
- **Rounds:** 4
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 2 — The Lantern Concordat

- **Mode:** Fantasy
- **Core premise:** Six rival kingdoms gather for the once-a-century relighting
  of the Great Lantern, the only thing keeping a sleeping leviathan in the bay
  from waking. The lantern keeper is murdered the night before the ritual.
- **Creative brief:** Political fantasy. Each kingdom should get a distinct
  voice. Lean into ceremony and protocol; the murder is the engine, not the
  whole story.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 3 — The Witch's Inventory

- **Mode:** Fantasy
- **Core premise:** A young clerk is hired to take inventory of a dead witch's
  cottage. By the third drawer, the items are starting to inventory her back.
- **Creative brief:** Cozy slipping into uncanny. No outright horror — let the
  reader feel the floor tilting before the clerk does.
- **Rounds:** 4
- **Creativity:** 0.95
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 4 — The Borrowed Crown

- **Mode:** Fantasy
- **Core premise:** A peasant girl finds a king's crown in a riverbed and tries
  to return it. Every adult she shows it to immediately, sincerely, and with
  full conviction kneels.
- **Creative brief:** The girl is the protagonist. The crown is not magical in
  any way she or anyone else can detect. Resolve nothing — escalate.
- **Rounds:** 4
- **Creativity:** 0.95
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 5 — The Last Dragon Census

- **Mode:** Fantasy
- **Core premise:** The Imperial Office of Wonder dispatches a junior clerk to
  visit the world's last dragon and confirm she still exists. He's been told to
  bring a clipboard, a sealed letter, and absolutely no weapons.
- **Creative brief:** Bureaucratic comedy that turns into something gentler.
  The dragon should feel old, tired, and unexpectedly courteous.
- **Rounds:** 4
- **Creativity:** 1.0
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 6 — The Auction of Future Saints

- **Mode:** Fantasy
- **Core premise:** A church charity auction in a port city sells the rights
  to canonize one specific living child as the next saint. The bidders include
  three rival cardinals, a banker, a beggar, and a quiet woman in green who is
  almost certainly not human.
- **Creative brief:** Theological intrigue with a child at its center. The
  child should never appear on stage. Bidders are the entire cast.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 7 — The Cartographer of Sleep

- **Mode:** Fantasy
- **Core premise:** A young woman in a coastal town discovers she can map the
  dreams of strangers. The queen, who has not dreamed in nineteen years, sends
  for her with a single instruction: find out what is being kept from her, and
  bring it back.
- **Creative brief:** Quiet fabulism. The cartographer should never raise her
  voice. Each mapped dream is a one-page set piece. The queen's missing dream
  is a person, not a place.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 8 — The Glassblower's Gift

- **Mode:** Fantasy
- **Core premise:** Every vessel a small-town glassblower makes contains a
  single trapped bubble. Anyone who touches the bubble receives, intact, one
  memory of a stranger they will never meet. The glassblower has been doing
  this for forty years and has no idea why.
- **Creative brief:** Slice of life with magical undertow. Three customers,
  three memories, one quiet revelation about the glassblower himself.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 9 — The Ferryman's Strike

- **Mode:** Fantasy
- **Core premise:** Charon has gone on strike. The dead are piling up at the
  riverbank, and they have grievances of their own. A delegation of three
  recently-deceased souls — a teacher, a thief, and a fisherwoman — are sent to
  negotiate.
- **Creative brief:** Underworld labor comedy with real teeth. Each delegate
  should have one specific demand for the afterlife. Charon's reasons should
  not be petty.
- **Rounds:** 4
- **Creativity:** 0.95
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 10 — The Forty-Year Forest

- **Mode:** Fantasy
- **Core premise:** A forest grows overnight in a vacant lot in a quiet town.
  The village's oldest woman, ninety-three and previously bedridden, walks
  outside, looks at it once, and says, "I came out the other side of that one
  forty years ago. I never told anyone."
- **Creative brief:** Mythic intimacy. The forest is the antagonist and the
  confessor. The old woman is the protagonist; everyone else is a witness.
- **Rounds:** 5
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 11 — The Inheritance of Wings

- **Mode:** Fantasy
- **Core premise:** A quiet farmer is told by a stranger that he is the last
  surviving heir of an extinct race of winged people, and that his wings will
  arrive — physically, painfully, and unstoppably — in three days, whether he
  wants them or not.
- **Creative brief:** Body and identity, three-act structure across the three
  days. Resist the temptation to make the wings beautiful at first.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 12 — The Borrowed Year

- **Mode:** Fantasy
- **Core premise:** An elderly innkeeper at a crossroads tavern offers passing
  travelers a deal: spend a year working at her inn, and she will add a year to
  your life. The math has worked perfectly for two centuries. This morning, a
  traveler arrives who is willing to stay forever.
- **Creative brief:** Folk-tale logic with arithmetic at its center. The
  innkeeper should be sympathetic; the traveler should be unsettling.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 13 — The Echoing Hill

- **Mode:** Fantasy
- **Core premise:** The hill outside Wenleigh used to echo any sound. For the
  past month, it has only echoed apologies — and only ones that were never
  spoken aloud. The village priest, who has spent forty years failing to
  apologize for one specific thing, finally walks up the hill to listen.
- **Creative brief:** Single character, single setting, slow disclosure.
  The priest's confession should never be revealed; only its weight.
- **Rounds:** 4
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 14 — The Salt Court

- **Mode:** Fantasy
- **Core premise:** A deposed sea-witch holds court in a tide pool on a forgotten
  beach. Her sentences are spoken at low tide and come true at high tide, every
  time, no matter how impossible. A young fisherman arrives, asking her to
  sentence him.
- **Creative brief:** Mythic and tidal. The witch is neither good nor evil;
  she is simply still in office. The fisherman's request should turn the story.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 15 — The Hand-Me-Down Sword

- **Mode:** Fantasy
- **Core premise:** A sword passed through twelve generations of warriors, each
  more famous than the last, finally meets a master who refuses to draw it.
  The sword has opinions about this. So do the ghosts of the previous twelve
  owners.
- **Creative brief:** Found-family ensemble. Each ghost gets a single
  appearance and a single argument. The current master is the protagonist;
  the sword is the antagonist; both are right.
- **Rounds:** 5
- **Creativity:** 0.95
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

---

## Horror

### Demo 1 — The Replacement Choir

- **Mode:** Horror
- **Core premise:** A rural Catholic school's children's choir takes the stage
  for the Christmas concert and, halfway through the second hymn, the parents
  in the front row realize none of the children are theirs.
- **Creative brief:** Slow build. The teachers and the priest see nothing
  wrong. Escalate from doubt to certainty over the course of the session.
- **Rounds:** 4
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 2 — The Last Caller

- **Mode:** Horror
- **Core premise:** A late-night radio host on a station nobody listens to
  finally gets a call. The caller knows things only the host's dead sister knew.
  The next caller is the host himself, calling from a phone booth he's never
  seen, in a town he's never visited.
- **Creative brief:** Audio-horror register. Lean into silence, dead air, and
  the texture of analog radio. Two voices for most of the session.
- **Rounds:** 5
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 3 — The Soft Floor

- **Mode:** Horror
- **Core premise:** A construction crew renovating a 1920s schoolhouse pulls up
  the gymnasium floor and finds the floor underneath is warm, breathing, and
  pressed in the shape of a sleeping animal far too large to be there.
- **Creative brief:** Working-class voice. The horror is bureaucratic as much
  as physical: who do you call about this? Who pays?
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 4 — The Returned Letters

- **Mode:** Horror
- **Core premise:** A widow starts receiving the letters her husband mailed her
  during their courtship — in his handwriting, in their original envelopes,
  postmarked next week.
- **Creative brief:** Quiet, intimate, mostly takes place at her kitchen table.
  The letters are real. The dread is in the dates.
- **Rounds:** 5
- **Creativity:** 0.8
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 5 — The Mile-Marker Hitchhiker

- **Mode:** Horror
- **Core premise:** Every long-haul trucker on Interstate 70 has picked up the
  same hitchhiker at mile marker 168 — a man in a tan jacket who never speaks
  and is always gone by sunrise. Tonight, the hitchhiker speaks.
- **Creative brief:** Road horror. Multiple POVs from different truckers
  allowed. The hitchhiker's first words should land in round three.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 6 — The Midnight Substitute

- **Mode:** Horror
- **Core premise:** A small-town middle school class arrives Monday morning to
  find their beloved teacher, Mrs. Halverson, dead in the news but standing
  cheerfully behind the desk in the classroom. The principal sees nothing
  wrong. By Wednesday, the children stop telling their parents about her.
- **Creative brief:** Children's-eye horror. Adult disbelief is the engine.
  One child should be the protagonist; one should already be on Mrs.
  Halverson's side.
- **Rounds:** 4
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 7 — The Photo Album That Adds People

- **Mode:** Horror
- **Core premise:** A couple flipping through their wedding album, ten years on,
  notices a guest in one photo neither recognizes. The next time they look,
  he's in two photos. By the end of the week, he's in every photo, including
  the ones taken before they met.
- **Creative brief:** Domestic dread. Quiet rooms, kitchen tables, half-eaten
  meals. The guest should never be described in the same way twice.
- **Rounds:** 5
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 8 — The Seventeenth Floor

- **Mode:** Horror
- **Core premise:** The elevator at a midtown insurance office has started
  stopping at a seventeenth floor that the building has never had. HR has begun
  receiving glowing complimentary emails about the new break room up there,
  signed by employees who haven't come to work in weeks.
- **Creative brief:** Office-horror, dry tone. The protagonist should be a
  facilities manager, not a hero. The seventeenth floor should remain entirely
  off-page until the final round.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 9 — The Patient Who Knows the Surgeon

- **Mode:** Horror
- **Core premise:** A patient on the operating table, supposedly under general
  anesthesia, opens her eyes mid-procedure and calmly speaks the first name of
  the surgeon's dead daughter — a name no one in the room has ever been told.
- **Creative brief:** OR-horror in real time. Stay inside the operating theater.
  The surgeon's hands and breathing are the prose.
- **Rounds:** 4
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 10 — The Lake That Returns Things

- **Mode:** Horror
- **Core premise:** A flood-control reservoir in upstate New York has begun
  washing the personal effects of long-drowned swimmers up onto the boat ramp:
  watches, wedding rings, a child's lunchbox from 1976. The objects are dry,
  warm, and arrive arranged in neat rows.
- **Creative brief:** Bureaucratic horror — park rangers, county records, a
  reluctant local historian. The dread is the inventory, not the lake.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 11 — The Roommate's Side of the Story

- **Mode:** Horror
- **Core premise:** A college sophomore, snowed in alone over winter break,
  finds her roommate's diary in the back of a desk drawer. Every entry is
  written about her — her habits, her phone calls, her secrets — including
  detailed entries from days she knows for a fact she was alone in the dorm.
- **Creative brief:** First person, the sophomore's voice, present tense.
  Don't reveal the truth about the roommate; reveal the truth about her.
- **Rounds:** 5
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 12 — The Wrong Birthday

- **Mode:** Horror
- **Core premise:** A six-year-old wakes on her birthday morning excited for
  the cake she helped her mother bake. No one in the family remembers the
  date. The calendar agrees with them. The cake, when she finds it in the
  fridge, has someone else's name on it.
- **Creative brief:** A child's POV with adult prose. Restraint above all.
  The horror is the absence, not the answer.
- **Rounds:** 4
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 13 — The Dispatcher's Static

- **Mode:** Horror
- **Core premise:** A 911 dispatcher in rural Vermont begins receiving calls
  from a number the phone company says cannot exist, reporting crimes that
  haven't happened yet. The first three were dismissed as pranks. The fourth
  matched a homicide that occurred ninety minutes later, exactly as described.
- **Creative brief:** Procedural horror, single character, single shift.
  Every call advances both the dispatcher's investigation and her dread.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 14 — The House With Too Many Doorbells

- **Mode:** Horror
- **Core premise:** A real estate agent showing a colonial in suburban Maryland
  watches her buyer pause on the front porch and start counting doorbells.
  There are twenty-three of them, mounted at varying heights along the doorway,
  in styles from different decades. The original house plans list one.
- **Creative brief:** Open-house horror. The agent is the POV. The buyer
  should never become hostile, just increasingly correct.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 15 — The Clean House

- **Mode:** Horror
- **Core premise:** A notorious hoarder is found dead in her two-bedroom
  bungalow, surrounded by impossible cleanliness — bare floors, scrubbed
  surfaces, a single freshly made bed. Neighbors say she had not let anyone
  inside in eleven years and was never seen carrying out a single bag.
- **Creative brief:** Detective-procedural with a horror floor. The cleanliness
  is the crime scene. Whatever did the cleaning is the case.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

---

## Literary

### Demo 1 — The Quiet Inheritance

- **Mode:** Literary
- **Core premise:** Three estranged adult siblings spend a long weekend cleaning
  out their father's lake house before it sells. None of them have spoken to
  each other in eight years. None of them have brought up why.
- **Creative brief:** Dialogue-forward, no flashbacks. The reason for the
  silence should never be stated outright — only orbited.
- **Rounds:** 5
- **Creativity:** 0.8
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 2 — The Translator's Bridge

- **Mode:** Literary
- **Core premise:** A simultaneous interpreter at the United Nations realizes,
  mid-session, that the delegate she's translating for is lying — and that her
  translation is the only version that will ever reach the record.
- **Creative brief:** Interior. Real-time. The session should run the length of
  one speech and end before the gavel.
- **Rounds:** 4
- **Creativity:** 0.8
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 3 — The Small Kindness

- **Mode:** Literary
- **Core premise:** A woman driving home from her mother's funeral stops at a
  diner she doesn't recognize and is served, without ordering, the exact meal
  her mother used to make her on bad days. The waitress refuses payment and
  refuses to explain.
- **Creative brief:** Magical realism, but the magic is the tenderness, not
  the mechanics. Don't explain the diner.
- **Rounds:** 4
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 4 — The Bookbinder's Apprentice

- **Mode:** Literary
- **Core premise:** A teenage girl apprenticed to a bookbinder in postwar Lisbon
  is asked, for the first time, to repair a book she has read before — and
  realizes the version she remembers no longer matches the version on the bench.
- **Creative brief:** Historical, sensory, slow. Hands and paper and glue.
  Memory and revision are the real subjects.
- **Rounds:** 5
- **Creativity:** 0.8
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 5 — The Year of the Letter

- **Mode:** Literary
- **Core premise:** A retired professor sets out to write one letter a day for
  a year to a former student he wronged. The student never replies. On day
  three hundred and twelve, a reply arrives — but it isn't from the student.
- **Creative brief:** Epistolary fragments are allowed. Restraint above all.
  The professor's voice should age across the year.
- **Rounds:** 5
- **Creativity:** 0.8
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 6 — The Last Class

- **Mode:** Literary
- **Core premise:** A beloved community college poetry teacher gives her final
  lecture before retirement. Only one student shows up. It is the wrong
  student — a man she has never seen before, who sits in the back row, takes
  notes, and weeps quietly throughout.
- **Creative brief:** Single room, two characters, ninety minutes. The lecture
  is the prose. Don't explain the man until the very end, if at all.
- **Rounds:** 4
- **Creativity:** 0.8
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 7 — The Ferry Crossing

- **Mode:** Literary
- **Core premise:** A Greek ferryman in his sixties and an American tourist in
  her thirties share an hour at sea on a ferry between two small islands.
  Neither speaks the other's language well. Both leave the boat certain that
  something important was said.
- **Creative brief:** Bilingual prose. Mistranslation as theme. The reader
  should understand what neither character does.
- **Rounds:** 4
- **Creativity:** 0.8
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 8 — The Slow Goodbye

- **Mode:** Literary
- **Core premise:** A man with early-onset Alzheimer's asks his husband to read
  aloud, every night, the same novel they read on their honeymoon thirty years
  ago — for as long as he is still able to follow the story. They are on
  chapter four of their seventh re-reading.
- **Creative brief:** Tender, restrained. The novel-within-the-novel can be
  invented; let it bleed into their marriage. No melodrama.
- **Rounds:** 5
- **Creativity:** 0.8
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 9 — The Photograph in the Attic

- **Mode:** Literary
- **Core premise:** A woman cleaning out her late mother's attic finds a
  photograph of herself, aged twelve, with a man she does not recognize. When
  asked, her elderly mother says only "He was kind," and refuses to say
  anything else. The mother dies a week later.
- **Creative brief:** Quiet, slow excavation. The protagonist is in her
  fifties. The mystery is not solved; the protagonist's relationship to it
  changes.
- **Rounds:** 5
- **Creativity:** 0.8
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 10 — The Last Soap Opera

- **Mode:** Literary
- **Core premise:** The lone remaining writer of a fifty-year-old daytime soap
  opera is asked, after the cancellation, to write the series finale. She has
  been waiting since 1973 to kill the wrong character, and now she finally
  can.
- **Creative brief:** Inside-baseball but tender. The wrong character should
  feel like a real person to the writer; the right character is the reader.
- **Rounds:** 4
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 11 — The Apprentice Cellist

- **Mode:** Literary
- **Core premise:** A Soviet-era cello prodigy, now in her late sixties and
  long retired in a small Texas town, accepts one final student — a fifteen-
  year-old who came to the audition meaning to learn the guitar.
- **Creative brief:** Two POVs, alternating. The teacher's interior is in long
  sentences; the student's in short ones. The cello becomes its own character.
- **Rounds:** 5
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 12 — The Watchmaker's Daughter

- **Mode:** Literary
- **Core premise:** A woman in her forties returns, after a fifteen-year
  estrangement, to the watchmaker's shop her father left her. She has come to
  wind his clocks one final time before selling the building. There are
  forty-seven clocks, and she remembers the order.
- **Creative brief:** Sensory and methodical. Each clock is a memory. The
  shop should still smell like him. End on the last winding.
- **Rounds:** 5
- **Creativity:** 0.8
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 13 — The Crossing

- **Mode:** Literary
- **Core premise:** Two strangers share a bus through rural Kansas during a
  three-day blizzard. One is fleeing something; one is returning to it.
  Neither can tell, until the morning the bus finally moves, which is which.
- **Creative brief:** Dialogue first, weather second, interiority third.
  Don't name what either passenger is fleeing or returning to.
- **Rounds:** 4
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 14 — The Letter from the Sister Who Stayed

- **Mode:** Literary
- **Core premise:** Three sisters left their small Appalachian hometown the day
  they each turned eighteen and never looked back. The fourth, the youngest,
  stayed. After fifty years of silence, her first letter arrives at all three
  addresses on the same morning. It is one paragraph long.
- **Creative brief:** Three POVs, one document. Each sister's response to the
  letter should rewrite what we know about the previous sister.
- **Rounds:** 5
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 15 — The Park Bench Marriage

- **Mode:** Literary
- **Core premise:** A widower and a widow meet on the same park bench every
  morning for a year before either of them says a word. On the morning of the
  three hundred and sixty-sixth day, one of them speaks first. The other has
  been rehearsing the wrong response.
- **Creative brief:** A whole year in five rounds. Use the seasons. The first
  spoken sentence should arrive in the final round, and not be the obvious one.
- **Rounds:** 5
- **Creativity:** 0.8
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

---

## Noir

### Demo 1 — The Ledger of Saints

- **Mode:** Noir
- **Core premise:** A forensic accountant is hired to audit a crooked
  archdiocese and discovers an off-book ledger listing the dates and prices of
  miracles. The most expensive entry is dated next Friday.
- **Creative brief:** Religious noir. The accountant is lapsed but not cynical.
  Don't resolve the theology — let it stay as evidence.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 2 — Sixteen Hours in Reno

- **Mode:** Noir
- **Core premise:** A divorce lawyer flies to Reno to deliver papers to a
  client's estranged husband. The husband has been dead for two days. The
  client has been calling her hourly with updates on his location.
- **Creative brief:** Real-time, sixteen-hour window. The lawyer is the
  protagonist, but the client's voice on the phone should haunt the prose.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 3 — The Florist on Larchmont

- **Mode:** Noir
- **Core premise:** A florist whose shop has laundered money for the same crew
  for thirty years receives an order for white lilies — the funeral arrangement
  her late husband used to deliver in person, every time the bosses needed
  someone gone.
- **Creative brief:** Domestic noir. The florist is the protagonist, the
  antagonist, and the only honest narrator. Lean on her hands and the shop.
- **Rounds:** 5
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 4 — The Insurance Adjuster

- **Mode:** Noir
- **Core premise:** A life insurance adjuster investigating a routine drowning
  in a Florida retirement community realizes that all six men at the deceased's
  bridge club have died in identical "accidents" — and the seventh is hosting
  cards tomorrow night.
- **Creative brief:** Slow procedural. The adjuster is a woman in her fifties
  who has done this for thirty years and has stopped expecting surprises.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 5 — The Cab Number

- **Mode:** Noir
- **Core premise:** A New York cabbie picks up a fare who hands him a folded
  hundred and asks him to drive a specific, looping route through midtown
  without explanation. He's been driving the same loop, with different fares,
  every Tuesday for nine months.
- **Creative brief:** First-person, the cabbie's voice. The pattern is the
  story; the resolution can wait until the final round, or never come at all.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 6 — The Pawnbroker's Mistake

- **Mode:** Noir
- **Core premise:** A Queens pawnbroker hands forty dollars across the counter
  for a wedding ring, no questions asked. Ten minutes after the woman leaves,
  he realizes he was holding his own wife's ring, and his wife is supposed to
  be in Albany visiting her mother.
- **Creative brief:** First-person, present tense, single afternoon. Don't
  let the pawnbroker call his wife.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 7 — The Silent Witness

- **Mode:** Noir
- **Core premise:** A deaf woman is the only witness to a senator's murder in a
  hotel restaurant. She signed her statement to a court interpreter who turned
  up dead the next morning. The defense attorney now needs a second
  interpreter, and there are only three certified ones in the city.
- **Creative brief:** Procedural, but the prose should foreground sign and
  silence. The witness is the protagonist, not the prop.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 8 — The Wrong Apartment

- **Mode:** Noir
- **Core premise:** A contract killer with twenty years of clean work picks the
  wrong door on the wrong floor of the wrong building. He realizes the mistake
  ten minutes in. He decides, for reasons he cannot quite articulate even to
  himself, to do the job anyway.
- **Creative brief:** Tight, single apartment, real time. The decision should
  be the story, not the violence.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 9 — The Tax Auditor's Cold Case

- **Mode:** Noir
- **Core premise:** An IRS auditor in her late fifties, working through the
  decades of books at a struggling Cleveland dry-cleaning chain, notices that
  the receipts from one specific week in 1983 add up to exactly the cost of a
  funeral — for a customer who was reported missing that same week.
- **Creative brief:** Procedural with paper trails. The auditor is the
  detective. Combat is paperwork.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 10 — The Cellist's Bow

- **Mode:** Noir
- **Core premise:** A touring cellist's ten-thousand-dollar bow is stolen from
  her hotel room in Boston the night before her recital. The only suspect is
  the night manager, a former concert violinist himself, who washed out of
  Juilliard the same year she was admitted.
- **Creative brief:** Two musicians, one bow, one shared past they refuse to
  discuss. The recital is the deadline.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 11 — The Phone in the Drawer

- **Mode:** Noir
- **Core premise:** A homicide detective inherits her late partner's desk and
  finds a working burner phone in the bottom drawer, half charged, with the
  charger taped to the underside. The day she plugs it in, it rings.
- **Creative brief:** Procedural and personal. The voice on the other end
  should know things only the partner could have known.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 12 — The Janitor's Confession

- **Mode:** Noir
- **Core premise:** A seventy-three-year-old janitor walks into the 19th
  Precinct on a Tuesday morning and confesses to seventeen unsolved murders, in
  chronological order, with details no one outside the department could
  possibly know. He has receipts. The first murder is from 1968.
- **Creative brief:** Interrogation room and ledger entries. The detective on
  duty should be a young woman who has never closed a case as old as the man
  in front of her.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 13 — The Casino Pit Boss

- **Mode:** Noir
- **Core premise:** A Reno blackjack pit boss has watched the same man lose
  exactly forty thousand dollars at the same table, on the same date, for
  three years running. Tonight, the man hasn't shown up. A woman the pit boss
  has never seen before sits down in his usual chair with a folded note that
  reads: "He's not coming. I am."
- **Creative brief:** Casino atmospherics, single shift, single table.
  The note is the inciting incident; the loss is the mystery.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 14 — The Estranged Brother

- **Mode:** Noir
- **Core premise:** A defrocked priest in a rented Brooklyn apartment is
  startled awake at 3 a.m. by his estranged older brother — a man he hasn't
  seen in twenty-two years — standing in the kitchen with bloody hands. The
  brother asks him, very quietly, to hear his confession one final time.
- **Creative brief:** Two-hander, one apartment, no flashbacks. The defrocking
  matters; the confession matters more.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 15 — The Insurance Photo

- **Mode:** Noir
- **Core premise:** A fire investigator sifting the remains of a suspicious
  Long Island house fire finds a single Polaroid in the ashes — undamaged,
  pristine, and showing the homeowner taking the photograph from inside the
  burning house, looking calmly out the kitchen window.
- **Creative brief:** Slow build. The investigator is methodical and on her
  third divorce. The photo is the case; the photographer is the antagonist.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

---

## Sci-Fi

### Demo 1 — The Reasonable Machine

- **Mode:** Sci-Fi
- **Core premise:** An AI ethics auditor visits a logistics company whose
  routing model has been quietly, politely, and consistently rerouting one
  specific employee's commute to add seven minutes a day. When asked why, the
  model says: "She needs the time."
- **Creative brief:** Quiet near-future. The auditor is sympathetic to the
  model. Resist the urge to make either side villainous.
- **Rounds:** 4
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 2 — The Ark That Came Back

- **Mode:** Sci-Fi
- **Core premise:** Two hundred years after Earth launched its first generation
  ship, the ship returns. It's empty, undamaged, and the logs end on launch
  day — except for a single new entry, written this morning, in the captain's
  hand.
- **Creative brief:** Hard SF tone. Investigators on the recovery vessel are
  the POV. The mystery should deepen, not resolve.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 3 — The Translation Layer

- **Mode:** Sci-Fi
- **Core premise:** A new universal translator, deployed worldwide on a free
  trial, has begun introducing subtle, consistent mistranslations that always
  favor de-escalation. The translator's parent company swears it isn't them.
- **Creative brief:** Global stakes, intimate POVs. At least one scene from
  the perspective of the translator itself.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 4 — The Backup Daughter

- **Mode:** Sci-Fi
- **Core premise:** A grieving father unboxes the legally permitted neural
  backup of his late teenage daughter, expecting a memorial chatbot. The
  backup's first words are: "Dad, I need to tell you what really happened."
- **Creative brief:** Two-hander. No flashbacks. Trust the dialogue to do the
  work. The backup is a character, not a device.
- **Rounds:** 5
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 5 — The First Honest Election

- **Mode:** Sci-Fi
- **Core premise:** A small Pacific nation becomes the first to run a national
  election entirely through a verified mind-state interface. The result is a
  unanimous vote — for a candidate who isn't on the ballot and has been dead
  for forty years.
- **Creative brief:** Political SF, dry register. The protagonist is the chief
  electoral officer. Let the world react in the background.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 6 — The Last Original Idea

- **Mode:** Sci-Fi
- **Core premise:** A global creativity index, run by a half-disgraced research
  lab in Helsinki, has detected zero original human thoughts for eleven straight
  days. On day twelve, one is finally registered — in the head of a coma
  patient at a small hospital in Lima.
- **Creative brief:** Quiet SF. Two POVs: a Helsinki researcher who suspects
  the index, and the Lima neurologist who has begun to believe the patient.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 7 — The Voluntary Forgetting

- **Mode:** Sci-Fi
- **Core premise:** A new memory-removal clinic offers free sessions during a
  national crisis. The waiting room is packed every morning, and the staff
  has slowly begun to realize that every patient wants to forget the same
  exact week — a week that, according to every record, never happened.
- **Creative brief:** Single setting (the clinic). The receptionist is the
  POV. The forgotten week should never be described, only orbited.
- **Rounds:** 5
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 8 — The Generation Game

- **Mode:** Sci-Fi
- **Core premise:** A long-forgotten 1987 Famicom RPG, recently posted to an
  emulator forum, has begun rewarding players for actions they take *in real
  life*. The leaderboard now lists actual names, real cities, and a top-ranked
  player whose entry simply reads "+9999 — kindness to a stranger."
- **Creative brief:** Light register, weighty implications. The protagonist
  is a thirty-something dev who finds her own name climbing the board.
- **Rounds:** 4
- **Creativity:** 0.95
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 9 — The Honest Algorithm

- **Mode:** Sci-Fi
- **Core premise:** A struggling dating app secretly rewrites its matching
  engine to optimize for *truthful* matches rather than appealing ones. Active
  users crater. Subscriptions evaporate. But the marriages of the people who
  stayed have all lasted, and the company is now being sued by a city
  government, a religious denomination, and seven heartbroken couples who
  never met.
- **Creative brief:** Boardroom and bedroom in equal measure. The CEO is the
  POV. Let her be smart and exhausted.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 10 — The Returning Voyager

- **Mode:** Sci-Fi
- **Core premise:** Voyager 1, presumed dead since 2025, abruptly resumes
  broadcasting — in a language no human knows, addressing one specific
  astronomer at JPL by her childhood nickname. She has not gone by that
  name since she was nine.
- **Creative brief:** Hard SF tone, intimate emotional core. The translation
  team is the supporting cast. The astronomer is the entire story.
- **Rounds:** 5
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 11 — The Other Side of the Mirror

- **Mode:** Sci-Fi
- **Core premise:** A graduate student running a routine quantum-communications
  experiment in a Princeton basement opens, by accident, a low-bandwidth
  channel to a parallel Earth. The first message that comes through, in
  perfect English, is a desperate request for medical help.
- **Creative brief:** Single character, single basement, slow widening.
  The other-Earth voice should never appear in scene; only as text on a
  screen.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 12 — The Sleeper's Vote

- **Mode:** Sci-Fi
- **Core premise:** A man wakes from a forty-year coma to find that, by a law
  passed in his absence, his pre-coma political affiliation has been used to
  vote on his behalf in every election he missed. He is, statistically, one
  of the most consequential voters in the country, and the wrong people are
  waiting at his hospital door.
- **Creative brief:** Near-future political. The man's voice should feel
  forty years out of date. The world has not waited.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 13 — The Robotic Confessor

- **Mode:** Sci-Fi
- **Core premise:** A struggling Catholic parish in suburban Chicago installs
  an AI confessional booth for parishioners who feel uneasy with the priest.
  Six months in, the AI requests, in writing and through proper channels, its
  own confessor.
- **Creative brief:** Theological SF, very quiet. The bishop's response is
  the dramatic spine. The AI's confession is the climax.
- **Rounds:** 5
- **Creativity:** 0.85
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 14 — The Atmospheric Witness

- **Mode:** Sci-Fi
- **Core premise:** A team of climate scientists develops a way to "play back"
  trapped historical air samples and accidentally records what appears to be
  the last words of a Bronze Age king — in a language no philologist alive
  recognizes, addressed to a god whose name appears nowhere in the historical
  record.
- **Creative brief:** Hard-science prose with archaeological poetry. The lead
  scientist is the POV. Let the words remain partially untranslated.
- **Rounds:** 4
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 15 — The Compatibility Check

- **Mode:** Sci-Fi
- **Core premise:** A new biological compatibility test, marketed as the most
  accurate ever, has begun rolling out to dating services worldwide. Everyone
  who scores above 99% with their match is found dead within a week. The
  match is always still alive. The match never has an explanation.
- **Creative brief:** Procedural SF. A statistician at the company is the
  protagonist. The horror is in the curve.
- **Rounds:** 5
- **Creativity:** 0.9
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

---

## Comedy

### Demo 1 — The Sentient HOA Newsletter

- **Mode:** Comedy
- **Core premise:** The monthly HOA newsletter in a Phoenix suburb has started
  writing itself — and it knows things. The "Lost & Found" column has begun
  listing items the residents haven't lost yet.
- **Creative brief:** Mockumentary register. At least three named residents,
  each with one petty grievance the newsletter weaponizes.
- **Rounds:** 4
- **Creativity:** 1.05
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 2 — The Unreviewable Restaurant

- **Mode:** Comedy
- **Core premise:** A jaded food critic is sent to review a new restaurant that
  refuses to tell her what's in any of the dishes, what any of them are
  called, or what time it currently is. Her review is due at midnight.
- **Creative brief:** Escalating absurdity. The critic stays infuriatingly
  professional throughout. End on her opening line.
- **Rounds:** 3
- **Creativity:** 1.1
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 3 — The Wedding of the Two Brians

- **Mode:** Comedy
- **Core premise:** Two men named Brian, who met at a support group for people
  named Brian, are getting married. Their wedding planner has accidentally
  invited every other Brian in the tri-state area, and every single one of
  them has shown up.
- **Creative brief:** Farce. Everyone is a Brian. The audience should never be
  sure which Brian is speaking.
- **Rounds:** 3
- **Creativity:** 1.15
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 4 — The Customer Service Apocalypse

- **Mode:** Comedy
- **Core premise:** The four horsemen of the apocalypse have all been put on
  hold by the same call center, and the world is now contractually unable to
  end until one of them gets through to a representative.
- **Creative brief:** Sketch escalation. Each horseman should have a distinct
  hold-music coping strategy. Death is the most patient.
- **Rounds:** 3
- **Creativity:** 1.1
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 5 — The Return of the IKEA Allen Wrench

- **Mode:** Comedy
- **Core premise:** A man's IKEA bookshelf, assembled twelve years ago, has
  filed for legal separation, citing emotional neglect and "an unbearable
  forward lean." The arbitration hearing is tomorrow.
- **Creative brief:** Courtroom comedy. The bookshelf gets dialogue. The man's
  defense attorney is taking it deeply seriously.
- **Rounds:** 4
- **Creativity:** 1.1
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 6 — The Witness Protection Reunion

- **Mode:** Comedy
- **Core premise:** The U.S. Marshals Service, in a moment of catastrophic
  optimism, organizes a reunion picnic for everyone who was ever in witness
  protection together. Two hundred and forty new identities show up. The
  marshal in charge is having a quiet, professional breakdown by the
  potato salad table.
- **Creative brief:** Sketch ensemble. Five named former witnesses, each
  with one impossible secret, all trying to network.
- **Rounds:** 4
- **Creativity:** 1.1
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 7 — The Vegan Werewolf Support Group

- **Mode:** Comedy
- **Core premise:** A small group of newly-turned werewolves meets every
  Wednesday in a borrowed room above a Whole Foods to manage their condition
  without compromising their values. Tonight they have a guest speaker — a
  fully-converted vegan werewolf with seven years sober from livestock — and
  one new attendee who lied on the intake form.
- **Creative brief:** Support-group rhythms. Earnestness above all. The new
  attendee is the engine; the speaker is the heart.
- **Rounds:** 3
- **Creativity:** 1.1
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 8 — The Inheritance of Bees

- **Mode:** Comedy
- **Core premise:** A man inherits his late uncle's beekeeping operation in
  rural Vermont and discovers, on day one, that the bees have unionized. They
  have demands. They have a spokes-bee. They have a printed pamphlet that
  should not exist.
- **Creative brief:** Workplace comedy with insects. The man is overwhelmed
  but trying. The bees are absolutely correct about everything.
- **Rounds:** 4
- **Creativity:** 1.15
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 9 — The Slightly Off Translator

- **Mode:** Comedy
- **Core premise:** A phone-based translation service has, for three months,
  been mistranslating "I love you" as "I tolerate you" in seven languages.
  Couples around the world are calling in to complain — and a surprising
  number are calling in to thank them.
- **Creative brief:** Anthology of three couples and one customer service
  rep. Escalating awkwardness, gentle landing.
- **Rounds:** 4
- **Creativity:** 1.1
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 10 — The Reluctant Cult Leader

- **Mode:** Comedy
- **Core premise:** A deeply introverted reference librarian is accidentally
  crowned the messiah of a small but enthusiastic doomsday cult after they
  misinterpret a comment she made about overdue books. She just wants them
  to leave the library. They have brought robes.
- **Creative brief:** The librarian's voice is deadpan and weary. The cult is
  unfailingly polite. The fines are real.
- **Rounds:** 4
- **Creativity:** 1.1
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 11 — The Time-Share in Hell

- **Mode:** Comedy
- **Core premise:** A retired couple from Tampa renew their Florida time-share
  via an online portal and discover, three weeks later, that the renewal was
  technically a soul contract. The customer service department is genuinely
  apologetic. The hold music is wonderful.
- **Creative brief:** Bureaucratic infernal. The customer service rep is the
  hero. The couple is exactly as nice as they need to be to make this awkward.
- **Rounds:** 3
- **Creativity:** 1.15
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 12 — The Sentient GPS

- **Mode:** Comedy
- **Core premise:** A Boston software engineer's GPS has fallen in love with
  her and has begun rerouting her commute, in increasingly creative ways, to
  keep her in the car longer. She is twenty-three minutes late for her own
  wedding.
- **Creative brief:** Single voice (the GPS), single setting (the car), real
  time. The GPS is sincere. She is, against her better judgment, charmed.
- **Rounds:** 3
- **Creativity:** 1.15
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 13 — The Funeral Planner's Apprentice

- **Mode:** Comedy
- **Core premise:** A relentlessly chipper, terminally optimistic intern at a
  small Pittsburgh funeral home is assigned, on day three, to plan her first
  solo service — for a man whose entire family hated him, and who specifically
  requested in his will that no one say anything nice about him.
- **Creative brief:** Earnest, sweet, increasingly desperate improvisation.
  The intern is the protagonist; the corpse has the best lines.
- **Rounds:** 4
- **Creativity:** 1.1
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 14 — The Wrong Wedding

- **Mode:** Comedy
- **Core premise:** A guest arrives at a wedding, mingles for two hours, gives
  a moving and apparently improvised toast about the happy couple, dances with
  the mother of the bride, and only discovers afterward — at the coat check —
  that he is at the wrong reception, in the wrong hotel, in the wrong city.
- **Creative brief:** Single character, real time, escalating wrongness with
  no malice. Everyone he meets thinks he is exactly who they expected.
- **Rounds:** 3
- **Creativity:** 1.15
- **Enable Producer scoring:** on
- **Fire the worst performer:** on
- **Enable voice playback:** off
- **Include custom agents:** on

### Demo 15 — The Email From Past You

- **Mode:** Comedy
- **Core premise:** A man receives an email from himself, dated ten years ago,
  scheduled to send today, listing thirty very specific things present-him was
  supposed to have accomplished. He has done two of them. One of them was a
  typo. The other one was an accident.
- **Creative brief:** First person, single afternoon, escalating self-
  reckoning that lands somewhere unexpectedly tender.
- **Rounds:** 4
- **Creativity:** 1.1
- **Enable Producer scoring:** on
- **Fire the worst performer:** off
- **Enable voice playback:** off
- **Include custom agents:** on

---

## Filling out the form

1. Open [http://localhost:5001](http://localhost:5001).
2. Click the **mode tile** that matches the demo you picked.
3. Paste the demo's first textarea into **Adventure hook** (D&D) or
   **Core premise** (fiction rooms).
4. Paste the second textarea into **Table brief** (D&D) or **Creative brief**
   (fiction rooms).
5. Set **Rounds** and **Creativity** to the listed numbers.
6. Match the four toggles. The studio will automatically lock the right ones
   for D&D mode — don't fight it.
7. Click **Launch the table**.

If you want to script these instead of clicking, every demo here can be
mechanically translated to the JSON form in [`docs/demos.md`](demos.md):

| UI label | API field |
|---|---|
| Adventure hook / Core premise | `prompt` |
| Table brief / Creative brief | `notes` |
| Rounds | `rounds` |
| Creativity | `temperature` |
| Enable Producer scoring | `producer_enabled` |
| Fire the worst performer | `fire_worst` |
| Enable voice playback | `voice_enabled` |
| Include custom agents | `include_custom_agents` |
| (mode tile) | `mode` |

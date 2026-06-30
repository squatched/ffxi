# CLAUDE.md — FFXI Data

This directory stores reference data for FFXI game mechanics, primarily to answer the question:
**"Given a job and a level, what is the complete set of actions available to that character?"**

Actions include job abilities (JAs), magic spells, and weapon skills. Weapon skills are derived
by combining the job's weapon skill rank with the rank cap table and the weapon skill files.

Subjob actions are computed at query time: apply the same query to the subjob at `floor(main_level / 2)`.

---

## Directory Structure

```
data/
  CLAUDE.md                    # this file
  weapon_rank_caps.yml         # shared: rank × level → max skill cap (breakpoints)
  weapon_skills/
    Sword.yml                  # all sword weapon skills with skill requirements
    Dagger.yml
    Staff.yml
    ...                        # one file per weapon type
  magic/
    white_magic.yml            # shared: per-job unlock levels for WHM/RDM/PLD/SCH
    black_magic.yml            # shared: per-job unlock levels for BLM/RDM/SCH/DRK
    ninjutsu.yml               # NIN exclusive
    songs.yml                  # BRD exclusive
    blue_magic.yml             # BLU exclusive
    geomancy.yml               # GEO exclusive
    summoning.yml              # SMN avatar unlock levels
    blood_pacts.yml            # SMN blood pacts by avatar (rage/ward)
  jobs/
    RDM.yml                    # abilities, magic category list, weapon ranks
    WAR.yml
    SMN.yml                    # magic: [summoning, blood_pacts]
    BST.yml                    # + jug_pets section
    ...                        # one file per job
```

---

## Job Files — `jobs/JOB.yml`

All jobs share the same base structure. Special sections for SMN and BST are documented below.

```yaml
job: RDM
name: Red Mage

abilities:
  - name: Convert
    level: 1
  - name: Chainspell     # 2-hour; always include even though it's level 1
    level: 1
  - name: Composure
    level: 50
  - name: Saboteur
    level: 75
    notes: "optional notes for unusual cases"

magic:
  - white_magic
  - black_magic
  # only list categories the job actually has
  # spell data lives in data/magic/<category>.yml

weapons:
  Sword: B
  Dagger: B
  Club: D
  Archery: D
  # only list weapon types the job can equip
  # rank values: A+, A, B+, B, C+, C, D, E
  # verify against bg-wiki.com/ffxi/Skill_Caps/Job_Name before entering
```

### Magic Category Keys (canonical snake_case)

| Key | In-game label |
|-----|---------------|
| `white_magic` | White Magic |
| `black_magic` | Black Magic |
| `songs` | Songs |
| `ninjutsu` | Ninjutsu |
| `summoning` | Summoning Magic |
| `blue_magic` | Blue Magic |
| `geomancy` | Geomancy |

Only list categories the job actually has. Do not add empty categories.

### SMN — Additional `blood_pacts` Section

Blood Pacts are level-gated per avatar and triggered with `/pet`. Include them alongside the
standard sections. The avatar must also appear in `magic.summoning` to be usable.

```yaml
# jobs/SMN.yml (excerpt)
magic:
  - summoning
  - blood_pacts
# Avatar data lives in data/magic/summoning.yml
# Blood pact data lives in data/magic/blood_pacts.yml
```

Query: filter blood_pacts.yml pacts by `level ≤ target_level`, restricted to avatars available
at that level per summoning.yml. The `notes: "merit"` flag on L75 elemental rage pacts indicates
merit investment is required. The `notes: "2-hour"` flag marks Astral Flow pacts.

### BST — Additional `jug_pets` Section

A jug's unlock level is the level gate for both calling the pet AND using all its abilities —
they are all available simultaneously. Abilities are listed flat inside each jug entry.

Charmed monster abilities are mob-specific and not enumerable; they are out of scope.

```yaml
# jobs/BST.yml (excerpt)
jug_pets:
  - name: Sheep Familiar
    level: 1
    family: Sheep
    abilities:
      - Lamb Chop
      - Sheep Song
      - Rage
  - name: Crab Familiar
    level: 10
    family: Crab
    abilities:
      - Big Scissors
      - Bubble Shower
      - Bubble Curtain
```

### PUP — No Special Section

PUP automaton behavior is fully autonomous — the player has no direct trigger for specific
automaton spells or weapon skills. Maneuvers (all 8 elements) and deployment commands
(Activate, Deactivate, Repair, Maintenance, Overdrive) are standard JAs and go in `abilities`.
Automaton head/frame/attachment data is out of scope for this model.

---

## Magic Catalog Files — `magic/CATEGORY.yml`

Magic data lives in separate catalog files rather than embedded in job files, avoiding duplication
across the jobs that share white/black magic. Job files list which categories they have via a
`magic:` key; the catalog files hold the actual spell data.

### Job-Exclusive Categories

For magic types tied to a single job (songs, ninjutsu, blue_magic, geomancy, summoning, blood_pacts),
spells have a single `level:` field plus optional flags:

```yaml
# magic/ninjutsu.yml
magic: ninjutsu
spells:
  - name: Utsusemi: Ichi
    level: 12
  - name: Katon: Ni
    level: 40
```

### Series Links (`prev` / `next`)

Spells that form upgrade series carry `prev` and `next` fields pointing to adjacent members
by name. These are present in `white_magic.yml`, `black_magic.yml`, `ninjutsu.yml`, and
`songs.yml`. They are NOT present in `geomancy.yml` (Indi-/Geo- variants are used
simultaneously, not as upgrades) or `blue_magic.yml` / `blood_pacts.yml`.

```yaml
- name: Cure II
  WHM: 14
  RDM: 28
  prev: "Cure"
  next: "Cure III"
```

Use these to determine which spells in the available set are superseded by a higher-tier
version the character also has access to. A spell with a `next` whose level is also ≤
target_level is effectively replaced for most purposes.

**blue_magic** adds two boolean flags:
- `main_job_only: true` — spells level 60+ are unavailable via /BLU subjob
- `unbridled_learning: true` — spell requires Unbridled Learning to be active when cast

### Shared Categories (white_magic / black_magic)

These are shared across multiple jobs at different unlock levels. Each spell entry uses inline
job keys rather than a nested `levels:` map:

```yaml
# magic/white_magic.yml
magic: white_magic
spells:
  - name: Cure
    WHM: 1
    PLD: 5
    RDM: 3
    SCH: 5
  - name: Cure V
    WHM: 61     # WHM only — omit a job if they cannot learn the spell
```

Jobs with `white_magic`: WHM, RDM, PLD, SCH
Jobs with `black_magic`: BLM, RDM, SCH, DRK

`black_magic` covers all three in-game subcategories (elemental, dark, enfeebling) as a flat
list. Per-job level data is authoritative; the in-game subcategory distinction is not stored.

### Summoning Magic

`summoning.yml` lists avatars with their unlock level and acquisition type. `blood_pacts.yml`
lists blood pacts organized by avatar name, then `rage:` / `ward:` sublists, each pact having
a `level:` and optional `notes:`. Query: load the avatar from `summoning.yml` at `level ≤
target_level`, then filter its pacts by `level ≤ target_level`.

### Job File Magic Reference

In each job file, the `magic:` key lists the category names the job has access to:

```yaml
magic:
  - white_magic
  - black_magic
```

Jobs with no magic (WAR, MNK, THF, DRG, SAM, RNG, COR, PUP, DNC, RUN) have no `magic:` key.

---

## Weapon Skill Files — `weapon_skills/WeaponType.yml`

One file per weapon type. Weapon skills are job-agnostic; any job that reaches the required
skill cap can use them (subject to acquisition type).

```yaml
weapon: Sword

skills:
  - name: Fast Blade
    skill: 5
    acquisition: automatic

  - name: Burning Blade
    skill: 50
    acquisition: automatic

  - name: Red Lotus Blade
    skill: 100
    acquisition: automatic

  - name: Seraph Blade
    skill: 150
    acquisition: quest
    notes: "Walkure Sagas quest"

  - name: Savage Blade
    skill: 240
    acquisition: automatic

  - name: Sanguine Blade
    skill: 300
    acquisition: automatic
    jobs: [WAR, RDM, PLD, DRK, BLU, RUN]
    notes: "main or sub"

  - name: Requiescat
    skill: 357
    acquisition: merit
    jobs: [WAR, RDM, PLD, DRK, SAM, BLU, COR, RUN]
```

`acquisition` values:
- `automatic` — unlocks when skill cap reaches the required value
- `quest` — requires completing a quest; include `notes` naming the quest
- `merit` — requires merit point investment; always at skill 357; most have `jobs` restrictions
- `weapon_specific` — tied to a specific legendary weapon (Relic/Empyrean/Mythic/Prime/Ergon/Aeonic/Campaign); omit `skill`; include `notes` naming the weapon(s)

Job restrictions use the optional `jobs` field and can appear with any acquisition type. When omitted, any job that can equip the weapon and reach the required skill level can use it — do not add a `jobs` field just to document which jobs happen to have that weapon type.

Only add `jobs` when some jobs with that weapon are explicitly excluded: e.g. Dancing Edge is THF/DNC only even though RDM and NIN also have dagger skill.

Include `notes: "main only"` when a quest or merit WS is explicitly unavailable to that job via subjob.

Some weapon skills have multiple unlock paths (e.g. quest AND a weapon-specific alternative). These appear as two separate entries with the same `name` — one per path. The in-game command is identical regardless of how it was unlocked.

Per-job unlock levels (as shown in the "level" column on wiki weapon skill pages) are **derived**, not stored. Given a job and level: look up the job's rank for this weapon type, then find the lowest level at which `caps[level - 1] ≥ skill`. Do not add a `job_levels` or `job_skills` field.

File naming: multi-word weapon types use underscores (`Great_Sword.yml`, `Hand_to_Hand.yml`).
The `weapon:` field inside each file uses the in-game spelling with spaces (`weapon: Great Sword`).
Throwing has no weapon skills and has no file.

Note: some skills marked `automatic` at skill 357 are merit-upgradeable but do not require merits
to unlock — these are noted with `notes: "merit upgradeable (not required)"`.

---

## Weapon Rank Cap Table — `weapon_rank_caps.yml`

Stores the full 99-level cap array per canonical tier. `caps[level - 1]` gives the max
skill cap at that level (e.g. `caps[74]` = cap at level 75).

### Canonical Tiers

Wiki job pages use inconsistent rank labels — the same letter grade can map to different
cap tables on different job pages. Canonical tiers are defined by their L75 cap value.
Always verify a job's tier by matching cap values, not wiki letter labels, using:
`bg-wiki.com/ffxi/Skill_Caps/Job_Name`

| Tier | L75 | L99 | Example weapons |
|------|-----|-----|-----------------|
| A+   | 276 | 424 | WAR Great Axe, SAM Great Katana |
| A    | 269 | 417 | WAR Axe, THF Dagger |
| B+   | 256 | 404 | WHM Club, WAR Great Sword/Scythe |
| B    | 250 | 398 | WAR Sword/Staff, RDM Sword/Dagger |
| B-   | 240 | 388 | SAM Polearm, WAR Dagger/Polearm |
| C+   | 230 | 378 | WHM Staff, THF Marksmanship |
| C    | 225 | 373 | DRK Dagger |
| C-   | 220 | 368 | THF Archery, DRK Club |
| D    | 210 | 334 | RDM Club/Archery |
| E    | 200 | 300 | THF H2H/Club, SAM Dagger/Club |

All 10 tiers confirmed across multiple job pages.

```yaml
# excerpt showing format; see weapon_rank_caps.yml for full arrays
tiers:
  "A+":  # L75=276, L99=424 | WAR Great Axe, SAM Great Katana
    caps: [6, 9, 12, 15, ...]  # 99 values
```

---

## Deriving Available Weapon Skills

Given a job and level:

1. For each weapon type in the job's `weapons` map, read the tier (e.g. `Sword: B`)
2. Look up `weapon_rank_caps.tiers[tier].caps[level - 1]` to get the skill cap at that level
3. Load the corresponding `weapon_skills/WeaponType.yml`
4. Include all skills where `skill ≤ cap`, subject to acquisition rules:
   - `automatic` — always included if skill requirement is met
   - `quest` — include in the list but flag as quest-gated; the player must have completed it
   - `merit` — include only if skill ≥ 357; flag as merit-gated
   - `weapon_specific` — out of scope for level-based queries; requires specific weapon equipped
5. For any skill with a `jobs` field, also check that the current job appears in the list

---

## Deriving Available Magic Spells

Given a job and level:

1. Check the job's `magic:` list. If absent, the job has no castable magic.
2. For each category in that list, load `data/magic/<category>.yml`.
3. **Shared categories** (`white_magic`, `black_magic`): for each spell, check whether the job
   key exists on that spell entry. If it does, include the spell if `spell[job] ≤ target_level`.
4. **Exclusive categories** (`ninjutsu`, `songs`, `blue_magic`, `geomancy`): include each spell
   if `spell.level ≤ target_level`.
   - For `blue_magic`, if the job is used as a **subjob**, exclude any spell with `main_job_only: true`.
   - `unbridled_learning: true` spells require the Unbridled Learning JA to be active — flag them
     as conditionally available rather than unconditionally available.
5. **Summoning** (`summoning` + `blood_pacts`):
   - Available avatars: filter `summoning.yml` avatars by `level ≤ target_level`.
   - For each available avatar, filter its `blood_pacts.yml` pacts by `level ≤ target_level`.
6. For **subjob magic**: apply steps 1–5 to the subjob at `floor(main_level / 2)`.

---

## Out of Scope

- **Passive traits** (Attack Bonus, Magic Attack Bonus, etc.) — not player-triggered
- **Charmed BST mob abilities** — mob-specific, not enumerable
- **PUP automaton autonomous abilities** — determined by head/frame/attachments, not triggered by the player
- **Gear-conditional abilities** — anything that requires equipping a specific item (e.g. some PUP attachments enabling new behaviors)

---

## Known Gaps (Post-99 Content)

This data set is complete for levels 1–99. Post-99 progression systems are not yet modeled
because the player this data is built for hasn't reached level 99 yet. When that changes,
the following systems will need a pass:

### Job Points
Job Points (JP) are earned at level 99 by continuing to fight. They primarily upgrade
existing abilities (passive enhancements to Chainspell, Astral Flow, etc.), but a small
number of jobs unlock **new actions** via JP that have no level equivalent:

- **BRD**: Threnody II series — already flagged with `notes: "Job Points"` in `songs.yml`
- **Other jobs**: likely have JP-exclusive abilities; not yet researched

To model JP-unlocked actions, add `notes: "job_points"` to any ability or spell that
requires JP investment (analogous to the existing `notes: "merit"` convention).

### Master Levels (ML 1–50)
Master Levels raise combat and magic skill caps above their level-99 values, potentially
pushing weapon skill access past what `weapon_rank_caps.yml` currently shows for L99.
No new JAs or spells unlock from ML progression — only extended skill caps.

To model this, the `caps` arrays in `weapon_rank_caps.yml` would need to be extended
beyond index 98 (level 99), or a separate ML cap table added.

### Merit Points
Already fully modeled — see `notes: "merit"` entries throughout job files, blood_pacts.yml,
and weapon skill files. No further work needed here.

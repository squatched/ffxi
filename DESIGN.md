# FFXI Macro System — Design

This document captures the design of the next-generation macro generation system. The existing
`macros/JOB.yml` hand-crafted files are the current source of truth; this design replaces them
with a structured spoke-definition format that enables automatic generation for any job/subjob/
level combination.

---

## Architecture

Three layers produce a final importable macro YAML:

```
data/jobs/JOB.yml            game data: abilities, magic, weapon ranks, unlock levels
macros/spokes/JOB.yml        spoke definitions: groups, actions, priorities       ← NEW
characters/NAME/manifest.yml  per-character config: job/level/subjob + book pins  ← NEW
scripts/gen_macros.py        generator: combines all layers into a macro YAML
out/NAME.yml                 full character macro set; one macromog import         ← CHANGES
macros/JobsHub.yml           generated from manifest (no longer hand-crafted)     ← CHANGES
```

---

## Group Types

Every set in a job book is one of three types. See `macros/AGENTS.md` for full nav conventions.

### Hub
The player's home set — the hub is where you live between actions; you navigate to spokes as needed
and return. Hub actions are the most constantly-needed: JAs, reactive self-buffs, and any spell
you reach for without wanting to navigate first. Spells are valid hub actions. Contract:
- Ctrl+0 = 2-hour (always, on every hub — primary and secondary)
- Alt+0 = JobsHub
- Alt slots = full nav to all other groups (hubs, cores, spokes)
- Alt+1 on Hub A = Hub B (toggle); Alt+1 on Hub B = Hub A (toggle)
- At most **two hubs** per job. Primary = pin:1. Secondary = pin:2.
- If a hub overflows to a 2nd set: Ctrl+0 = 2-hour repeated; Ctrl+1-9 duplicated from page 1
  (or holds overflow JAs if page 1 was full); toggle on Alt+9 (Alt+0 is reserved for JobsHub)

### Core
A content set (spells/skills) that must be reactively reachable from any other set without first
returning to the hub. Alt slot assignment is driven by `type:` and file order: hubs fill Alt+1 and Alt+2 in file order,
then cores fill the next available slots in file order. On a single-hub job the first core lands
on Alt+2; on a dual-hub job it lands on Alt+3. Nav back to hub(s) only — no full
spoke nav, no Ctrl+0 = 2-hour. Use sparingly: each core costs one Alt slot on every other set.
If a core overflows: Alt+0 toggles between pages.

### Spoke
A content set reachable only from the hub. Nav back to hub(s) on Alt+1 (Alt+2 if dual-hub).
Not pinned. If a spoke overflows: Alt+0 toggles between pages.

---

## Action Priority

Controls slot assignment within a group's set(s):

| Priority | Target slots | Notes |
|---|---|---|
| `high` | Ctrl+1-5 | Most-used actions; prime real estate |
| `mid` | Ctrl+6-0 | Used but not primary |
| `low` | Remaining Alt slots (after nav/pins), then overflow to 2nd set | Rarely used but worth having |

Ctrl+0 on hubs is always reserved for the 2-hour regardless of priority assignment.

**Within a priority tier, file order determines slot order.** Main job actions should be
defined first so their button positions remain stable.

When a subjob contributes actions to a matching group, the subjob group is placed **adjacent**
as a separate set — actions are not interleaved with the main job's group. Priority levels
are preserved in the schema as a forward-looking signal: if behavior ever changes to allow
mixing actions within the same set, priority already provides the information needed to do it
correctly without re-deriving anything.

---

## Spoke Definition Schema (draft)

Each job has a `macros/spokes/JOB.yml` defining its groups independent of layout:

### Top-level spoke fields

| Field | Required | Notes |
|---|---|---|
| `job` | yes | Job abbreviation (`DRG`, `RDM`, …) |
| `name` | yes | Full human-readable job name (`Dark Knight`) |
| `label` | no | ≤8-char button name for the JobsHub. Defaults to `_abbrev(name)` (spaces stripped, Roman numerals → digits, truncated). Set explicitly when the default is unreadable: `DrkKnght` for Dark Knight. |
| `ws_rank_cutoff` | no | See job-level parameters below. |
| `hubs` | yes | List of hub definitions. |
| `groups` | yes | List of group definitions. |

```yaml
job: RDM
hubs:
  - name: main
    pin: 1
    actions:
      - name: Convert
        priority: high
      - name: Chainspell       # 2-hour; generator places this on Ctrl+0 automatically
        priority: high
      - name: Composure
        priority: high
      - name: Saboteur
        priority: mid

groups:
  - name: nukes
    type: spoke
    label: "Nukes"
    actions:
      - name: Fire VI
        priority: high
      - name: Blizzard VI
        priority: high
      # generator fills best available tier per level
      # series: Fire I→II→III→IV→V→VI — only highest available placed here

  - name: healing
    type: core
    pin: 3
    label: "Healing"
    actions:
      - name: Cure IV
        priority: high
      - name: Cure III
        priority: mid
```

Group names must use the canonical taxonomy defined in `macros/AGENTS.md`. The taxonomy is
organized by **usage context**, not magic type — `nuking` contains Holy and Katon alongside
Fire/Blizzard, because that's how you reach for them. Actions are **cross-cutting**: the same
action may appear in multiple groups if it's genuinely used in different contexts. Tractor, for
example, belongs in both `healing` (Raise workflow) and `field` (door trick in Qufim).
Deduplication when merging subjob groups applies within a group only — an action in group A
does not prevent it from appearing in group B.

### Job-level parameters

| Field | Default | Notes |
|---|---|---|
| `ws_rank_cutoff` | `"B-"` | Weapons at this rank or below have WS excluded. Set lower to include more weapons; `null` to include all. |

### 2-hour detection

The generator reads the job's 2-hour from the top-level `two_hour_ability:` field in
`data/jobs/JOB.yml`. This field is **required** — the generator errors if absent. The 2-hour
is **not** listed in the `abilities:` array; all 2-hours share the same implicit properties
(level 1, `<me>`, standard recast) so there is nothing unique to store there. The generator
places it on Ctrl+0 of every hub; the spoke definition does not reference it.

### Group fields

| Field | Required | Notes |
|---|---|---|
| `name` | yes | Canonical taxonomy name (`cc`, `enfeebling`, `ws_sword`, etc.) |
| `type` | yes | `hub`, `core`, or `spoke` |
| `family` | no | Merge family. Groups with the same family are candidates for merging into one set when combined content fits. `ws_*` groups are implicitly in family `ws` by prefix — no explicit declaration needed. Other families must be declared: `enfeebling` (covers `cc`+`enfeebling`+`dots`), `enhance` (covers `enhance_others`+`enhance_self`). File order among same-family groups determines merge order. |
| `label` | no | Display name for hub nav button. Derived from group name if omitted. |
| `actions` | yes | List of action entries (see Action fields below). |

### Action fields

| Field | Required | Notes |
|---|---|---|
| `name` | yes | Spell/ability name as it appears in game data |
| `priority` | yes | `high`, `mid`, or `low` |
| `exact` | no | When `true`, use exactly this spell name — never upgrade to a higher tier. Slot is empty if the spell isn't available at this level. Use this when you genuinely want both `Raise` and `Raise II` as separate buttons (mana efficiency). Default: `false` (series resolves to highest available tier). |
| `max_tier` | no | Hard cap on tier placed (e.g. `max_tier: "Cure IV"`) |
| `sub_tier` | no | N tiers below the current max available. Slot is empty until enough tiers exist. E.g. `sub_tier: 2` with Cure IV available → Cure II; with only Cure II available → empty; once Cure III available → Cure I. |
| `position` | no | Override slot (e.g. `position: ctrl_0` for explicit placement) |
| `note` | no | Freeform; preserved in generated output as a comment |

---

## Subjob Handling

Given a main job at level N and subjob at floor(N/2):

1. Load main job's spoke definitions and filter actions to available at level N
2. Load subjob's spoke definitions and filter to available at floor(N/2)
3. For each subjob group:
   - If a matching group exists in the main job: place the subjob group **adjacent** to it
     (next set number). Deduplicate: skip any action already present in the main job's group.
   - If no matching group exists: add the subjob group as a new spoke (or core if flagged)
4. Nav is wired automatically. If a subjob group adds a new spoke, the hub gets a nav link to it.

Subjob groups inherit the main job's hub (they don't bring their own hub). The main job's 2-hour
always stays on Ctrl+0 of every hub; subjob 2-hours are not included (no 2-hour via subjob).

---

## Group Merging

Some taxonomy categories have sub-groups that can be merged into a single set when content
is sparse, or kept separate when content is large. The spoke file always defines the
fine-grained sub-groups; the generator decides merge vs. split at build time based on
whether the combined unique item count fits within the set's content slots (~18: 10 Ctrl
+ 8 usable Alt after hub/core nav). If it fits, one set is generated with one hub nav link.
If it doesn't, each sub-group becomes its own set and nav link.

### Enfeebling family (`cc` + `enfeebling` + `dots`)

Merge label: **Enfeebling**. Order when merged: cc first (most reactive), then enfeebling,
then dots. Cross-cutting items (e.g. Dia/Bio which are both dots and enfeebling) appear once.

### Enhance family (`enhance_others` + `enhance_self`)

Merge label: **Enhance**. Order when merged: enhance_others first (party buffs are more
reactive in group content), then enhance_self. Note that spells placed on the hub for
immediate access (e.g. Stoneskin, Blink on RDM) do not appear in enhance_self and are
not counted toward the merge threshold.

### Weapon skill family (`ws_<weapon>` groups)

Merge label: **Weapon Skills** (or **WS**). When merged, weapons are ordered by rank
descending (primary weapon first); within the same rank, file order determines placement.
Priority is consistent across merge and split — high-priority WS (endgame merit/relic/
empyrean) always land on Ctrl+1-5 in both states, so the muscle memory that matters is
stable through the transition. Early low-tier WS shift when sets split, but by that point
the player has moved on to better WS anyway.

---

## Overflow Rules

### Too many actions in a group (content overflow)
Generator creates a page 2 set for that group. Toggle on Alt+0 (spokes/cores) or Alt+9 (hubs).

### Too many groups for hub nav (nav overflow)
Generator creates a secondary hub (type: hub, unpinned) to hold the overflow spoke nav links.
Primary hub's last nav slot points to the secondary hub. Secondary hub's Alt+1 returns to
primary hub. Secondary hub also has Ctrl+0 = 2-hour and Alt+0 = JobsHub.

---

## Characters, Manifest, and Output

### Directory structure

```
characters/
  Valeria/
    manifest.yml       ← job configurations for this character
out/
  Valeria.yml          ← entire macro set; one macromog import (git-ignored)
```

One output file per character contains all books (JobsHub + all job books). Import with:

```sh
macromog import --char-name Valeria out/Valeria.yml
```

### manifest.yml

A list of configurations the builder should generate for this character. Books are assigned
in manifest order starting at 2 (book 1 = JobsHub always). Use the optional `book:` field
to pin a configuration to a specific slot; unpinned configs fill remaining slots in order.

```yaml
character: Valeria
configurations:
  - job: WAR
    level: 99
    book: 2            # pinned — WAR always in book 2
  - job: RDM
    level: 99
    subjob: WHM
    book: 6            # pinned — RDM/WHM always in book 6
  - job: RDM
    level: 99
    subjob: BLM        # unpinned — builder assigns next available slot
  - job: WHM
    level: 99
```

If a configuration needs more than 10 sets, the builder assigns the next available book
automatically and names the continuation book `RDM99WHM2`, `RDM99WHM3`, etc. in-game.

### Build warnings and errors

| Condition | Severity |
|---|---|
| Book assignment changed from previous build | Warn (muscle memory impact) |
| 35+ books occupied | Warn (headroom shrinking) |
| Book slots exhausted (>39 configs + spill) | Error (hard stop) |
| Pinned book conflicts with another config | Error |

### JobsHub (book 1)

Generated from the final book assignments — no longer hand-crafted. One nav link per
occupied book slot, labeled with the configuration (`RDM/WHM`, `WAR`, etc.), ordered by
book number. Multi-page if more than ~18 entries (Alt+0 toggle between pages — JobsHub
has no Alt+0 = self-reference, so Alt+0 is free for the page toggle).

The JobsHub is regenerated on every build. It is its own special case: pure nav, no group
type, no 2-hour, no spokes.

---

## Weapon Skill Policy

- Include WS for weapons with rank **B or higher** on the main job
- Exclude rank **B- and below** — not the job's primary weapon at endgame
- Always include weapon-specific WS (Relic/Empyrean/Mythic/Prime/Aeonic) regardless of rank
- WS groups are type `spoke`; priority reflects endgame usage:
  - `high`: merit, weapon-specific, and top automatic WS
  - `mid`: mid-tier automatic WS
  - `low`: low-tier automatic WS (still worth having a slot)

---

## Pre-Battle Spells (Magic Jobs) — TBD

Magic jobs need a set for pre-combat buffs previously excluded from all macros:
Protect/Shell/Reraise/Sneak/Invisible/Deodorize/Bar-spells/Teleports. These vary meaningfully
by job. Design: each magic job gets a pre-battle group (type: spoke or core TBD). Books 25-40
available for per-job extension books if needed.

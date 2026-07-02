# AGENTS.md — FFXI Macro System

This repo builds and generates in-game macro sets for FFXI (retail). It has three layers:
**game data** (what actions exist and when they unlock), **macro layouts** (what buttons do what),
and a **generator** that combines them to produce level-appropriate macro files.

Each subdirectory has its own `AGENTS.md` with schema details. This file covers the big picture.

---

## Directories

### `data/`
Game mechanics data. Answers: *given a job and level, what actions are available?*

- `jobs/JOB.yml` — each job's abilities, magic categories, and weapon skill ranks
- `magic/*.yml` — spell catalogs with per-job unlock levels; spells in the same upgrade chain (Cure → Cure II → … → Cure VI) are linked via `prev`/`next` fields
- `weapon_skills/*.yml` — weapon skills with skill point requirements
- `weapon_rank_caps.yml` — maps weapon rank (A+, B, C, …) × level → max skill cap

See `data/AGENTS.md` for full schemas and targeting conventions (`default_self`, `self_only`).

### `macros/`
Hub-and-spoke macro layouts. Two coexisting formats live here — see `macros/AGENTS.md` for the
full breakdown:
- `spokes/JOB.yml` — declarative layout (hubs/groups/actions + priority, no fixed addresses); what
  `scripts/gen_macros.py` actually reads today to build a per-character macro set.
- `JOB.yml` / `JOB.md` (this folder's root) — hand-authored, standalone L99-only macro sets at
  fixed book numbers, importable directly without the generator.

Both share the same hub-and-spoke conventions: a shared **JobsHub** links to each job's book; a
primary hub set holds always-up abilities and nav links to category sets (healing, nukes,
enfeebling, WS, etc.). See `macros/AGENTS.md` for hub types, button naming rules, nav conventions,
group taxonomy, and multi-page overflow.

### `characters/`
Per-character, per-player inputs (git-ignored — local to the player, not checked in):
- `NAME/manifest.yml` — which job/level/subjob combinations to generate for this character
- `custom.yml` (account-wide) and `NAME/custom.yml` (per-character) — player-authored macros
  (Mount, Trust, farming sets, etc.) layered onto the authoritative `spokes/` layouts

See `characters/AGENTS.md` for both schemas.

### `scripts/`
`gen_macros.py` — given a character (`characters/NAME/manifest.yml`), reads each configured job's
`macros/spokes/JOB.yml` layout and the game data from `data/`, then produces a filled macro YAML
where, for every job/level/subjob in the manifest:
- Each spell slot holds the best available tier at that level
- Multi-slot series slots (CureS / CureM / CureL) distribute available tiers with gaps — the lowest available tier fills the S slot, highest fills the L slot, never duplicating a spell
- Unavailable actions are dropped entirely; nav macros are always preserved
- Book/set addresses (including JobsHub) are allocated dynamically; anything that doesn't fit on one page spills to a second rather than being dropped

Output goes to `out/` by default. `coverage.py` audits a single `spokes/JOB.yml` against everything the job can actually do at a given level.

### `out/`
Generated macro files (git-ignored). Import with `macromog import --char-name NAME file.yml`.

---

## Key design principle

`macros/spokes/JOB.yml` is the **source of truth for layout**. The generator never adds buttons that aren't in the design (short of player-authored `characters/*/custom.yml` additions) — it only fills, downgrades, or removes them. This preserves muscle memory across levels: the same button always does the "same kind of thing," just with the best currently-available tier.

---

## Running the generator

```sh
python3 scripts/gen_macros.py NAME                     # reads characters/NAME/manifest.yml, writes out/NAME.yml
python3 scripts/gen_macros.py NAME --char Valeria       # import directly via macromog
python3 scripts/gen_macros.py NAME --out path/to/file.yml
```

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
Authoritative macro layouts, one per job (`WHM.yml`, `BLM.yml`, …). These are the **L99 designs** — hand-crafted, never auto-generated. Each file is a [macromog](https://github.com/blobfish/macromog)-importable YAML defining which book/set/button holds which action.

The system uses a hub-and-spoke layout: a shared **JobsHub** book (book 1) links to each job's book. Within a job, a primary hub set holds always-up abilities and nav links to category sets (healing, nukes, enfeebling, WS, etc.).

See `macros/AGENTS.md` for hub types, button naming rules, nav conventions, and the book index table.

### `scripts/`
`gen_macros.py` — given a job and level, reads the authoritative layout from `macros/` and the game data from `data/`, then produces a filled macro YAML where:
- Each spell slot holds the best available tier at that level
- Multi-slot series slots (CureS / CureM / CureL) distribute available tiers with gaps — the lowest available tier fills the S slot, highest fills the L slot, never duplicating a spell
- Unavailable actions are dropped entirely; nav macros are always preserved

Output goes to `out/` by default.

### `out/`
Generated macro files (git-ignored). Import with `macromog import --char-name NAME file.yml`.

---

## Key design principle

`macros/JOB.yml` is the **source of truth for layout**. The generator never adds buttons that aren't in the L99 design — it only fills, downgrades, or removes them. This preserves muscle memory across levels: the same button always does the "same kind of thing," just with the best currently-available tier.

---

## Running the generator

```sh
python3 scripts/gen_macros.py WHM 45           # writes out/WHM45.yml
python3 scripts/gen_macros.py WHM 45 --char Valeria   # import directly via macromog
python3 scripts/gen_macros.py WHM 45 --out path/to/file.yml
```

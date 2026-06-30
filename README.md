# FFXI Macro System

A hub-and-spoke macro system for FFXI (retail), with data-driven generation of level-appropriate macro sets.

## Structure

```
macros/      Authoritative macro layouts, one file per job (WHM.yml, BLM.yml, …)
data/        Game data — spell levels, job abilities, weapon skills
  jobs/        Per-job ability and weapon lists
  magic/       Spell catalogs with per-job unlock levels and upgrade chains
  weapon_skills/  Weapon skill catalogs with skill requirements
scripts/     Tools
  gen_macros.py  Generate a leveling macro set
out/         Generated output (git-ignored)
```

## How it works

`macros/JOB.yml` is the **authoritative layout** — the macro book designed for level 99, with all final-tier spells in their intended slots. This is never auto-generated; it's the source of truth for what each button does and why.

`data/` holds the game's rules: what spells exist, which jobs get them and at what level, how spells chain into upgrade series (Cure → Cure II → … → Cure VI), and weapon skill unlock thresholds.

`scripts/gen_macros.py` combines these: given a job and level, it takes the L99 layout and produces a macromog-importable YAML where:

- Each spell slot is filled with the best available tier at that level
- Multi-slot series (e.g. CureS / CureM / CureL) distribute available tiers low→high with gaps, so no tier is ever duplicated
- Unavailable spells, abilities, and weapon skills are dropped entirely
- Navigation macros are always preserved unchanged

The result lands in `out/` and can be imported with [macromog](https://github.com/blobfish/macromog).

## Generating a macro set

```sh
python3 scripts/gen_macros.py WHM 45          # writes out/WHM45.yml
python3 scripts/gen_macros.py WHM 45 --char Valeria  # import directly
```

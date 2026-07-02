# FFXI Macro System

A hub-and-spoke macro system for FFXI (retail), with data-driven generation of level-appropriate macro sets.

## Structure

```
data/        Game data — spell levels, job abilities, weapon skills
  jobs/        Per-job ability and weapon lists
  magic/       Spell catalogs with per-job unlock levels and upgrade chains
  weapon_skills/  Weapon skill catalogs with skill requirements
macros/      Hub-and-spoke macro layouts
  spokes/      Declarative per-job layout — what scripts/gen_macros.py reads
characters/  Per-character, per-player inputs (git-ignored)
  NAME/manifest.yml  Which job/level/subjob combos to generate for this character
scripts/     Tools
  gen_macros.py  Generate a character's full macro set
  coverage.py    Audit a spokes/JOB.yml against everything the job can actually do
out/         Generated output (git-ignored)
```

## How it works

`macros/spokes/JOB.yml` is the **authoritative layout** — a declarative list of hubs and groups
(no fixed book/set/button addresses) describing what each button does and why, for any job.

`data/` holds the game's rules: what spells exist, which jobs get them and at what level, how spells chain into upgrade series (Cure → Cure II → … → Cure VI), and weapon skill unlock thresholds.

`scripts/gen_macros.py` combines these with a character's `characters/NAME/manifest.yml` to produce a macromog-importable YAML where, for every job/level/subjob in the manifest:

- Each spell slot is filled with the best available tier at that level
- Multi-slot series (e.g. CureS / CureM / CureL) distribute available tiers low→high with gaps, so no tier is ever duplicated
- Unavailable spells, abilities, and weapon skills are dropped entirely
- Navigation macros are always preserved
- Book/set addresses (including JobsHub) are allocated dynamically; anything that doesn't fit on one page spills to a second rather than being dropped

The result lands in `out/` and can be imported with [macromog](https://github.com/blobfish/macromog).

## Generating a macro set

```sh
python3 scripts/gen_macros.py NAME                 # reads characters/NAME/manifest.yml, writes out/NAME.yml
python3 scripts/gen_macros.py NAME --char Valeria   # import directly via macromog
```

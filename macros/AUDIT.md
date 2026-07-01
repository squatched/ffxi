# Macro Audit

Systematically review each fleshed-out job macro against `data/` to verify:
1. **Accuracy** — targeting (`<me>` vs `<t>`), ability availability, correct names
2. **Completeness** — every available action has a slot (exceptions documented)

---

## Scope Decisions

### Weapon Skills
Exclude WS for weapon types with rank **B- or worse** on a given job. Rationale: B- caps at
388 (L99) and is never the job's primary weapon at endgame. DRG Staff (B-) is the canonical
example — excluded.

Weapon-specific WS (Relic/Empyrean/Mythic/Prime/Aeonic) are **always included** in WS sets,
regardless of how obscure — they occupy a slot in case the player acquires the weapon.

### Pre-Battle Spells (Magic Jobs) — Design TBD
Previously excluded from all macros: Protect/Shell/Reraise/Sneak/Invisible/Deodorize/Bar-spells/
Teleports. New plan: give magic-using jobs a dedicated pre-battle set (or book extension like
`RDM2` / `WHM2`) for these since they vary meaningfully by job.

Which jobs need a pre-battle set: WHM, RDM, BLM, SCH, GEO, BRD, SMN, NIN, PLD, DRK, RUN, BLU.
Books 25–40 are reserved — available for overflow or per-job extensions.

Open: finalize layout conventions before auditing magic jobs.

---

## Progress

| Job | Status | Issues found |
|-----|--------|--------------|
| DRG | Done | 3 (see below) |
| WAR | Pending | Set 2 (Defensive Hub) missing Ctrl+0 = Mighty Strikes (2-hour on all hubs) |
| MNK | Pending | |
| WHM | Pending | pre-battle set needed |
| BLM | Pending | pre-battle set needed |
| RDM | Pending | pre-battle set needed |
| THF | Pending | |
| PLD | Pending | pre-battle set needed |
| DRK | Pending | pre-battle set needed |
| BST | Pending | |
| BRD | Pending | pre-battle set needed |
| RNG | Pending | |
| SAM | Pending | |
| NIN | Pending | pre-battle set needed |
| SMN | Pending | pre-battle set needed |
| BLU | Pending | pre-battle set needed |
| COR | Pending | |
| PUP | Pending | |
| DNC | Pending | |
| SCH | Pending | pre-battle set needed |
| GEO | Pending | pre-battle set needed |
| RUN | Pending | pre-battle set needed |

---

## DRG — Done

### Data fixes (`data/jobs/DRG.yml`)
- **High Jump**: added `self_only: false` — targets enemy `<t>` in-game, was incorrectly
  defaulting to `<me>` (job default is `abilities_default_self: true`)

### Macro fixes (`macros/DRG.yml`, `macros/DRG.md`)
- **Set 3 Ctrl+6**: Added Thunder Thrust (`ThunThrt`) — skill 30, automatic
- **Set 3 Ctrl+7**: Added Skewer — skill 200, DRG-only automatic
- **Set 3 Ctrl+8**: Added Diarmuid — weapon_specific (Prime: Gae Buide)

### Additional fixes (post-review)
- **Steady Wing**: confirmed real, unlocks L95; added to `data/jobs/DRG.yml`
- Added `wyvern_commands:` section to `data/jobs/DRG.yml` covering Smiting Breath, Restoring
  Breath, and Steady Wing — previously these had no data representation at all
- Note: `/ja` and `/pet` are interchangeable in macros; no distinction needed
- Note: Smiting/Restoring Breath availability depends on subjob type (melee vs mage), not just
  level; modeled as L1 with a note

### Open
None.

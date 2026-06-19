# FFXI Macros

A hub-and-spoke macro system for all FFXI (retail) jobs — consistent button layout, scalable to level 99, designed to build transferable muscle memory across jobs.

Based on [The Hub System by Sekhmet](https://ffxiclopedia.fandom.com/wiki/The_Hub_System_of_Macro_Management_a_guide_by_Sekhmet).

---

## Table of Contents

### Navigation
- [JobsHub](JobsHub.md)

### Base Jobs
- [WAR — Warrior](WAR.md)
- [MNK — Monk](MNK.md)
- [WHM — White Mage](WHM.md)
- [BLM — Black Mage](BLM.md)
- [RDM — Red Mage](RDM.md)
- [THF — Thief](THF.md)
- [PLD — Paladin](PLD.md)
- [DRK — Dark Knight](DRK.md)
- [BST — Beastmaster](BST.md)
- [BRD — Bard](BRD.md)
- [RNG — Ranger](RNG.md)
- [SMN — Summoner](SMN.md)

### Expansion Jobs
- [SAM — Samurai](SAM.md) *(stub)*
- [NIN — Ninja](NIN.md) *(stub)*
- [DRG — Dragoon](DRG.md)
- [BLU — Blue Mage](BLU.md) *(stub)*
- [COR — Corsair](COR.md) *(stub)*
- [PUP — Puppetmaster](PUP.md) *(stub)*
- [DNC — Dancer](DNC.md) *(stub)*
- [SCH — Scholar](SCH.md) *(stub)*
- [GEO — Geomancer](GEO.md) *(stub)*
- [RUN — Rune Fencer](RUN.md)

---

## Global Conventions

- **Alt buttons** — Navigation priority across all jobs
- **Ctrl buttons** — Skills and actions only (exception: Hub sets use Ctrl for both)
- **Ctrl+0 on primary hub** — Always the 2-hour ability, isolated to prevent accidental use

---

## Weapon Skill Sets

Within each WS set:
- **Ctrl buttons** — primary/endgame weapon skills
- **Alt buttons** — Alt+1/Alt+2 for hub navigation back; Alt+3+ for lower-tier or filler weapon skills

---

## Primary Action Sets

Every job has one or more sets representing its core reactive function — the thing you need to reach fastest under pressure. These sets get a dedicated Alt shortcut reachable from anywhere, same as the hub:

- **WHM/RDM** — Healing; Alt+2 from anywhere
- **BLM** — Single Target Nukes; Alt+2 from anywhere
- **RNG** — Archery WS; Alt+2 from anywhere
- **WAR/MNK/DRG** — No magic; WS sets reachable from both hubs directly, no extra shortcut needed

The principle: if you'd need it mid-fight without thinking, it gets a shortcut. If you set it up before a fight or use it deliberately, hub navigation is sufficient.

---

## Spell Naming Conventions

- **Multiple tiers in use** — suffix `S`/`L` (or `S`/`M`/`L`) for Small/Large (e.g. `CureS`, `CureM`, `CureL`). Adjust which spell each maps to as ranks are acquired while leveling.
- **Single tier in use** (always highest available) — omit rank entirely (e.g. `Slow`, `Distract`, `Banish`, `Holy`). Swap in the highest rank you have while leveling.
- **Nukes** — omit rank, use element name only (e.g. `Fire`, `Stone`, `Thundr`). Elemental wheel ordering always applies.
- **AoE variants** — suffix `ga` where applicable (e.g. `Curaga`, `Diaga`, `Slpga`).

Layouts are designed for level 99. While leveling, substitute lower ranks manually — a slot designated for Cure4 uses Cure3 until Cure4 is available. No restructuring needed.

---

## Gear Swapping — Out of Scope

Gear swapping is not handled by these macros. Two approaches can be layered on independently:

- **Manual `/equip` lines** — up to 6 lines per macro; workable for simple pre/post-cast swaps
- **GearSwap (Windower4 addon)** — the standard endgame solution; defines gear sets in Lua and auto-equips based on spell/ability conditions with no macro line overhead. Recommended once gear swapping matters to performance.

---

## Common Book (Planned)

A dedicated common macro book for cross-job utility, eliminating duplication across job books. Candidates:

- Consumables (medicines, XP rings)
- Utility spells (Sneak, Invisible, Deodorize, Teleport/Recall)
- Pre-combat buffs shared across jobs (Protect/Shell/Reraise/Bar-spells)
- Trust macros, Lockstyle sets
- Commonly subbed job spells and abilities (WHM/RDM sub spells, WAR/NIN/DNC sub abilities)
- Gear swap sets (Fast Cast, Refresh, Enhancing) if not handled by GearSwap

**Cascading rank macros** — tiered spells in the common book can use sequential lines from highest to lowest rank. FFXI executes lines sequentially and stops at the first successful command, so the macro auto-selects the highest available rank without manual adjustment as you level:

```
/ma "Protect V" <t>
/ma "Protect IV" <t>
/ma "Protect III" <t>
```

This makes the common book self-maintaining during leveling and truly universal across jobs.

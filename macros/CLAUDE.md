# CLAUDE.md — FFXI Macros

This folder documents a hub-and-spoke macro system for FFXI (retail), covering all jobs. Each job has its own file (`WAR.md`, `RDM.md`, etc.). Navigation lives in `JobsHub.md`. See `README.md` for full conventions.

## System Overview

Based on [The Hub System by Sekhmet](https://ffxiclopedia.fandom.com/wiki/The_Hub_System_of_Macro_Management_a_guide_by_Sekhmet). 40 macro books × 10 sets × 20 buttons (Ctrl+1-0 and Alt+1-0). A shared **JobsHub** book links all job books.

## Naming Rules

- **8 character hard limit** — strictly enforced
- Digits not Roman numerals: `Cure4`, `Haste2`, `Refresh3`
- Nav macros use `S` prefix ("go to Set"): `SHub`, `SHeal`, `SEnfCC`
- Abbreviate spell/skill names, prioritizing readability

## Button Conventions

- **Alt** = navigation priority (all jobs)
- **Ctrl** = skills/actions only (exception: Hub sets use both)
- **Ctrl+0 on primary hub** = 2-hour ability (always, every job)
- Fill spare Alt slots with lower-priority spells rather than leaving empty

## Hub Types

**Single Hub** (simple jobs, e.g. MNK): one hub + WS sets. Alt+1 = hub. Alt+1 blank on hub.

**Dual Hub** (complex melee, e.g. WAR, THF, BST): two peer hub sets split by logical category (offensive/defensive, combat/utility, etc.). Alt+1 and Alt+2 navigate between hubs from any WS set. Alt+1 blank on Set 1, Alt+2 blank on Set 2.

**Spell Hub** (mage jobs, e.g. RDM, WHM, BLM): single hub with always-up buffs + nav links to spell category sets. Alt+2 shortcut to the primary reactive set (Healing for healers, Nukes for BLM). Alt+2 blank on that primary reactive set.

## Navigation

- **Alt+0** on the primary hub = JobsHub book
- **Alt+1** = blank on the primary hub of every job (safe to hammer from any sub-set)
- **Alt+2** = blank on the secondary hub or primary reactive set
- Two-press sequence to reach JobsHub (Alt+1 to hub, then Alt+0) is intentional — prevents accidental job-switching

## Set Order (mage jobs)

1. Hub → 2. Healing → 3. Nuking → 4. Enfeebling/CC → 5. Offensive/Utility → 6. Enhance Others → 7. Enhance Self → 8+ WS, Overflow

## Elemental Ordering

Always: **Earth → Lightning → Water → Fire → Ice → Wind** (Light ↔ Dark)

## Spell Filtering — Excluded by Default

- **Pre-combat set-and-forget**: Protect/Shell/Reraise/Sneak/Invisible/Deodorize/Teleport/Bar-spells
- **Redundant**: lower tiers when a higher tier is macroed, healing is an exception for mana efficiency
- **Covered by Erase**: Blindna, Paralyna, Poisona — Cursna is kept because Erase does not remove Curse
- **Subjob spells**: excluded by default; switch to the relevant job book instead

## Targets

- `<me>` — self-only
- `<t>` — targeted
- `N/A` — navigation (no cast)

When a set contains both target types, pick the majority as the canonical `Target:` value. Minority exceptions are annotated inline after the macro name (e.g. `WpnBash <t>` in an otherwise `<me>` set). The 8-character name limit applies to the abbreviated name only — the target indicator does not count toward it.

## SMN Special Cases

- Sets organized **per avatar** (not by spell category)
- Dual Hub A/B (Sets 1-2), celestial avatars on Sets 3-8, Staff WS on Set 9, Set 10 open for future expansion/customization/subjob macros
- Overflow avatars (Cait Sith, Fenrir, Diabolos, Carbuncle) live in **MNK book Sets 6-9**; Sets 4 and 10 left empty as bookend buffers
- If more SMN overflow is needed, next destination is THF book (highest set number downward, buffer set first)

## Intentional Redundancy

Some spells appear on multiple sets deliberately — e.g. Regen on both Healing and EnhOth — because they're used reactively in different contexts. This is documented per job.

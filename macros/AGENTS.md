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
- `<t>` — always an enemy (offensive spells, debuffs, WS)
- `<st>` — sub-target; beneficial spell that may target a party member on a job that holds enemy lock during combat (PLD, DRK, RUN). A bare `<t>` on a cure or buff would land on the enemy.
- `N/A` — navigation (no cast)

When a set contains multiple target types, pick the majority as the canonical `Target:` value. Minority exceptions are annotated inline after the macro name (e.g. `WpnBash <t>` in an otherwise `<me>` set). The 8-character name limit applies to the abbreviated name only — the target indicator does not count toward it.

## SMN Special Cases

- Sets organized **per avatar** (not by spell category)
- Dual Hub A/B (Sets 1-2), celestial avatars on Sets 3-8, Staff WS on Set 9, Set 10 open for future expansion/customization/subjob macros
- Overflow avatars (Cait Sith, Fenrir, Diabolos, Carbuncle) live in **MNK book Sets 6-9**; Sets 4 and 10 left empty as bookend buffers
- If more SMN overflow is needed, next destination is THF book (highest set number downward, buffer set first)

## Intentional Redundancy

Some spells appear on multiple sets deliberately — e.g. Regen on both Healing and EnhOth — because they're used reactively in different contexts. This is documented per job.

---

## .md / .yml Dual-File Workflow

Each job has two files:

- **`JOB.md`** — design document. Button layout tables, naming rationale, glossary of abbreviations, open questions. Source of truth for *what* each button does and *why*.
- **`JOB.yml`** — importable artifact for the [macromog](../macromog/) tool. Contains the actual `/ma`, `/ja`, `/ws`, `/pet` command lines. Maintained in parallel with the .md.

The `.md` files are not generated from the `.yml` and vice versa — they are hand-authored companions. When you change what a button does, update both.

### Book Index Assignment

Each .md file begins with YAML frontmatter declaring its book slot — the single source of truth:

```markdown
---
book: 4
---
# Book: WHM — White Mage
```

The full assignment table:

| Book | Job      | Book | Job      |
|------|----------|------|----------|
| 1    | JobsHub  | 14   | SAM      |
| 2    | WAR      | 15   | NIN      |
| 3    | MNK      | 16   | DRG      |
| 4    | WHM      | 17   | BLU      |
| 5    | BLM      | 18   | COR      |
| 6    | RDM      | 19   | PUP      |
| 7    | THF      | 20   | DNC      |
| 8    | PLD      | 21   | SCH      |
| 9    | DRK      | 22   | GEO      |
| 10   | BST      | 23   | RUN      |
| 11   | BRD      | 24   | (reserved) |
| 12   | RNG      | 25–40 | (reserved) |
| 13   | SMN      |      |          |

### Navigation Macro Contents (Formulaic)

Nav macros are always two lines derived from the book table. No lookup needed — just book index + set number:

```yaml
contents:
  - /macro book N
  - /macro set M
```

Common patterns:

| Nav label | Meaning | Example (WHM = book 4) |
|-----------|---------|------------------------|
| `SJobHub` | Go to JobsHub Set 1 | `/macro book 1` / `/macro set 1` |
| `SHub`    | Go to this job's Set 1 | `/macro book 4` / `/macro set 1` |
| `SHeal`   | Go to this job's Set 2 | `/macro book 4` / `/macro set 2` |
| `SHub` (Alt+1 on Set 1) | Omitted — blank slot | (no entry in YAML) |

Blank nav slots (e.g., Alt+1 on the primary hub) are simply omitted from the YAML — sparse format means only non-empty slots appear.

### Authoring a .yml

```yaml
version: 1
scope:
  level: book
  selections:
    - {book: N}        # matches the book: N in the .md frontmatter
books:
  N:
    name: JOB          # ≤15 chars, alphanumeric — shown in-game
    sets:
      1:
        ctrl:
          1:
            name: McrName  # ≤8 bytes — shown on button
            contents:
              - /ma "Spell Name" <t>   # ≤6 lines, ≤60 chars each
        alt:
          0:
            name: SJobHub
            contents:
              - /macro book 1
              - /macro set 1
```

Constraints (from macromog schema):
- Books: 1–40, Sets: 1–10, Keys: 1–9 then 0 (0 = tenth/rightmost slot)
- Button name: ≤8 bytes
- Contents: ≤6 lines, each ≤60 characters
- Only populated slots appear — gaps are valid (sparse format)

### Stub .yml Files

Jobs not yet designed have minimal stub .yml files with only the `SJobHub` nav on Alt+0 of Set 1. These are valid for import but essentially empty. Expand them as the corresponding .md is designed.

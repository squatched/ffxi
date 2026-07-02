# CLAUDE.md — FFXI Macros

This folder documents a hub-and-spoke macro system for FFXI (retail), covering all jobs.
`spokes/JOB.yml` is the declarative layout `scripts/gen_macros.py` reads to build a
*per-character* macro set (any job/level/subjob combo, addresses allocated dynamically via
`characters/NAME/manifest.yml` — see `characters/AGENTS.md`). There are no fixed book numbers;
JobsHub itself is generated, not hand-authored. See "`spokes/JOB.yml` — Generator Input Format"
further down for its schema.

## System Overview

Based on [The Hub System by Sekhmet](https://ffxiclopedia.fandom.com/wiki/The_Hub_System_of_Macro_Management_a_guide_by_Sekhmet). 40 macro books × 10 sets × 20 buttons (Ctrl+1-0 and Alt+1-0). A shared **JobsHub** book links all job books.

## Naming Rules

- **8 character hard limit** — strictly enforced
- Digits not Roman numerals: `Cure4`, `Haste2`, `Refresh3`
- Nav macros use `S` prefix ("go to Set"): `SHub`, `SHeal`, `SEnfCC`
- Abbreviate spell/skill names, prioritizing readability

## Group Types

Every set in a job book is one of three types:

**Hub** — the player's home set. The hub is where you live between actions; you navigate to spokes as needed and return. Actions on the hub are the most constantly-needed — JAs and reactive self-buffs (spells are valid hub actions). Always pinned (reachable from every other set). Full nav to all groups on Alt. Ctrl+0 = 2-hour. Alt+0 = JobsHub, except on a hub's own overflow pages before the last one, where Alt+0 walks forward instead (see "Multi-page groups"). A job may have one or two hubs (max); a second hub is a full co-equal hub with the same contract, not an overflow mechanism. The primary hub is pin:1, the secondary hub is pin:2.

**Core** — a content set (spells/skills) that must be reactively reachable from any other set without first returning to the hub. Alt slot assignment is driven by `type:` and file order: cores fill Alt slots immediately after hubs in file order (see Navigation). No 2-hour on Ctrl+0; no full nav on Alt — just nav back to the hub(s). Use sparingly; each core costs one Alt slot on every other set.

**Spoke** — a content set reachable only from the hub. Nav back to hub(s) on Alt+1 (and Alt+2 if dual-hub). No pin.

## Button Conventions

- **Alt** = navigation priority (all groups)
- **Ctrl** = actions only (exception: hubs use both for actions and nav)
- **Ctrl+0** = 2-hour ability on **every hub** (primary and secondary)
- **Alt+0** = JobsHub on **every hub**; free on all other sets (exception: a hub's overflow pages before the last one use Alt+0 to walk forward instead — see "Multi-page groups")
- Action priority fills Ctrl slots in order: `high` → Ctrl+1-5, `mid` → Ctrl+6-0, `low` → remaining Alt slots then overflow to a second set

## Navigation

Alt slots are filled in priority order on every set:
1. **Hubs** — pin:1 → Alt+1 (always); pin:2 → Alt+2 if the job has a secondary hub
2. **Cores** — fill the next available Alt slots in pin order, immediately after hubs
3. **Spoke nav** (hub sets only) — remaining Alt slots after hub and core pins

Examples:
- Single-hub job, one core: Alt+1 = hub, Alt+2 = core
- Dual-hub job, one core: Alt+1 = Hub A, Alt+2 = Hub B, Alt+3 = core

Two-press sequence to reach JobsHub (Alt+1 → hub, then Alt+0) is intentional — prevents accidental job-switching. On a hub deep in its own overflow chain, this takes an extra press or two to walk forward to the last page first; that's an acceptable cost since subjob support means fast job-switching is no longer load-bearing the way it was when this convention was first written.

### Hub toggle (dual-hub jobs)
On Hub A: Alt+2 = Hub B. On Hub B: Alt+1 = Hub A. This link is pinned — it holds its slot on every page of that hub, including overflow pages (see "Multi-page groups"). Single-hub jobs have no hub-to-hub link, so neither slot is claimed by it.

### Multi-page groups
When any group overflows to a second set:

- **Spokes and core groups**: Alt+0 toggles page 1 ↔ page 2 (free on non-hub sets). The toggle always returns you to the primary page.
- **Hubs**: Alt+0 walks forward instead of toggling — page 1 → page 2 → … → the last page — and only on that last page does Alt+0 become JobsHub. Reaching JobsHub no longer needs to be one hop away from every hub page now that subjob support covers fast job-switching, so the extra hop through a deep overflow chain is an acceptable cost. Whichever of Alt+1/Alt+2 isn't claimed by the dual-hub pin (see above) carries this hub's own back-nav to the previous page — blank on page 1, since there's nothing before it. On a single-hub job, that's simply Alt+1.

  Example (single-hub, 2 pages): page 1 — Alt+0 = forward to page 2, Alt+1 blank. Page 2 (last) — Alt+0 = JobsHub, Alt+1 = back to page 1.

  Example (dual-hub, Hub A overflows to 2 pages): Hub A page 1 — Alt+0 = forward, Alt+1 blank, Alt+2 = Hub B (pinned). Hub A page 2 (last) — Alt+0 = JobsHub, Alt+1 = back to Hub A page 1, Alt+2 = Hub B (still pinned).

On hub overflow pages, Ctrl+0 = 2-hour is repeated. Ctrl+1-9 duplicates page 1 if all JAs fit there; otherwise holds the overflow JAs.

The generator only ever allocates up to 2 pages per hub/core/spoke today; if content still doesn't fit on page 2 it prints a `WARN: ... unreachable` rather than adding a third page. If a hub ever needs 3+ pages, the forward/back nav described above generalizes directly (Alt+0 keeps walking forward through the chain, JobsHub lands only on the true last page) — same idea JobsHub itself already uses for its own multi-page nav (`build_jobshub`) — but the generator would need extending to actually allocate beyond 2 pages.

For the `spokes/` generator path, capacity is enforced automatically — `scripts/gen_macros.py` dry-run checks capacity during address allocation (`_hub_page_fits` / `_nonhub_page_fits`) and reserves a second page whenever a hub, core, or spoke's actions or nav links don't fit on one, rather than dropping anything. It prints a `WARN:` if something still doesn't fit even with a second page.

## Group Taxonomy

Groups are named by **usage context** (how you reach for them mid-fight), not by magic type or
skill category. The same action can appear in multiple groups if it's genuinely used in different
contexts — this is expected and correct. Deduplication when merging subjob groups applies only
within the same group.

| Group | What belongs here | Examples |
|---|---|---|
| `nuking` | Offensive damage | Fire/Blizzard/Thunder series, Holy, Banish, Katon/Hyoton/Raiton ninjutsu, Drain, offensive BLU spells |
| `cc` | Crowd control — prevents, restricts, or impairs enemy action | Sleep/Sleepga, Bind, Gravity, Silence, Break, Repose, Lullaby, Elegy (BRD), Paralyze, Kurayami/Hojo ninjutsu |
| `dots` | Damage over time | Dia/Bio series, Poison, elemental DoTs (Choke/Rasp/Shock/Drown/Burn/Frost), Requiem (BRD) |
| `enfeebling` | Stat debuffs with no CC or DoT component; cross-cut into `cc` or `dots` if both apply | Slow, Blind, Addle, Frazzle, Distract, Dispel, Inundation, elemental DoTs (also in `dots`) |
| `healing` | Ally restoration and recovery | Cure/Cura/Raise/Regen series, Full Cure, Tractor, Curing Waltz, Paeon/Ballad songs |
| `status_removal` | Removing debuffs from allies | Erase, Esuna, Cursna, Poisona, Paralyna, Blindna, Silena, Viruna, Stona |
| `resist_dmg` | Damage resistance/mitigation — self or party | Stoneskin, Blink, Aquaveil, Phalanx, Utsusemi/Tonko/Migawari ninjutsu, Protect, Shell |
| `resist_elem` | Elemental resistance buffs — sub-category of `resist` | Barfira, Barblizzara, Barstonra, Barthundra, Barwatera, Baraera |
| `resist_status` | Status resistance buffs — sub-category of `resist` | Barsleepra, Barparalyzra, Barsilencera, Barpoisonra, Barpetra, Baramnesra |
| `enhance_self` | Capability buffs that can only target self | Enspells, Klimaform, Convert, Composure |
| `enhance_others` | Capability buffs cast on party members | Haste, Refresh, Regen, Boost-stats, Protect/Shell (party), March/Minuet/Madrigal/Mambo songs, COR rolls |
| `field` | Out-of-combat situational utility | Teleport/Recall, Warp, Flee, Sneak, Invisible, Deodorize, Tractor (field use) |
| `utility` | Catch-all for anything that genuinely doesn't fit above | (reserved; may be unused) |
| `ws_<weapon>` | Weapon skills — one group per weapon type | `ws_polearm`, `ws_sword`, `ws_great_sword`, `ws_hand_to_hand`, etc. |
| `avatar_<name>` | SMN per-avatar sets (summon + all blood pacts inline) | `avatar_ifrit`, `avatar_shiva`, etc. |
| `jug_pets` | BST jug pet command sets | — |

### Weapon type keys (snake_case, matching `data/weapon_skills/` filenames)
`ws_hand_to_hand` · `ws_dagger` · `ws_sword` · `ws_great_sword` · `ws_axe` · `ws_great_axe`
· `ws_scythe` · `ws_polearm` · `ws_katana` · `ws_great_katana` · `ws_club` · `ws_staff`
· `ws_marksmanship` · `ws_archery`

## Set Order (mage jobs)

1. Hub → 2. Healing → 3. Nuking → 4. Enfeebling/CC → 5. Offensive/Utility → 6. Enhance Others → 7. Enhance Self → 8+ WS, Overflow

## Elemental Ordering

Always: **Earth → Lightning → Water → Fire → Ice → Wind** (Light ↔ Dark)

## Spell Filtering Conventions

- **Redundant**: lower tiers when a higher tier is macroed, healing is an exception for mana efficiency
- **Covered by Erase**: Blindna, Paralyna, Poisona — Cursna is kept because Erase does not remove Curse
- **Subjob spells**: excluded by default; switch to the relevant job book instead

## Targets

- `<me>` — self-only
- `<t>` — always an enemy (offensive spells, debuffs, WS)
- `<st>` — sub-target; beneficial spell that may target a party member on a job that holds enemy lock during combat (PLD, DRK, RUN). A bare `<t>` on a cure or buff would land on the enemy.
- `N/A` — navigation (no cast)

When a set contains multiple target types, pick the majority as the canonical `Target:` value. Minority exceptions are annotated inline after the macro name (e.g. `WpnBash <t>` in an otherwise `<me>` set). The 8-character name limit applies to the abbreviated name only — the target indicator does not count toward it.

## Pet Command Syntax (`/ja` vs `/pet`)

- **DRG wyvern commands** — `/ja` and `/pet` are interchangeable. The wyvern is a job pet intrinsic to DRG, so wyvern commands sit in the same namespace as job abilities.
- **SMN blood pacts, BST pet commands** — `/pet` only. External summoned pets do not respond to `/ja`.
- **PUP** — all player-triggered commands (Activate, Deactivate, Overdrive, maneuvers) are `/ja`. The automaton then acts autonomously; there are no `/pet` commands for PUP.

## SMN Special Cases

- Sets organized **per avatar** (not by spell category)
- Primary book: hub (Set 1), six celestial avatars (Sets 2-7), Staff WS (Set 8), Carbuncle (Set 9), Fenrir (Set 10)
- Overflow avatars (Diabolos, Cait Sith, Siren, Alexander, Odin, Atomos) land in generator gap-fill sets; their exact addresses appear in the `# Overflow allocations:` comment header of the generated output
- Hub nav maxes out at 8 spokes (Alt+2-9); the first 8 spokes get links — Carbuncle (Alt+9) is the last. Diabolos through Atomos have no hub nav; navigate to them via `/macro book N` `/macro set M`

## Intentional Redundancy

Some spells appear on multiple sets deliberately — e.g. Regen on both Healing and EnhOth — because they're used reactively in different contexts. This is documented per job.

---

## `spokes/JOB.yml` — Generator Input Format

This is what `scripts/gen_macros.py` actually reads (via `characters/NAME/manifest.yml` — see
`characters/AGENTS.md`). It has no book/set/button addresses at all — just a declarative list of
hubs and groups, each holding named actions with a priority. The generator resolves action names
against `data/` (spells/JAs/WS availability at the target level), buckets by priority into
Ctrl/Alt slots, and allocates book/set addresses at generation time.

```yaml
job: WHM
name: White Mage
ws_rank_cutoff: C          # optional; overrides the default B- weapon-rank-to-include cutoff

exclude:                    # optional; action names never resolved for this job (see coverage.py)
  - Reraise

hubs:                       # 1-2 entries; each becomes a hub set (see "Group Types" above)
  - name: main               # referenced by characters/*/custom.yml to merge in custom actions
    label: "WHM Hub"          # nav button text (abbreviated to 8 chars); falls back to name
    actions:
      - {name: Stoneskin, priority: high}
      - {name: Cure, priority: mid, sub_tier: 1}   # sub_tier: series member N below the max tier
      - {name: Reraise, priority: low, exact: true} # exact: true — never auto-upgrade to a higher tier

groups:                     # any number; each becomes a core or spoke set
  - name: healing
    type: core                # core | spoke (see "Group Types" above)
    label: "Healing"           # optional; defaults to name.title()
    family: enhance             # optional; groups sharing a family merge into one set if the
                                  # combined action count fits (see FAMILY_DEFS in gen_macros.py)
    actions:
      - {name: Cure, priority: high}
```

Action entry fields: `name` (required — spell/JA/WS/avatar/blood-pact name as it appears in
`data/`), `priority` (`high`/`mid`/`low`, default `mid`), `sub_tier` (int — for multi-slot series
like CureS/M/L), `exact` (bool — pin to this exact tier, never auto-upgrade), `self_only`
(overrides the job/spell default target).

Group names are the same namespace `characters/*/custom.yml` uses to merge custom macros into an
existing hub/core/spoke, or to define a brand-new one (see `characters/AGENTS.md`).

---

## Future Ideas / Out of Scope

- **Common book (not yet implemented)** — a dedicated cross-job macro book for utility that
  doesn't belong to any one job: consumables (medicines, XP rings), Sneak/Invisible/Deodorize/
  Teleport-Recall, Trust macros, lockstyle sets, and commonly-subbed job spells/abilities. Would
  reduce duplication across job books. A candidate technique for tiered spells in such a book:
  cascading rank lines — FFXI runs macro lines sequentially and stops at the first successful
  command, so stacking `/ma "Protect V" <t>` / `/ma "Protect IV" <t>` / `/ma "Protect III" <t>`
  auto-selects the highest available rank with no manual adjustment while leveling.
- **Gear swapping is out of scope** for this macro system. Two options exist independently, layered
  on top: manual `/equip` lines (workable for simple pre/post-cast swaps, within the 6-line/macro
  limit) or [GearSwap](https://github.com/Windower/Lua) (the standard endgame solution — Lua gear
  sets auto-equipped based on spell/ability conditions, recommended once gear swapping matters to
  performance).

# AGENTS.md — Characters

This directory holds per-character, per-player inputs to `scripts/gen_macros.py`. Nothing here is
game data or macro layout — those live in `data/` and `macros/spokes/`. This directory is **git-ignored**
(see repo root `.gitignore`) — it's local to the player running the generator, not checked in.

```
characters/
  AGENTS.md          # this file
  custom.yml          # optional — account-wide custom macros, applied to every character
  NAME/
    manifest.yml       # required — which jobs/levels/subjobs this character's output covers
    custom.yml          # optional — this character's own custom macros
```

---

## `NAME/manifest.yml`

Drives which job book(s) get generated for this character and in what order. Order matters: it's
also the order books get assigned and the order jobs appear in JobsHub nav.

```yaml
character: Valeria
configurations:
  - {job: WAR, level: 50, subjob: MNK}
  - {job: WHM, level: 50, subjob: BLM}
  - {job: DRK, level: 1}
  - {job: RUN, level: 50, subjob: WAR, book: 23}   # explicit book override (optional)
```

- `job` — required, matches a `data/jobs/JOB.yml` / `macros/spokes/JOB.yml` pair
- `level` — defaults to 99 if omitted
- `subjob` — optional; resolved at `level // 2` and merged into the main job's groups (merge logic:
  `scripts/gen_macros.py::_merge_subjob`)
- `book` — optional explicit primary book number; otherwise auto-increments from 2

Run with `python3 scripts/gen_macros.py NAME` (writes `out/NAME.yml`), or `--char CHARNAME` to
import directly via macromog, or `--out PATH` for a custom output path.

---

## `custom.yml` — Player-Authored Custom Macros

Lets you add macros the generator can't derive from `data/` (Mount, Trust, a farming macro, an
Escape/Teleport combo, etc.) without touching the authoritative `macros/spokes/JOB.yml` files.
Custom entries flow through the **same** priority (`high`/`mid`/`low`) and group/merge machinery
as every generated action — they aren't a separate bolted-on mechanism.

Two files are loaded and deep-merged (lists concatenate, dicts merge key-wise), in this order:

1. `characters/custom.yml` — applies to every character
2. `characters/NAME/custom.yml` — this character only, layered on top

### Schema

```yaml
global:                          # → JobsHub, bucketed by priority like job nav buttons
  - name: Mount
    priority: high                # high/mid/low; job nav buttons default to 'mid'
    contents:
      - /item "Chocobo Whistle"
  - name: Trust
    priority: mid
    contents:
      - /ma "Trust: Kupipi" <me>

jobs:
  RDM:
    main:                        # matches an existing hub/core/spoke *name* in
                                  # macros/spokes/RDM.yml → merges into it
      - name: Escape
        priority: low
        contents:
          - /item "Silent Oil"
          - /ma "Escape" <me>

    WHM:                         # WHM is a real job code (data/jobs/WHM.yml exists) →
                                  # scopes everything nested here to RDM main / WHM sub only
      grind:                     # no group named "grind" exists on RDM → becomes a
                                  # brand-new spoke (or core), with its own nav + address
        type: spoke               # spoke (default) | core
        label: "Grind Set"        # optional; defaults to the key, title-cased
        actions:
          - name: PullPlan
            priority: high
            contents:
              - /ma "Sleep" <t>
```

### Rules

- **`global`** entries are raw command lines merged with job-nav buttons on JobsHub, sorted by
  priority (stable — equal-priority customs land just ahead of job nav). No subjob scoping applies.
- **`jobs.JOB`** — any key that is *not* a real job code (i.e. `data/jobs/{key}.yml` doesn't exist)
  is a **group name** and applies to `JOB` regardless of subjob. Group names must match a hub/core/
  spoke `name` field in `macros/spokes/JOB.yml` to merge in; job codes are always uppercase
  3-letter, group names never collide with them.
- **`jobs.JOB.SUBJOB`** — a key that *is* a real job code nests one level deeper and scopes its
  group entries to that exact main/sub combo. A manifest entry for `RDM/WHM` picks up both
  `jobs.RDM.<group>` (any-subjob) and `jobs.RDM.WHM.<group>` (combo-specific); `jobs.RDM.BLM.<group>`
  would not apply.
- A new group's value can be a **plain list** (shorthand — becomes a `type: spoke` with no custom
  label) or a **dict** with `type`/`label`/`actions` for explicit control.
- Entries need `name` + `contents` (a list of literal macro lines, ≤6 lines/≤60 chars each per the
  macromog schema — not enforced by the generator, verify manually). `display` optionally overrides
  the button text (defaults to `name` abbreviated to 8 chars). `priority` defaults to `mid`.
- If a job's hub/groups are already full, custom entries (like everything else) spill onto an
  overflow page rather than getting dropped — see "Multi-page groups" in `macros/AGENTS.md`.

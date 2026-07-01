#!/usr/bin/env python3
"""
Coverage report: what actions a job can access vs what the spoke definition covers.

  python3 scripts/coverage.py WHM           # L99 report
  python3 scripts/coverage.py WHM 50        # L50 report
  python3 scripts/coverage.py WHM --strict  # include lower series tiers in uncovered

Default mode suppresses lower-tier series members from the uncovered list when any
tier of that series is already covered or excluded.  Weapon-specific (relic/empyrean/
prime/aeonic) WS are also suppressed by default since most players won't have them.
--strict disables both suppressions and reports every individual action.

Spoke files may list actions to intentionally omit:
  exclude:
    - Reraise     # pre-combat set-and-forget
    - Protect     # pre-combat

Excluded names also suppress their series siblings in default mode.

Exit code 1 if any spoke entry is unreachable (wrong name or unavailable to job).
Exit code 0 otherwise (including when uncovered items exist).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gen_macros import (
    DATA_DIR, SPOKES_DIR,
    _load, _avail_spells, _avail_abilities, _avail_ws, _avail_ws_exotic, _avail_wyvern,
    build_series_map, _build_spell_target_map, _resolve_action,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Coverage of a spoke definition against job availability.'
    )
    parser.add_argument('job',   help='Job abbreviation (WHM, BLM, …)')
    parser.add_argument('level', type=int, nargs='?', default=99,
                        help='Character level (default: 99)')
    parser.add_argument('--strict', action='store_true',
                        help='Report all uncovered actions including lower series tiers')
    args = parser.parse_args()

    job   = args.job.upper()
    level = args.level

    job_path   = DATA_DIR / 'jobs'   / f'{job}.yml'
    spoke_path = SPOKES_DIR          / f'{job}.yml'

    if not job_path.exists():
        sys.exit(f'error: no job data at {job_path}')
    if not spoke_path.exists():
        sys.exit(f'error: no spoke definition at {spoke_path}')

    job_data  = _load(job_path)
    spoke_def = _load(spoke_path)

    name_to_series, series_members = build_series_map(DATA_DIR)
    spell_targets = _build_spell_target_map(DATA_DIR)
    ability_data  = {ab['name']: ab for ab in job_data.get('abilities', [])}
    for cmd in job_data.get('wyvern_commands', []):
        ability_data[cmd['name']] = cmd

    cutoff    = spoke_def.get('ws_rank_cutoff', 'B-')
    spells    = _avail_spells(job_data, DATA_DIR, level)
    abilities = _avail_abilities(job_data, level)
    ws_names  = _avail_ws(job_data, DATA_DIR, level, cutoff)
    wyvern    = _avail_wyvern(job_data, level)
    two_hour  = job_data.get('two_hour_ability')

    # Precompute L99 availability for "not yet unlocked" hints when level < 99
    if level < 99:
        avail_99: set[str] = (
            _avail_spells(job_data, DATA_DIR, 99)
            | _avail_abilities(job_data, 99)
            | _avail_ws(job_data, DATA_DIR, 99, cutoff)
            | _avail_wyvern(job_data, 99)
        )
        if two_hour:
            avail_99.add(two_hour)
    else:
        avail_99 = None

    # Availability map: name → category tag
    available: dict[str, str] = {}
    for s in spells:    available[s] = 'spell'
    for a in abilities: available[a] = 'ability'
    for w in ws_names:  available[w] = 'ws'
    for v in wyvern:    available[v] = 'wyvern'
    if two_hour:        available.setdefault(two_hour, 'ability')

    excludes: set[str] = set(spoke_def.get('exclude', []))
    ws_exotic: set[str] = _avail_ws_exotic(job_data, DATA_DIR)

    # ── Resolve spoke entries ─────────────────────────────────────────────────

    covered: set[str] = set()
    if two_hour:
        covered.add(two_hour)  # always auto-placed by generator on every hub

    unreachable: list[tuple[str, str, str]] = []

    def _hint(entry: dict) -> str:
        name    = entry['name']
        root    = name_to_series.get(name, name)
        members = series_members.get(root, [name])
        if avail_99 and any(m in avail_99 for m in members):
            return f'not yet available at L{level}'
        return f'not available to {job}'

    def _walk(group_name: str, entry: dict, is_hub: bool) -> None:
        result = _resolve_action(
            entry, group_name, is_hub,
            spells, abilities, ws_names, wyvern,
            job_data, spell_targets, ability_data,
            name_to_series, series_members,
        )
        if result:
            covered.add(result['resolved'])
        else:
            unreachable.append((group_name, entry['name'], _hint(entry)))

    for hub in spoke_def.get('hubs', []):
        for entry in hub.get('actions', []):
            _walk(hub['name'], entry, is_hub=True)

    for group in spoke_def.get('groups', []):
        for entry in group.get('actions', []):
            _walk(group['name'], entry, is_hub=False)

    # ── Build uncovered list ──────────────────────────────────────────────────

    def _series_touched(name: str) -> bool:
        """True if any series member is covered or excluded."""
        root    = name_to_series.get(name, name)
        members = series_members.get(root, [name])
        return any(m in covered or m in excludes for m in members)

    uncovered: list[tuple[str, str]] = []  # (category, name)
    for name in sorted(available):
        if name in covered:
            continue
        if name in excludes:
            continue
        if name == two_hour:
            continue
        if not args.strict and _series_touched(name):
            continue
        if not args.strict and name in ws_exotic:
            continue
        uncovered.append((available[name], name))

    # ── Output ────────────────────────────────────────────────────────────────

    job_name = job_data.get('name', job)
    title    = f'{job} ({job_name}) — L{level}'
    print(title)
    print('─' * len(title))

    n_avail = len(available)
    n_cov   = len(covered & available.keys())
    n_unc   = len(uncovered)
    n_unr   = len(unreachable)
    print(f'Available {n_avail}  │  Covered {n_cov}  │  Uncovered {n_unc}  │  Unreachable {n_unr}')

    if uncovered:
        print('\nUNCOVERED')
        print('─' * 40)
        for category, name in uncovered:
            print(f'  {category:<10} {name}')

    if unreachable:
        print(f'\nUNREACHABLE  (in spoke, resolves to nothing at L{level})')
        print('─' * 40)
        for group_name, name, hint in unreachable:
            print(f'  {group_name:<18} {name}  [{hint}]')

    if not uncovered and not unreachable:
        print('\nFully covered — no gaps.')

    sys.exit(1 if unreachable else 0)


if __name__ == '__main__':
    main()

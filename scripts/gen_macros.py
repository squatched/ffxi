#!/usr/bin/env python3
"""
Generate a leveling macro set for an FFXI job at a given level.

The existing hand-crafted macro YAML (macros/JOB.yml) is the authoritative
layout. This script replaces end-game spell names with the best available tier
at the given level, removes unavailable actions, and distributes series slots
(CureS / CureM / CureL) across available tiers with gaps when fewer tiers are
available than slots. Nav macros are always preserved unchanged.

Usage:
  python3 scripts/gen_macros.py WHM 45           # writes out/WHM45.yml
  python3 scripts/gen_macros.py BLM 30           # writes out/BLM30.yml
  python3 scripts/gen_macros.py WHM 45 --char Valeria
"""

import argparse
import re
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / 'data'
MACROS_DIR = ROOT_DIR / 'macros'
OUT_DIR = ROOT_DIR / 'out'


# ── Series map ────────────────────────────────────────────────────────────────

def build_series_map(data_dir: Path):
    """
    Walk all magic catalog files and follow prev/next chains.

    Returns:
      name_to_series: {spell_name: series_root_name}
      series_members: {series_root_name: [spell_name, ...]}  (ordered low→high)
    """
    name_to_series: dict[str, str] = {}
    series_members: dict[str, list[str]] = {}

    for catalog_path in (data_dir / 'magic').glob('*.yml'):
        with open(catalog_path) as f:
            catalog = yaml.safe_load(f)

        magic_type = catalog.get('magic', '')
        if magic_type in ('blood_pacts', 'summoning'):
            continue

        spells = catalog.get('spells', [])
        spell_by_name = {s['name']: s for s in spells if 'name' in s}

        for spell in spells:
            name = spell.get('name')
            if not name or 'prev' in spell:
                continue  # not a root (roots have no prev)
            if 'next' not in spell:
                continue  # singleton, no series

            # Walk the chain from this root
            members: list[str] = []
            current_name = name
            while current_name:
                members.append(current_name)
                current_spell = spell_by_name.get(current_name, {})
                current_name = current_spell.get('next')

            series_members[name] = members
            for m in members:
                name_to_series[m] = name

    return name_to_series, series_members


# ── Availability ──────────────────────────────────────────────────────────────

def available_spells(data_dir: Path, job: str, level: int) -> set[str]:
    job_data = _load_yaml(data_dir / 'jobs' / f'{job}.yml')
    found: set[str] = set()

    for category in job_data.get('magic', []):
        if category in ('blood_pacts', 'summoning'):
            continue
        catalog_path = data_dir / 'magic' / f'{category}.yml'
        if not catalog_path.exists():
            continue
        catalog = _load_yaml(catalog_path)

        for spell in catalog.get('spells', []):
            name = spell.get('name')
            if not name:
                continue
            if job in spell:           # shared catalog (white/black magic)
                if spell[job] <= level:
                    found.add(name)
            elif 'level' in spell:     # exclusive catalog (ninjutsu, songs, …)
                if spell['level'] <= level:
                    found.add(name)

    return found


def available_abilities(data_dir: Path, job: str, level: int) -> set[str]:
    job_data = _load_yaml(data_dir / 'jobs' / f'{job}.yml')
    found: set[str] = set()

    for ab in job_data.get('abilities', []):
        if ab.get('level', 999) > level:
            continue
        if ab.get('notes') == 'merit' and level < 99:
            continue
        found.add(ab['name'])

    return found


def available_ws(data_dir: Path, job: str, level: int) -> set[str]:
    job_data = _load_yaml(data_dir / 'jobs' / f'{job}.yml')
    rank_caps = _load_yaml(data_dir / 'weapon_rank_caps.yml')
    found: set[str] = set()

    for weapon_type, rank in job_data.get('weapons', {}).items():
        tier = rank_caps.get('tiers', {}).get(rank, {})
        caps = tier.get('caps', [])
        if level < 1 or level > len(caps):
            continue
        cap = caps[level - 1]

        ws_filename = weapon_type.replace(' ', '_') + '.yml'
        ws_path = data_dir / 'weapon_skills' / ws_filename
        if not ws_path.exists():
            continue
        ws_data = _load_yaml(ws_path)

        for ws in ws_data.get('skills', []):
            acq = ws.get('acquisition', 'automatic')
            if acq == 'weapon_specific':
                continue
            if acq == 'merit' and level < 99:
                continue
            if ws.get('skill', 0) > cap:
                continue
            allowed_jobs = ws.get('jobs')
            if allowed_jobs and job not in allowed_jobs:
                continue
            found.add(ws['name'])

    return found


# ── Macro command parsing ─────────────────────────────────────────────────────

_CMD_RE = re.compile(r'^(/\w+)\s+"([^"]+)"\s+(<\w+>)\s*$')


def parse_action(line: str):
    """Return (cmd, name, target) for /ma /ja /ws /pet lines, else None."""
    m = _CMD_RE.match(line.strip())
    if m and m.group(1) in ('/ma', '/ja', '/ws', '/pet'):
        return m.group(1), m.group(2), m.group(3)
    return None


def is_nav(line: str) -> bool:
    return line.strip().startswith('/macro ')


# ── Gap-distribution algorithm ────────────────────────────────────────────────

def distribute(n_slots: int, tiers: list[str]) -> list[str | None]:
    """
    Assign m available tiers to n_slots with gaps when m < n.

    Rules:
    - slot[0]  always gets the lowest tier
    - slot[-1] always gets the highest tier
    - middle slots get interpolated tiers
    - remaining slots are None (removed from output)
    - single slot: gets the highest available tier
    """
    m = len(tiers)
    result: list[str | None] = [None] * n_slots

    if m == 0:
        return result

    if n_slots == 1:
        result[0] = tiers[-1]   # single slot → best available
        return result

    if m >= n_slots:
        # Pick n evenly spaced indices from the m tiers
        for i in range(n_slots):
            idx = round(i * (m - 1) / (n_slots - 1))
            result[i] = tiers[idx]
    else:
        # Fewer tiers than slots: anchor low at slot[0], high at slot[-1]
        result[0] = tiers[0]
        if m > 1:
            result[-1] = tiers[-1]
        # Fill middle slots with remaining tiers
        for i, t in enumerate(tiers[1:-1], start=1):
            result[i] = t

    return result


# ── Set processor ─────────────────────────────────────────────────────────────

def _series_pos(name: str, name_to_series, series_members) -> int:
    root = name_to_series.get(name)
    if root is None:
        return 0
    members = series_members.get(root, [])
    try:
        return members.index(name)
    except ValueError:
        return 0


def process_set(set_data: dict,
                avail_spells: set[str],
                avail_abilities: set[str],
                avail_ws: set[str],
                name_to_series: dict,
                series_members: dict):
    """Modify set_data in-place."""

    # ── 1. Collect all action slots ──────────────────────────────────────────
    # action_slots: {(side, slot_id): (cmd, name, target)}
    action_slots: dict = {}

    for side in ('ctrl', 'alt'):
        for slot_id, slot in set_data.get(side, {}).items():
            for line in slot.get('contents', []):
                parsed = parse_action(line)
                if parsed:
                    action_slots[(side, slot_id)] = parsed
                    break   # one action line per slot is the convention

    # ── 2. Group /ma slots by series within this set ─────────────────────────
    # series_root → [(side, slot_id), ...] sorted by series position of referenced spell
    series_groups: dict[str, list] = {}
    for key, (cmd, name, _) in action_slots.items():
        if cmd != '/ma':
            continue
        root = name_to_series.get(name)
        if root:
            series_groups.setdefault(root, []).append(key)

    for root, keys in series_groups.items():
        keys.sort(key=lambda k: _series_pos(action_slots[k][1], name_to_series, series_members))

    # ── 3. Compute overrides ─────────────────────────────────────────────────
    # overrides: {(side, slot_id): new_name or None}
    overrides: dict = {}

    # Series groups (multi-slot): gap distribution
    for root, keys in series_groups.items():
        if len(keys) < 2:
            continue
        members = series_members.get(root, [])
        avail_in_series = [m for m in members if m in avail_spells]
        assigned = distribute(len(keys), avail_in_series)
        for key, tier in zip(keys, assigned):
            overrides[key] = tier

    # Single-occurrence series: highest available tier
    for root, keys in series_groups.items():
        if len(keys) != 1:
            continue
        key = keys[0]
        if key in overrides:
            continue
        members = series_members.get(root, [])
        avail_in_series = [m for m in members if m in avail_spells]
        overrides[key] = avail_in_series[-1] if avail_in_series else None

    # Non-series /ma slots: check availability directly
    for key, (cmd, name, _) in action_slots.items():
        if cmd != '/ma' or key in overrides:
            continue
        overrides[key] = name if name in avail_spells else None

    # /ja slots
    for key, (cmd, name, _) in action_slots.items():
        if cmd != '/ja':
            continue
        overrides[key] = name if name in avail_abilities else None

    # /ws slots
    for key, (cmd, name, _) in action_slots.items():
        if cmd != '/ws':
            continue
        overrides[key] = name if name in avail_ws else None

    # /pet (blood pacts): leave untouched — complex to validate per avatar

    # ── 4. Apply overrides ───────────────────────────────────────────────────
    for (side, slot_id), new_name in overrides.items():
        side_data = set_data.get(side, {})
        if slot_id not in side_data:
            continue

        if new_name is None:
            del side_data[slot_id]
            continue

        slot = side_data[slot_id]
        slot['contents'] = [
            make_action(parse_action(line), new_name) if parse_action(line) else line
            for line in slot.get('contents', [])
        ]

    # Clean up now-empty sides
    for side in ('ctrl', 'alt'):
        if side in set_data and not set_data[side]:
            del set_data[side]


def make_action(parsed, new_name: str) -> str:
    cmd, _, target = parsed
    return f'{cmd} "{new_name}" {target}'


# ── Book processor ────────────────────────────────────────────────────────────

def process_book(book_yaml: dict,
                 avail_spells: set[str],
                 avail_abilities: set[str],
                 avail_ws: set[str],
                 name_to_series: dict,
                 series_members: dict) -> dict:
    result = deepcopy(book_yaml)

    for book_data in result.get('books', {}).values():
        for set_data in book_data.get('sets', {}).values():
            process_set(set_data, avail_spells, avail_abilities, avail_ws,
                        name_to_series, series_members)

    return result


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Generate a level-appropriate macro set from the authoritative L99 layout'
    )
    parser.add_argument('job',   help='Job abbreviation (WHM, BLM, WAR, …)')
    parser.add_argument('level', type=int, help='Character level (1–99)')
    parser.add_argument('--out', '-o', metavar='FILE',
                        help='Write output to FILE instead of stdout')
    parser.add_argument('--char', metavar='CHARNAME',
                        help='Import directly into macromog for CHARNAME')
    args = parser.parse_args()

    job = args.job.upper()
    level = args.level

    macro_path = MACROS_DIR / f'{job}.yml'
    job_data_path = DATA_DIR / 'jobs' / f'{job}.yml'

    if not macro_path.exists():
        sys.exit(f'error: no macro file at {macro_path}')
    if not job_data_path.exists():
        sys.exit(f'error: no job data at {job_data_path}')

    name_to_series, series_members = build_series_map(DATA_DIR)

    avail_sp  = available_spells(DATA_DIR, job, level)
    avail_ab  = available_abilities(DATA_DIR, job, level)
    avail_ws_ = available_ws(DATA_DIR, job, level)

    with open(macro_path) as f:
        book_yaml = yaml.safe_load(f)

    result = process_book(book_yaml, avail_sp, avail_ab, avail_ws_,
                          name_to_series, series_members)

    output = yaml.dump(result, default_flow_style=False, allow_unicode=True,
                       sort_keys=False)

    if args.char:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False,
                                         prefix=f'ffxi_{job}_{level}_') as tmp:
            tmp.write(output)
            tmp_path = Path(tmp.name)
        try:
            subprocess.run(
                ['macromog', 'import', '--char-name', args.char, str(tmp_path)],
                check=True,
            )
        finally:
            tmp_path.unlink(missing_ok=True)
    else:
        out_path = Path(args.out) if args.out else OUT_DIR / f'{job}{level}.yml'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output)
        print(f'Written to {out_path}', file=sys.stderr)


if __name__ == '__main__':
    main()

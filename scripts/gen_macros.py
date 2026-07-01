#!/usr/bin/env python3
"""
Build a complete character macro set from spoke definitions + game data.

Usage:
  python3 scripts/gen_macros.py Valeria
  python3 scripts/gen_macros.py Valeria --out path/to/file.yml
  python3 scripts/gen_macros.py Valeria --char Valeria
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import yaml

ROOT_DIR   = Path(__file__).parent.parent
DATA_DIR   = ROOT_DIR / 'data'
SPOKES_DIR = ROOT_DIR / 'macros' / 'spokes'
CHARS_DIR  = ROOT_DIR / 'characters'
OUT_DIR    = ROOT_DIR / 'out'

CTRL_SLOTS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]
ALT_SLOTS  = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]

RANK_ORDER = ['E', 'D', 'C-', 'C', 'C+', 'B-', 'B', 'B+', 'A-', 'A', 'A+']

PRIORITY_RANK = {'low': 0, 'mid': 1, 'high': 2}

# Family definitions: family_name → member group names (merge candidates)
FAMILY_DEFS: dict[str, list[str]] = {
    'enfeebling':  ['cc', 'enfeebling', 'dots'],
    'enhance':     ['enhance_others', 'enhance_self'],
    'resist':      ['resist_dmg', 'resist_elem', 'resist_status'],
    'resist_bars': ['resist_elem', 'resist_status'],
}

# Group names whose actions always target self
SELF_GROUPS = frozenset({'enhance_self', 'pre_battle', 'field'})
# Group names whose actions always target an enemy
ENEMY_GROUPS = frozenset({'nuking', 'nuking_aoe', 'cc', 'dots', 'enfeebling'})

# Content slots before overflow: ~10 Ctrl + 8 Alt after a typical non-hub nav prefix
MAX_CONTENT = 18

# Known nav button labels for groups (≤8 chars)
_GROUP_NAV_LABELS: dict[str, str] = {
    'healing':        'SHeal',
    'nuking':         'SNukes',
    'nuking_aoe':     'SAoeNuke',
    'cc':             'SCC',
    'status_removal': 'SStatRmv',
    'dark_utility':   'SDarkUtl',
    'enfeebling':     'SEnfblg',
    'dots':           'SDots',
    'resist_dmg':    'SResDmg',
    'resist_elem':   'SResElem',
    'resist_status': 'SResStat',
    'resist':        'SResist',
    'resist_bars':   'SResBars',
    'enhance_self':   'SEnhSlf',
    'enhance_others': 'SEnhOth',
    'field':          'SField',
    'utility':        'SUtil',
    'ws_polearm':     'SPolrm',
    'ws_sword':       'SSword',
    'ws_dagger':      'SDagger',
    'ws_great_sword': 'SGtSwd',
    'ws_axe':         'SAxe',
    'ws_great_axe':   'SGtAxe',
    'ws_scythe':      'SScythe',
    'ws_katana':      'SKtna',
    'ws_great_katana': 'SGtKtna',
    'ws_club':        'SClub',
    'ws_staff':       'SStaff',
    'ws_hand_to_hand': 'SHTH',
    'ws_marksmanship': 'SMrksmn',
    'ws_archery':     'SArchry',
    # merged family names
    'enfeebling_merged': 'SEnfblg',
    'enhance':        'SEnhAll',
    'ws':             'SWS',
}


# ── Utilities ──────────────────────────────────────────────────────────────────

def _load(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}

def _rank_idx(rank: str) -> int:
    try:
        return RANK_ORDER.index(rank)
    except ValueError:
        return -1

def _abbrev(name: str, max_len: int = 8) -> str:
    """Abbreviate a name to ≤max_len chars for macro button display."""
    s = name
    for rom, dig in ((' VI', '6'), (' V', '5'), (' IV', '4'), (' III', '3'), (' II', '2')):
        s = s.replace(rom, dig)
    s = s.replace(' ', '').replace("'", '')
    return s[:max_len]

def _nav_label(text: str) -> str:
    """Create a ≤8-char nav button label with 'S' prefix from a hub label."""
    s = re.sub(r'\s*(Hub|Set|Page)\s*$', '', text, flags=re.I).strip()
    parts = s.split('/')
    if len(parts) >= 2:
        body = parts[0][:3].strip() + parts[1][:4].strip()
    else:
        body = s.replace(' ', '')
    return ('S' + body)[:8]

def _group_nav_label(group_name: str, label: Optional[str] = None) -> str:
    if label:
        return _nav_label(label)
    return _GROUP_NAV_LABELS.get(group_name) or ('S' + group_name.replace('_', '')[:7])[:8]

def _higher_priority(a: str, b: str) -> str:
    return a if PRIORITY_RANK.get(a, 0) >= PRIORITY_RANK.get(b, 0) else b


# ── Series map ────────────────────────────────────────────────────────────────

def build_series_map(data_dir: Path):
    """Walk magic catalog files and build spell upgrade chain maps."""
    name_to_series: dict[str, str] = {}
    series_members: dict[str, list[str]] = {}

    for path in (data_dir / 'magic').glob('*.yml'):
        catalog = _load(path)
        if catalog.get('magic') in ('blood_pacts', 'summoning'):
            continue
        spells = catalog.get('spells', [])
        by_name = {s['name']: s for s in spells if 'name' in s}
        for spell in spells:
            name = spell.get('name')
            if not name or 'prev' in spell or 'next' not in spell:
                continue
            members: list[str] = []
            cur: Optional[str] = name
            while cur:
                members.append(cur)
                cur = by_name.get(cur, {}).get('next')
            series_members[name] = members
            for m in members:
                name_to_series[m] = name

    return name_to_series, series_members


# ── Availability ──────────────────────────────────────────────────────────────

def _avail_spells(job_data: dict, data_dir: Path, level: int) -> set[str]:
    job = job_data['job']
    found: set[str] = set()
    for category in job_data.get('magic', []):
        if category in ('blood_pacts', 'summoning'):
            continue
        path = data_dir / 'magic' / f'{category}.yml'
        if not path.exists():
            continue
        catalog = _load(path)
        for spell in catalog.get('spells', []):
            name = spell.get('name')
            if not name:
                continue
            if job in spell:
                if spell[job] <= level:
                    found.add(name)
            elif 'level' in spell:
                if spell['level'] <= level:
                    found.add(name)
    return found


_RANGED_WEAPONS = frozenset({'Archery', 'Marksmanship'})

def _avail_abilities(job_data: dict, level: int) -> set[str]:
    found: set[str] = set()
    for ab in job_data.get('abilities', []):
        if ab.get('level', 999) > level:
            continue
        if ab.get('notes') == 'merit' and level < 99:
            continue
        found.add(ab['name'])
    if _RANGED_WEAPONS & job_data.get('weapons', {}).keys():
        found.add('Ranged Attack')
    return found


def _avail_wyvern(job_data: dict, level: int) -> set[str]:
    found: set[str] = set()
    for cmd in job_data.get('wyvern_commands', []):
        if cmd.get('level', 999) <= level:
            found.add(cmd['name'])
    return found


def _avail_ws(job_data: dict, data_dir: Path, level: int, cutoff: str) -> set[str]:
    """Return available WS names. weapon_specific WS always included; others filtered by rank cutoff."""
    rank_caps = _load(data_dir / 'weapon_rank_caps.yml')
    cutoff_idx = _rank_idx(cutoff)
    found: set[str] = set()
    job = job_data['job']

    for weapon_type, rank in job_data.get('weapons', {}).items():
        ws_file = data_dir / 'weapon_skills' / (weapon_type.replace(' ', '_').replace('-', '_') + '.yml')
        if not ws_file.exists():
            continue
        ws_data = _load(ws_file)

        below_cutoff = _rank_idx(rank) <= cutoff_idx
        cap_at_level: Optional[int] = None
        if not below_cutoff:
            tier = rank_caps.get('tiers', {}).get(rank, {})
            caps = tier.get('caps', [])
            if 1 <= level <= len(caps):
                cap_at_level = caps[level - 1]

        for ws in ws_data.get('skills', []):
            name = ws.get('name')
            if not name:
                continue
            allowed = ws.get('jobs')
            if allowed and job not in allowed:
                continue
            acq = ws.get('acquisition', 'automatic')

            if acq == 'weapon_specific':
                found.add(name)  # always include regardless of rank
                continue

            if below_cutoff or cap_at_level is None:
                continue
            if acq == 'merit' and level < 99:
                continue
            if ws.get('skill', 0) > cap_at_level:
                continue

            found.add(name)

    return found


def _avail_ws_exotic(job_data: dict, data_dir: Path) -> set[str]:
    """Return the subset of available WS names that are weapon_specific (relic/empyrean/prime/etc)."""
    job = job_data['job']
    exotic: set[str] = set()
    for weapon_type in job_data.get('weapons', {}):
        ws_file = data_dir / 'weapon_skills' / (weapon_type.replace(' ', '_').replace('-', '_') + '.yml')
        if not ws_file.exists():
            continue
        for ws in _load(ws_file).get('skills', []):
            name = ws.get('name')
            if not name:
                continue
            if ws.get('acquisition') != 'weapon_specific':
                continue
            allowed = ws.get('jobs')
            if allowed and job not in allowed:
                continue
            exotic.add(name)
    return exotic


def _build_spell_target_map(data_dir: Path) -> dict[str, str]:
    """Build {spell_name: '<me>'|'<t>'} from magic catalog files."""
    targets: dict[str, str] = {}
    for path in (data_dir / 'magic').glob('*.yml'):
        catalog = _load(path)
        default_self = catalog.get('default_self', False)
        for spell in catalog.get('spells', []):
            name = spell.get('name')
            if not name:
                continue
            self_only = spell.get('self_only', default_self)
            targets[name] = '<me>' if self_only else '<t>'
    return targets


# ── Action resolution ─────────────────────────────────────────────────────────

def _resolve_series(name: str, sub_tier: Optional[int],
                    spells: set[str], name_to_series: dict, series_members: dict
                    ) -> Optional[str]:
    root = name_to_series.get(name, name)
    members = series_members.get(root, [name])
    available = [m for m in members if m in spells]
    if not available:
        return None
    if sub_tier is None:
        return available[-1]
    target_idx = len(available) - 1 - sub_tier
    return available[target_idx] if target_idx >= 0 else None


def _resolve_action(entry: dict, group_name: str, is_hub: bool,
                    spells: set, abilities: set, ws_names: set, wyvern: set,
                    job_data: dict, spell_targets: dict, ability_data: dict,
                    name_to_series: dict, series_members: dict
                    ) -> Optional[dict]:
    """
    Resolve one spoke action entry to a concrete macro.
    Returns None if the action is unavailable at this level.
    """
    name     = entry['name']
    sub_tier = entry.get('sub_tier')
    exact    = entry.get('exact', False)
    priority = entry.get('priority', 'mid')

    # ── Ranged attack ─────────────────────────────────────────────────────────
    if name == 'Ranged Attack' and name in abilities:
        return {
            'display':  'RngAtk',
            'cmd':      '/ra',
            'resolved': 'Ranged Attack',
            'target':   '<t>',
            'priority': priority,
        }

    # ── Spell (including series resolution) ───────────────────────────────────
    # exact=True: check only this specific spell name, never upgrade to a higher tier
    if exact:
        resolved = name if name in spells else None
    else:
        resolved = _resolve_series(name, sub_tier, spells, name_to_series, series_members)
    if resolved:
        if is_hub:
            target = '<me>'  # hub spells are always reactive self-buffs
        elif group_name in SELF_GROUPS:
            target = '<me>'
        elif group_name in ENEMY_GROUPS:
            target = '<t>'
        else:
            target = spell_targets.get(resolved, '<t>')
        return {
            'display': _abbrev(resolved),
            'cmd': '/ma',
            'resolved': resolved,
            'target': target,
            'priority': priority,
        }

    # ── Job ability ───────────────────────────────────────────────────────────
    if name in abilities:
        ab = ability_data.get(name, {})
        default_self = job_data.get('abilities_default_self', True)
        self_only = ab.get('self_only', default_self)
        return {
            'display': _abbrev(name),
            'cmd': '/ja',
            'resolved': name,
            'target': '<me>' if self_only else '<t>',
            'priority': priority,
        }

    # ── Weapon skill ──────────────────────────────────────────────────────────
    if name in ws_names:
        return {
            'display': _abbrev(name),
            'cmd': '/ws',
            'resolved': name,
            'target': '<t>',
            'priority': priority,
        }

    # ── Wyvern command ────────────────────────────────────────────────────────
    if name in wyvern:
        cmd_def = next((c for c in job_data.get('wyvern_commands', []) if c.get('name') == name), {})
        default_self = job_data.get('abilities_default_self', True)
        self_only = cmd_def.get('self_only', default_self)
        return {
            'display': _abbrev(name),
            'cmd': '/ja',
            'resolved': name,
            'target': '<me>' if self_only else '<t>',
            'priority': priority,
        }

    return None  # not available at this level


# ── Family resolution ─────────────────────────────────────────────────────────

def _family_of(group_name: str, explicit_family: Optional[str]) -> Optional[str]:
    if group_name.startswith('ws_'):
        return 'ws'
    if explicit_family:
        return explicit_family
    for fam, members in FAMILY_DEFS.items():
        if group_name in members:
            return fam
    return None


def _resolve_families(groups: list) -> list:
    """
    Groups in the same family merge into one set if combined unique actions ≤ MAX_CONTENT.
    When merging, duplicate actions are deduplicated; the higher priority wins across groups.
    """
    original_order = {g['name']: i for i, g in enumerate(groups)}
    family_map: dict[str, list] = {}
    standalone: list = []

    for g in groups:
        fam = _family_of(g['name'], g.get('family'))
        if fam:
            family_map.setdefault(fam, []).append(g)
        else:
            standalone.append(g)

    result: list = []
    for fam, members in family_map.items():
        if len(members) == 1:
            result.append(members[0])
            continue

        # Build merged action list — dedup by resolved name, higher priority wins
        seen: dict[str, dict] = {}
        merged: list[dict] = []
        for g in members:
            for a in g.get('actions', []):
                key = a['resolved']
                if key in seen:
                    seen[key]['priority'] = _higher_priority(
                        seen[key]['priority'], a.get('priority', 'mid')
                    )
                else:
                    action = dict(a)
                    seen[key] = action
                    merged.append(action)

        if len(merged) <= MAX_CONTENT:
            result.append({
                'name': fam,
                'type': members[0].get('type', 'spoke'),
                'family': fam,
                'label': fam.replace('_', ' ').title(),
                'actions': merged,
                '_merged_from': [g['name'] for g in members],
            })
        else:
            result.extend(members)

    result.extend(standalone)

    # Restore relative order: cores before spokes, within each tier by original file order
    def _sort_key(g):
        names = g.get('_merged_from', [g['name']])
        return min(original_order.get(n, 999) for n in names)

    cores  = sorted([g for g in result if g.get('type') == 'core'],  key=_sort_key)
    spokes = sorted([g for g in result if g.get('type') != 'core'], key=_sort_key)
    return cores + spokes


# ── Nav helpers ───────────────────────────────────────────────────────────────

def _nav_entry(book: int, set_no: int, label: str) -> dict:
    return {'name': label, 'contents': [f'/macro book {book}', f'/macro set {set_no}']}

def _action_slot(action: dict) -> dict:
    cmd = action['cmd']
    if cmd == '/ra':
        line = f'/ra {action["target"]}'
    else:
        line = f'{cmd} "{action["resolved"]}" {action["target"]}'
    return {'name': action['display'], 'contents': [line]}

def _two_hour_slot(two_hour: dict) -> dict:
    return _action_slot(two_hour)


# ── Slot assignment ───────────────────────────────────────────────────────────

def _build_set(actions: list, two_hour: Optional[dict],
               fixed_alt: dict  # {slot: nav_dict_or_None}
               ) -> dict:
    """
    Assign actions to ctrl/alt slots and wire nav.
    two_hour occupies Ctrl+0 (hub only).
    fixed_alt pre-assigns Alt slots; None entries are blank (omitted from output).
    Low-priority actions fill remaining Alt slots after nav.
    """
    ctrl: dict = {}
    alt:  dict = {}

    if two_hour:
        ctrl[0] = _two_hour_slot(two_hour)

    high = [a for a in actions if a.get('priority') == 'high']
    mid  = [a for a in actions if a.get('priority') == 'mid']
    low  = [a for a in actions if a.get('priority') == 'low']

    # Ctrl+1-5: high priority
    for slot, action in zip([1, 2, 3, 4, 5], high):
        ctrl[slot] = _action_slot(action)
    overflow_high = high[5:]

    # Ctrl+6-9 (hub, 0 reserved) or Ctrl+6-0 (non-hub)
    mid_ctrl = [6, 7, 8, 9] if two_hour else [6, 7, 8, 9, 0]
    all_mid = overflow_high + mid
    for slot, action in zip(mid_ctrl, all_mid):
        ctrl[slot] = _action_slot(action)
    overflow_mid = all_mid[len(mid_ctrl):]

    # Alt nav (fixed_alt) + low-priority actions in remaining Alt slots
    used_alt = set(fixed_alt.keys())
    for slot, nav in fixed_alt.items():
        if nav is not None:
            alt[slot] = nav

    low_actions = overflow_mid + low
    remaining_alt = [s for s in ALT_SLOTS if s not in used_alt]
    for slot, action in zip(remaining_alt, low_actions):
        alt[slot] = _action_slot(action)

    out: dict = {}
    if ctrl:
        out['ctrl'] = ctrl
    if alt:
        out['alt'] = alt
    return out


# ── Book builder ──────────────────────────────────────────────────────────────

def build_job_book(job: str, level: int, spoke_def: dict, job_data: dict,
                   data_dir: Path, book_num: int,
                   name_to_series: dict, series_members: dict,
                   spell_targets: dict) -> dict:

    cutoff = spoke_def.get('ws_rank_cutoff', 'B-')
    spells    = _avail_spells(job_data, data_dir, level)
    abilities = _avail_abilities(job_data, level)
    ws_names  = _avail_ws(job_data, data_dir, level, cutoff)
    wyvern    = _avail_wyvern(job_data, level)

    # Build ability lookup map (abilities + wyvern commands) for target resolution
    ability_data: dict[str, dict] = {ab['name']: ab for ab in job_data.get('abilities', [])}
    for cmd in job_data.get('wyvern_commands', []):
        ability_data[cmd['name']] = cmd

    two_hour_name = job_data.get('two_hour_ability')
    if not two_hour_name:
        sys.exit(f'error: {job} missing two_hour_ability in game data')
    two_hour = {
        'display': _abbrev(two_hour_name),
        'cmd': '/ja',
        'resolved': two_hour_name,
        'target': '<me>',
        'priority': 'high',
    }

    # Resolve hub actions
    hubs_raw = spoke_def.get('hubs', [])
    resolved_hubs = []
    for hub in hubs_raw:
        acts = []
        for entry in hub.get('actions', []):
            r = _resolve_action(entry, hub['name'], is_hub=True,
                                spells=spells, abilities=abilities, ws_names=ws_names,
                                wyvern=wyvern, job_data=job_data,
                                spell_targets=spell_targets, ability_data=ability_data,
                                name_to_series=name_to_series, series_members=series_members)
            if r:
                acts.append(r)
        resolved_hubs.append({**hub, 'actions': acts})

    # Resolve group actions
    resolved_groups = []
    for group in spoke_def.get('groups', []):
        acts = []
        for entry in group.get('actions', []):
            r = _resolve_action(entry, group['name'], is_hub=False,
                                spells=spells, abilities=abilities, ws_names=ws_names,
                                wyvern=wyvern, job_data=job_data,
                                spell_targets=spell_targets, ability_data=ability_data,
                                name_to_series=name_to_series, series_members=series_members)
            if r:
                acts.append(r)
        if acts:
            resolved_groups.append({**group, 'actions': acts})

    # Family merge/split
    final_groups = _resolve_families(resolved_groups)

    # Assign set numbers: hubs → cores → spokes (all in file order)
    num_hubs = len(resolved_hubs)
    is_dual  = num_hubs == 2
    hub_sets = list(range(1, num_hubs + 1))

    next_set = num_hubs + 1
    cores  = [g for g in final_groups if g.get('type') == 'core']
    spokes = [g for g in final_groups if g.get('type') != 'core']

    core_set_nums:  dict[str, int] = {}
    spoke_set_nums: dict[str, int] = {}
    for g in cores:
        core_set_nums[g['name']] = next_set; next_set += 1
    for g in spokes:
        spoke_set_nums[g['name']] = next_set; next_set += 1

    # Nav entries
    jobshub_nav = _nav_entry(1, 1, 'SJobHub')
    hub_navs = [_nav_entry(book_num, s, _nav_label(h.get('label', h['name'])))
                for h, s in zip(resolved_hubs, hub_sets)]
    core_navs  = {g['name']: _nav_entry(book_num, core_set_nums[g['name']],
                                         _group_nav_label(g['name'], g.get('label')))
                  for g in cores}
    spoke_navs = {g['name']: _nav_entry(book_num, spoke_set_nums[g['name']],
                                          _group_nav_label(g['name'], g.get('label')))
                  for g in spokes}
    all_content_navs = list(core_navs.values()) + list(spoke_navs.values())

    sets: dict = {}

    # ── Hub sets ───────────────────────────────────────────────────────────────
    for hub_idx, (hub, set_no) in enumerate(zip(resolved_hubs, hub_sets)):
        fixed: dict = {0: jobshub_nav}

        if is_dual:
            other_nav = hub_navs[1 - hub_idx]
            if hub_idx == 0:
                # Hub A: Alt+1 = Hub B toggle, Alt+2 = Hub B (spoke consistency)
                fixed[1] = other_nav
                fixed[2] = other_nav
            else:
                # Hub B: Alt+1 = Hub A toggle, Alt+2 = blank (Hub B is here)
                fixed[1] = other_nav
                fixed[2] = None
        else:
            fixed[1] = None  # blank — nothing to toggle to on single-hub job

        # Fill remaining Alt slots with core then spoke nav
        free = [s for s in ALT_SLOTS if s not in fixed]
        for slot, nav in zip(free, all_content_navs):
            fixed[slot] = nav

        sets[set_no] = _build_set(hub['actions'], two_hour, fixed)

    # ── Non-hub Alt prefix: hub nav + optional core nav ───────────────────────
    def _nonhub_fixed(include_cores: bool) -> dict:
        fa: dict = {1: hub_navs[0]}
        if is_dual:
            fa[2] = hub_navs[1]
        if include_cores:
            free = [s for s in ALT_SLOTS if s not in fa]
            for slot, nav in zip(free, list(core_navs.values())):
                fa[slot] = nav
        return fa

    # ── Core sets ──────────────────────────────────────────────────────────────
    for g in cores:
        sets[core_set_nums[g['name']]] = _build_set(g['actions'], None,
                                                      _nonhub_fixed(include_cores=False))

    # ── Spoke sets ─────────────────────────────────────────────────────────────
    for g in spokes:
        sets[spoke_set_nums[g['name']]] = _build_set(g['actions'], None,
                                                       _nonhub_fixed(include_cores=bool(cores)))

    return {'name': job[:15], 'sets': sets}


# ── JobsHub ───────────────────────────────────────────────────────────────────

def build_jobshub(assignments: list) -> dict:
    """Build the JobsHub book from (book_num, label) pairs."""
    ctrl: dict = {}
    alt:  dict = {}
    for i, (book_num, label) in enumerate(assignments):
        btn = _nav_entry(book_num, 1, _abbrev(label, 8))
        if i < 10:
            ctrl[CTRL_SLOTS[i]] = btn
        elif i - 10 < 10:
            alt[ALT_SLOTS[i - 10]] = btn
    sets: dict = {1: {}}
    if ctrl:
        sets[1]['ctrl'] = ctrl
    if alt:
        sets[1]['alt'] = alt
    return {'name': 'JobsHub', 'sets': sets}


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Build a complete character macro set from spoke definitions + game data'
    )
    parser.add_argument('character',
                        help='Character name (must have characters/NAME/manifest.yml)')
    parser.add_argument('--out', '-o', metavar='FILE',
                        help='Output path (default: out/NAME.yml)')
    parser.add_argument('--char', metavar='CHARNAME',
                        help='Import directly into macromog for CHARNAME')
    args = parser.parse_args()

    manifest_path = CHARS_DIR / args.character / 'manifest.yml'
    if not manifest_path.exists():
        sys.exit(f'error: manifest not found at {manifest_path}')
    manifest = _load(manifest_path)

    name_to_series, series_members = build_series_map(DATA_DIR)
    spell_targets = _build_spell_target_map(DATA_DIR)

    books: dict = {}
    assignments: list = []  # (book_num, label)

    next_book = 2
    for config in manifest.get('configurations', []):
        job = config['job'].upper()
        level = config.get('level', 99)
        book_num = config.get('book', next_book)
        next_book = max(next_book, book_num) + 1

        spoke_path   = SPOKES_DIR / f'{job}.yml'
        job_data_path = DATA_DIR / 'jobs' / f'{job}.yml'
        if not spoke_path.exists():
            sys.exit(f'error: no spoke definition at {spoke_path}')
        if not job_data_path.exists():
            sys.exit(f'error: no job data at {job_data_path}')

        spoke_def = _load(spoke_path)
        job_data  = _load(job_data_path)

        book = build_job_book(job, level, spoke_def, job_data, DATA_DIR, book_num,
                              name_to_series, series_members, spell_targets)
        books[book_num] = book

        def _job_label(sdef: dict, fallback: str) -> str:
            explicit = sdef.get('label')
            return explicit if explicit else _abbrev(sdef.get('name', fallback), 8)

        if 'display' in config:
            job_display = config['display'][:8]
        elif 'subjob' in config:
            # combo: always use 3-letter abbreviations — "RDM/WHM" fits in 7 chars
            job_display = f'{job}/{config["subjob"].upper()}'
        else:
            job_display = _job_label(spoke_def, job)
        assignments.append((book_num, job_display))

    books[1] = build_jobshub(assignments)
    all_books = sorted(books.keys())

    output = {
        'version': 1,
        'scope': {
            'level': 'book',
            'selections': [{'book': n} for n in all_books],
        },
        'books': books,
    }

    yaml_str = yaml.dump(output, default_flow_style=False, allow_unicode=True,
                         sort_keys=False)

    if args.char:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False,
                                          prefix=f'ffxi_{args.character}_') as tmp:
            tmp.write(yaml_str)
            tmp_path = Path(tmp.name)
        try:
            subprocess.run(
                ['macromog', 'import', '--char-name', args.char, str(tmp_path)],
                check=True,
            )
        finally:
            tmp_path.unlink(missing_ok=True)
    else:
        out_path = Path(args.out) if args.out else OUT_DIR / f'{args.character}.yml'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(yaml_str)
        print(f'Written to {out_path}', file=sys.stderr)


if __name__ == '__main__':
    main()

# Version: 0.1.0 | 2026-11-02
"""WP-1.6 / spec §6.4: local JSON slots and member exports.

Structural validation lives here until WP-3.1 supplies semantic persistence
validation. Callers can inject that validator without changing the file boundary.
"""
import json
from pathlib import Path
import re
from typing import Callable, get_type_hints

from cradle.engine.errors import SaveError
from cradle.engine.types import MemberDTO, SaveDoc, SlotInfo
from cradle.platform.config import Paths


def validate_structure(doc: object) -> None:
    if not isinstance(doc, dict):
        raise SaveError('save must be an object')
    if type(doc.get('schema_version')) is not int or doc['schema_version'] != 1:
        raise SaveError('unsupported schema_version (expected 1)')
    for name, kind in {'rng_state': dict, 'tick': int, 'clock_days': int, 'roster': list,
                       'expedition': dict, 'world': dict, 'treasury': int, 'config_echo': dict}.items():
        if type(doc.get(name)) is not kind:
            raise SaveError(f'invalid or missing {name}')
    if doc['tick'] < 0 or doc['clock_days'] < 0 or not 0 <= doc['treasury'] <= 65000:
        raise SaveError('save counter or treasury out of range')
    if len(doc['roster']) > 30:
        raise SaveError('roster exceeds 30 slots')
    for name, kind in {'site_states': dict, 'one_time_flags': dict, 'infamy': int,
                       'milestone': int, 'quest_score': int}.items():
        if type(doc['world'].get(name)) is not kind:
            raise SaveError(f'invalid or missing world.{name}')


def validate_member(doc: object) -> None:
    if not isinstance(doc, dict):
        raise SaveError('member must be an object')
    missing = MemberDTO.__required_keys__ - doc.keys()
    if missing:
        raise SaveError(f'member missing fields: {", ".join(sorted(missing))}')
    for key, hint in get_type_hints(MemberDTO).items():
        if hint in (int, bool, str) and type(doc[key]) is not hint:
            raise SaveError(f'invalid member.{key}')
    if not 1 <= doc['id'] <= 30 or not 0 <= doc['credit'] <= 65000:
        raise SaveError('member id or credit out of range')
    if not 1 <= doc['level'] <= 20:
        raise SaveError('member level out of range')
    if not isinstance(doc['items'], list) or len(doc['items']) > 9:
        raise SaveError('member kit exceeds 9 items or is invalid')


def _read(path: Path) -> dict:
    try:
        doc = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError) as exc:
        raise SaveError(f'{path.name}: cannot read JSON: {exc}') from exc
    if not isinstance(doc, dict):
        raise SaveError(f'{path.name}: document must be an object')
    return doc


def _write(path: Path, doc: dict) -> Path:
    temp = path.with_suffix('.json.tmp')
    try:
        # Serialize before touching any existing save.
        payload = json.dumps(doc, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
        path.parent.mkdir(parents=True, exist_ok=True)
        temp.write_text(payload, encoding='utf-8')
        temp.replace(path)
    except (OSError, TypeError, ValueError) as exc:
        temp.unlink(missing_ok=True)
        raise SaveError(f'{path.name}: cannot write JSON: {exc}') from exc
    return path


def _slot_path(paths: Paths, slot: int) -> Path:
    if type(slot) is not int or not 0 <= slot <= 4:
        raise SaveError('slot must be an integer in 0..4')
    return paths.saves / f'slot{slot}.json'


def write_slot(slot: int, doc: SaveDoc, *, paths: Paths,
               validator: Callable[[dict], None] = validate_structure) -> Path:
    path = _slot_path(paths, slot)
    validate_structure(doc)
    validator(doc)
    return _write(path, doc)


def read_slot(slot: int, *, paths: Paths,
              validator: Callable[[dict], None] = validate_structure) -> SaveDoc:
    doc = _read(_slot_path(paths, slot))
    validate_structure(doc)
    validator(doc)
    return doc


def list_slots(*, paths: Paths) -> list[SlotInfo]:
    return [{'slot': slot, 'exists': _slot_path(paths, slot).is_file(),
             'label': 'Autosave' if slot == 0 else f'Slot {slot}'} for slot in range(5)]


def backup_member(m: MemberDTO, *, paths: Paths,
                  validator: Callable[[dict], None] = validate_member) -> Path:
    validate_member(m)
    validator(m)
    return _write(paths.backups / f'member{m["id"]}.json', {'schema_version': 1, 'member': m})


def restore_member(name: str, *, paths: Paths,
                   validator: Callable[[dict], None] = validate_member) -> MemberDTO:
    if not isinstance(name, str) or re.fullmatch(r'member(?:[1-9]|[12][0-9]|30)\.json', name) is None:
        raise SaveError('backup filename must be member1.json..member30.json')
    path = paths.backups / name
    if path.is_symlink():
        raise SaveError('backup symlinks are not supported')
    doc = _read(path)
    if type(doc.get('schema_version')) is not int or doc['schema_version'] != 1:
        raise SaveError('unsupported backup schema_version')
    member = doc.get('member')
    validate_member(member)
    validator(member)
    return member


def erase_all(confirm: bool, *, paths: Paths) -> None:
    if confirm is not True:
        return
    # Erase active slots only. Member exports are separate storage (FR-SAV-003).
    for slot in range(5):
        path = _slot_path(paths, slot)
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise SaveError(f'{path.name}: cannot erase: {exc}') from exc

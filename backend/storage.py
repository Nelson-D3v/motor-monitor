"""
Storage layer — JSON file-based persistence.
Fully decoupled: swap for SQLite/Postgres without touching UI code.
"""

import json
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from backend.models import Equipment, SensorReading

DATA_DIR = Path(__file__).parent.parent / "data"
EQUIPMENT_FILE = DATA_DIR / "equipment.json"
READINGS_FILE = DATA_DIR / "readings.json"


def _ensure_files():
    DATA_DIR.mkdir(exist_ok=True)
    if not EQUIPMENT_FILE.exists():
        EQUIPMENT_FILE.write_text(json.dumps([], indent=2))
    if not READINGS_FILE.exists():
        READINGS_FILE.write_text(json.dumps([], indent=2))


def _load_equipment() -> List[dict]:
    _ensure_files()
    return json.loads(EQUIPMENT_FILE.read_text())


def _save_equipment(records: List[dict]):
    EQUIPMENT_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False))


def _load_readings() -> List[dict]:
    _ensure_files()
    return json.loads(READINGS_FILE.read_text())


def _save_readings(records: List[dict]):
    READINGS_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False))


# ── Equipment CRUD ──────────────────────────────────────────────────────────

def get_all_equipment() -> List[Equipment]:
    return [Equipment.from_dict(e) for e in _load_equipment()]


def get_equipment_by_id(equipment_id: str) -> Optional[Equipment]:
    records = _load_equipment()
    for r in records:
        if r["id"] == equipment_id:
            return Equipment.from_dict(r)
    return None


def get_equipment_by_tag(tag: str) -> Optional[Equipment]:
    records = _load_equipment()
    for r in records:
        if r["tag"].upper() == tag.upper():
            return Equipment.from_dict(r)
    return None


def save_equipment(equipment: Equipment) -> Equipment:
    """Insert or update an equipment record."""
    records = _load_equipment()
    equipment.updated_at = datetime.now().isoformat()
    for i, r in enumerate(records):
        if r["id"] == equipment.id:
            records[i] = equipment.to_dict()
            _save_equipment(records)
            return equipment
    records.append(equipment.to_dict())
    _save_equipment(records)
    return equipment


def delete_equipment(equipment_id: str) -> bool:
    records = _load_equipment()
    new_records = [r for r in records if r["id"] != equipment_id]
    if len(new_records) == len(records):
        return False
    _save_equipment(new_records)
    return True


def tag_exists(tag: str, exclude_id: Optional[str] = None) -> bool:
    records = _load_equipment()
    for r in records:
        if r["tag"].upper() == tag.upper():
            if exclude_id and r["id"] == exclude_id:
                continue
            return True
    return False


# ── Sensor Readings ─────────────────────────────────────────────────────────

def get_readings_for_equipment(equipment_id: str) -> List[SensorReading]:
    records = _load_readings()
    return [SensorReading.from_dict(r) for r in records if r["equipment_id"] == equipment_id]


def save_reading(reading: SensorReading) -> SensorReading:
    records = _load_readings()
    records.append(reading.to_dict())
    _save_readings(records)
    return reading


def delete_readings_for_equipment(equipment_id: str):
    records = _load_readings()
    _save_readings([r for r in records if r["equipment_id"] != equipment_id])

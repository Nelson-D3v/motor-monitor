"""
Seed script — generates realistic mock data for demo/development.

Sprint 2 update:
  - 7 days of readings at 30-min intervals (336 readings per motor)
  - MOT-001: progressive bearing-overheating fault scenario
  - MOT-003 relocated to Bloco A for area-navigation demo
  - --force flag clears existing data before seeding

Run:
    python seed_data.py            # skip existing
    python seed_data.py --force    # clear all and regenerate
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import random
from datetime import datetime, timedelta
from backend.models import Equipment, SensorReading
import backend.storage as storage


SEED_EQUIPMENT = [
    {
        "tag": "MOT-001",
        "model": "W22 IR3 Premium",
        "manufacturer": "WEG",
        "power_kw": 75.0,
        "voltage_v": 380.0,
        "current_a": 144.0,
        "frequency_hz": 60.0,
        "rpm": 1780,
        "frame": "IEC 250M",
        "protection_class": "IP55",
        "insulation_class": "F",
        "installation_location": "Sala de Bombas — Bloco A",
        "responsible_technician": "Carlos Ferreira",
        "notes": "Motor principal da bomba centrífuga P-101.",
        "status": "active",
    },
    {
        "tag": "MOT-002",
        "model": "M3BP 315 SMC",
        "manufacturer": "ABB",
        "power_kw": 132.0,
        "voltage_v": 440.0,
        "current_a": 232.0,
        "frequency_hz": 60.0,
        "rpm": 1475,
        "frame": "IEC 315M",
        "protection_class": "IP65",
        "insulation_class": "H",
        "installation_location": "Compressor — Linha 2",
        "responsible_technician": "Ana Lima",
        "notes": "Acoplado a compressor de ar industrial.",
        "status": "active",
    },
    {
        "tag": "MOT-003",
        "model": "1LE1002",
        "manufacturer": "Siemens",
        "power_kw": 22.0,
        "voltage_v": 220.0,
        "current_a": 59.0,
        "frequency_hz": 60.0,
        "rpm": 1760,
        "frame": "IEC 180L",
        "protection_class": "IP54",
        "insulation_class": "F",
        "installation_location": "Transportador — Bloco A",
        "responsible_technician": "Ricardo Souza",
        "notes": "Transportador de esteira — saída da linha de montagem.",
        "status": "maintenance",
    },
]


def _noise(x: float, pct: float = 0.05) -> float:
    return max(0.0, x * (1.0 + random.uniform(-pct, pct)))


def _spike(x: float, chance: float = 0.05, magnitude: float = 1.15) -> float:
    return x * magnitude if random.random() < chance else x


def generate_readings(equipment: Equipment, days: int = 7, interval_min: int = 30) -> list:
    """
    Generate sensor readings for the given equipment over `days` days.

    MOT-001 gets a progressive bearing-overheating fault scenario:
      - Days 0-4  : Normal operation (~40-60 °C)
      - Day  4-5  : Temperature rising into WARNING zone (~60-82 °C)
      - Day  5-6  : Escalating WARNING → CRITICAL (~82-102 °C) + vibration rise
      - Day  6-7  : Full CRITICAL (~100-115 °C), vibration WARNING
    """
    from utils.unit_converter import ADC_RESOLUTION, VOLTAGE_SENSOR_MAX_V, CURRENT_SENSOR_MAX_A

    raw_v_nom   = (equipment.voltage_v / VOLTAGE_SENSOR_MAX_V) * ADC_RESOLUTION
    raw_a_nom   = (equipment.current_a / CURRENT_SENSOR_MAX_A) * ADC_RESOLUTION
    raw_rpm_nom = equipment.rpm / 60.0

    # Reference end-time: 2026-05-20 18:00 (today, Sprint 2 demo date)
    now = datetime(2026, 5, 20, 18, 0, 0)
    total = int(days * 24 * 60 / interval_min)   # 336 readings for 7 days

    readings = []
    for i in range(total):
        ts = (now - timedelta(minutes=interval_min * (total - i))).isoformat()
        day_offset = i / (24 * 60 / interval_min)   # 0.0 … ~6.98

        # ── Default: normal temperature & vibration ──────────────────────────
        # raw_temp ~1700  →  -20 + (1700/4095)*170 ≈ 50.6 °C
        raw_temp = _noise(1700, 0.10)
        raw_vibr = _noise(410,  0.20)   # ~1.6 g

        # ── MOT-001 fault scenario ────────────────────────────────────────────
        if equipment.tag == "MOT-001":
            if day_offset >= 6.0:
                # CRITICAL zone (day 6-7): temp 100-115 °C, vibration WARNING
                fault_p = (day_offset - 6.0) / 1.0   # 0 → 1
                raw_temp = _noise(2900 + fault_p * 300, 0.06)   # 2900 → 3200
                raw_vibr = _noise(900  + fault_p * 300, 0.12)   # 900  → 1200
            elif day_offset >= 5.0:
                # Escalating WARNING → CRITICAL (day 5-6): temp 82-102 °C
                fault_p = (day_offset - 5.0) / 1.0
                raw_temp = _noise(2400 + fault_p * 500, 0.07)   # 2400 → 2900
                raw_vibr = _noise(550  + fault_p * 350, 0.15)   # 550  → 900
            elif day_offset >= 4.0:
                # Rising WARNING (day 4-5): temp 60-82 °C
                fault_p = (day_offset - 4.0) / 1.0
                raw_temp = _noise(1900 + fault_p * 500, 0.08)   # 1900 → 2400
                raw_vibr = _noise(430  + fault_p * 120, 0.15)   # 430  → 550

        # ── MOT-003 slight voltage sag (explains maintenance status) ─────────
        if equipment.tag == "MOT-003" and day_offset >= 5.5:
            raw_v_nom_local = raw_v_nom * 0.88   # ~12 % voltage sag → WARNING
        else:
            raw_v_nom_local = raw_v_nom

        readings.append(SensorReading(
            equipment_id=equipment.id,
            timestamp=ts,
            raw_voltage=round(_spike(_noise(raw_v_nom_local if equipment.tag == "MOT-003" else raw_v_nom, 0.05)), 1),
            raw_current=round(_noise(raw_a_nom, 0.08), 1),
            raw_temperature=round(raw_temp, 1),
            raw_vibration=round(raw_vibr, 1),
            raw_rpm=round(_noise(raw_rpm_nom, 0.03), 2),
        ))
    return readings


def seed(force: bool = False):
    if force:
        print("⚠️   Force mode — clearing all data...")
        from pathlib import Path
        import json
        data_dir = Path(__file__).parent / "data"
        data_dir.mkdir(exist_ok=True)
        (data_dir / "equipment.json").write_text("[]", encoding="utf-8")
        (data_dir / "readings.json").write_text("[]", encoding="utf-8")

    print("🌱  Seeding demo data (Sprint 2)...")
    existing = {e.tag: e for e in storage.get_all_equipment()}

    for data in SEED_EQUIPMENT:
        tag = data["tag"]

        if tag in existing and not force:
            print(f"  ⚠️   {tag} already exists — skipping.")
            continue

        equip = Equipment(**data)
        storage.save_equipment(equip)
        readings = generate_readings(equip, days=7, interval_min=30)
        for r in readings:
            storage.save_reading(r)
        print(f"  ✅  {tag}  ({data['manufacturer']} {data['model']})  — {len(readings)} readings.")

    print("✅  Seed complete.")


if __name__ == "__main__":
    seed(force="--force" in sys.argv)

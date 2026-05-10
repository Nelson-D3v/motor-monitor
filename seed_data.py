"""
Seed script — generates realistic mock data for demo/development.
Run: python seed_data.py
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
        "installation_location": "Transportador — Esteira 3",
        "responsible_technician": "Ricardo Souza",
        "notes": "",
        "status": "maintenance",
    },
]


def generate_readings(equipment: Equipment, n: int = 48):
    """Generate n mock sensor readings for an equipment (last 24h, 30-min intervals)."""
    readings = []
    now = datetime.now()

    # Determine baseline raw values from nominal
    # Voltage: nominal V maps back to ADC
    from utils.unit_converter import ADC_RESOLUTION, VOLTAGE_SENSOR_MAX_V, CURRENT_SENSOR_MAX_A
    raw_v_nominal = (equipment.voltage_v / VOLTAGE_SENSOR_MAX_V) * ADC_RESOLUTION
    raw_a_nominal = (equipment.current_a / CURRENT_SENSOR_MAX_A) * ADC_RESOLUTION
    raw_rpm_nominal = equipment.rpm / 60.0   # pulses/sec

    for i in range(n):
        ts = (now - timedelta(minutes=30 * (n - i))).isoformat()
        # Add ±5% noise, occasional spikes
        noise = lambda x, pct=0.05: x * (1 + random.uniform(-pct, pct))
        spike = lambda x: x * random.choice([1] * 19 + [1.15])  # 5% chance spike

        readings.append(SensorReading(
            equipment_id=equipment.id,
            timestamp=ts,
            raw_voltage=round(spike(noise(raw_v_nominal)), 1),
            raw_current=round(noise(raw_a_nominal, 0.08), 1),
            raw_temperature=round(noise(1800, 0.12), 1),   # ~65°C
            raw_vibration=round(noise(410, 0.20), 1),      # ~1.6g
            raw_rpm=round(noise(raw_rpm_nominal, 0.03), 2),
        ))
    return readings


def seed():
    print("🌱  Seeding demo data...")
    existing = {e.tag for e in storage.get_all_equipment()}

    for data in SEED_EQUIPMENT:
        if data["tag"] in existing:
            print(f"  ⚠️  {data['tag']} already exists — skipping.")
            continue
        equip = Equipment(**data)
        storage.save_equipment(equip)
        readings = generate_readings(equip)
        for r in readings:
            storage.save_reading(r)
        print(f"  ✅  {data['tag']} created with {len(readings)} readings.")

    print("✅  Seed complete.")


if __name__ == "__main__":
    seed()

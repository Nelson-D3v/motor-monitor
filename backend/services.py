"""
Service layer — business logic and orchestration.
This is the contract between UI and storage/model layers.
"""

import random
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from backend.models import Equipment, SensorReading, Alert
import backend.storage as storage
import backend.nlp as nlp
from utils.unit_converter import (
    convert_reading, ADC_RESOLUTION, VOLTAGE_SENSOR_MAX_V, CURRENT_SENSOR_MAX_A,
)


class EquipmentService:
    """Handles all equipment business operations."""

    @staticmethod
    def list_equipment() -> List[Equipment]:
        return storage.get_all_equipment()

    @staticmethod
    def get(equipment_id: str) -> Optional[Equipment]:
        return storage.get_equipment_by_id(equipment_id)

    @staticmethod
    def create(data: dict) -> Tuple[bool, str, Optional[Equipment]]:
        """Create a new equipment. Returns (success, message, equipment)."""
        tag = data.get("tag", "").strip().upper()
        if not tag:
            return False, "TAG de identificação é obrigatória.", None
        if storage.tag_exists(tag):
            return False, f"TAG '{tag}' já está cadastrada.", None

        equip = Equipment(
            tag=tag,
            model=data["model"],
            manufacturer=data["manufacturer"],
            power_kw=float(data["power_kw"]),
            voltage_v=float(data["voltage_v"]),
            current_a=float(data["current_a"]),
            frequency_hz=float(data["frequency_hz"]),
            rpm=int(data["rpm"]),
            frame=data["frame"],
            protection_class=data["protection_class"],
            insulation_class=data["insulation_class"],
            installation_location=data["installation_location"],
            responsible_technician=data["responsible_technician"],
            notes=data.get("notes", ""),
            status=data.get("status", "active"),
        )
        saved = storage.save_equipment(equip)
        return True, f"Equipamento '{tag}' cadastrado com sucesso.", saved

    @staticmethod
    def update(equipment_id: str, data: dict) -> Tuple[bool, str, Optional[Equipment]]:
        """Update an existing equipment."""
        equip = storage.get_equipment_by_id(equipment_id)
        if not equip:
            return False, "Equipamento não encontrado.", None

        tag = data.get("tag", equip.tag).strip().upper()
        if storage.tag_exists(tag, exclude_id=equipment_id):
            return False, f"TAG '{tag}' já está em uso por outro equipamento.", None

        equip.tag = tag
        equip.model = data.get("model", equip.model)
        equip.manufacturer = data.get("manufacturer", equip.manufacturer)
        equip.power_kw = float(data.get("power_kw", equip.power_kw))
        equip.voltage_v = float(data.get("voltage_v", equip.voltage_v))
        equip.current_a = float(data.get("current_a", equip.current_a))
        equip.frequency_hz = float(data.get("frequency_hz", equip.frequency_hz))
        equip.rpm = int(data.get("rpm", equip.rpm))
        equip.frame = data.get("frame", equip.frame)
        equip.protection_class = data.get("protection_class", equip.protection_class)
        equip.insulation_class = data.get("insulation_class", equip.insulation_class)
        equip.installation_location = data.get("installation_location", equip.installation_location)
        equip.responsible_technician = data.get("responsible_technician", equip.responsible_technician)
        equip.notes = data.get("notes", equip.notes)
        equip.status = data.get("status", equip.status)

        saved = storage.save_equipment(equip)
        return True, f"Equipamento '{tag}' atualizado com sucesso.", saved

    @staticmethod
    def delete(equipment_id: str) -> Tuple[bool, str]:
        equip = storage.get_equipment_by_id(equipment_id)
        if not equip:
            return False, "Equipamento não encontrado."
        storage.delete_readings_for_equipment(equipment_id)
        storage.delete_alerts_for_equipment(equipment_id)
        storage.delete_equipment(equipment_id)
        return True, f"Equipamento '{equip.tag}' removido com sucesso."


class SensorService:
    """Handles sensor readings."""

    @staticmethod
    def get_readings(equipment_id: str) -> List[SensorReading]:
        return storage.get_readings_for_equipment(equipment_id)

    @staticmethod
    def add_reading(reading: SensorReading) -> SensorReading:
        return storage.save_reading(reading)


class AlertService:
    """
    Analytics/alerting layer. Today it evaluates the latest sensor reading of
    each equipment against nominal thresholds (reusing the same rules as the
    Sprint 1/2 sensor pages); the NLP summary/recommendation text comes from
    backend.nlp. This is the seam where a real ML anomaly-detection model
    would plug in — it only needs to produce the same (parameter, severity,
    value, unit, nominal) tuples consumed by `_build_alert`.
    """

    PARAM_FIELDS = [
        ("Tensão", "voltage_v", "voltage_status", "V"),
        ("Corrente", "current_a", "current_status", "A"),
        ("Temperatura", "temperature_c", "temperature_status", "°C"),
        ("Vibração", "vibration_g", "vibration_status", "g"),
        ("Velocidade", "rpm", "rpm_status", "RPM"),
    ]

    @staticmethod
    def _build_alert(equipment: Equipment, parameter: str, value: float,
                      unit: str, severity: str, nominal: float) -> Alert:
        context = {
            "equipment_tag": equipment.tag,
            "parameter": parameter,
            "severity": severity,
            "value": value,
            "unit": unit,
            "nominal": nominal,
        }
        return Alert(
            equipment_id=equipment.id,
            equipment_tag=equipment.tag,
            parameter=parameter,
            severity=severity,
            value=value,
            unit=unit,
            nominal=nominal,
            message=f"{parameter} fora da faixa nominal ({value:g}{unit}, nominal {nominal:g}{unit})",
            summary=nlp.generate_alert_summary(context),
            recommendation=nlp.generate_recommendation(context),
        )

    @staticmethod
    def evaluate_equipment(equipment: Equipment) -> List[Alert]:
        """Check the latest reading of one equipment and return new alerts (not yet persisted)."""
        readings = storage.get_readings_for_equipment(equipment.id)
        if not readings:
            return []

        nominal = {"voltage_v": equipment.voltage_v, "current_a": equipment.current_a, "rpm": equipment.rpm}
        readings_sorted = sorted(readings, key=lambda r: r.timestamp)
        latest = convert_reading(readings_sorted[-1].to_dict(), nominal)

        nominal_by_field = {
            "voltage_v": equipment.voltage_v,
            "current_a": equipment.current_a,
            "temperature_c": 60.0,
            "vibration_g": 1.5,
            "rpm": equipment.rpm,
        }

        new_alerts = []
        for label, field_name, status_field, unit in AlertService.PARAM_FIELDS:
            status = getattr(latest, status_field)
            if status == "ok":
                continue
            value = getattr(latest, field_name)
            new_alerts.append(AlertService._build_alert(
                equipment, label, value, unit, status, nominal_by_field[field_name]
            ))
        return new_alerts

    @staticmethod
    def scan_all(equipments: List[Equipment]) -> List[Alert]:
        """Evaluate every equipment, persist any new alerts, and return them."""
        found = []
        for eq in equipments:
            for alert in AlertService.evaluate_equipment(eq):
                storage.save_alert(alert)
                found.append(alert)
        return found

    @staticmethod
    def ensure_demo_signal(equipments: List[Equipment]) -> None:
        """
        Guarantee there is sensor data to analyze so the panel has something
        to show on a fresh install. Seeds a normal reading for equipment that
        doesn't have data yet. Fully isolated from the alerting logic above —
        AlertService.scan_all() is what turns readings into alerts.
        """
        for eq in equipments:
            if storage.get_readings_for_equipment(eq.id):
                continue

            raw_v_nom = (eq.voltage_v / VOLTAGE_SENSOR_MAX_V) * ADC_RESOLUTION
            raw_a_nom = (eq.current_a / CURRENT_SENSOR_MAX_A) * ADC_RESOLUTION
            raw_rpm_nom = eq.rpm / 60.0
            noise = lambda x, p=0.05: max(0, x * (1 + random.uniform(-p, p)))

            storage.save_reading(SensorReading(
                equipment_id=eq.id,
                timestamp=(datetime.now() - timedelta(minutes=5)).isoformat(),
                raw_voltage=round(noise(raw_v_nom), 1),
                raw_current=round(noise(raw_a_nom, 0.08), 1),
                raw_temperature=round(noise(1800, 0.1), 1),
                raw_vibration=round(noise(400, 0.15), 1),
                raw_rpm=round(noise(raw_rpm_nom, 0.03), 2),
            ))

    @staticmethod
    def inject_simulated_anomaly(equipment: Equipment) -> None:
        """Simulate a fresh anomalous reading for demo purposes (refresh/timer trigger)."""
        param = random.choice(["temperature", "vibration", "current"])
        raw_v_nom = (equipment.voltage_v / VOLTAGE_SENSOR_MAX_V) * ADC_RESOLUTION
        raw_a_nom = (equipment.current_a / CURRENT_SENSOR_MAX_A) * ADC_RESOLUTION
        raw_rpm_nom = equipment.rpm / 60.0

        raw_temperature = random.uniform(2400, 2900)   # ~ >100°C
        raw_vibration = random.uniform(1100, 2100)     # ~ >4g
        raw_current = raw_a_nom * random.uniform(1.15, 1.35)

        if param == "temperature":
            raw_temperature = random.uniform(2600, 2950)
        elif param == "vibration":
            raw_vibration = random.uniform(1300, 2200)
        else:
            raw_current = raw_a_nom * random.uniform(1.25, 1.4)

        storage.save_reading(SensorReading(
            equipment_id=equipment.id,
            timestamp=datetime.now().isoformat(),
            raw_voltage=round(raw_v_nom, 1),
            raw_current=round(raw_current, 1),
            raw_temperature=round(raw_temperature, 1),
            raw_vibration=round(raw_vibration, 1),
            raw_rpm=round(raw_rpm_nom, 2),
        ))

    @staticmethod
    def get_history(limit: int = 50) -> List[Alert]:
        alerts = storage.get_all_alerts()
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)[:limit]

    @staticmethod
    def equipment_state(equipment_id: str) -> str:
        """Return the equipment's current state: the worst severity among its open alerts."""
        alerts = [a for a in storage.get_all_alerts()
                  if a.equipment_id == equipment_id and a.status == "open"]
        if any(a.severity == "critical" for a in alerts):
            return "critical"
        if any(a.severity == "warning" for a in alerts):
            return "warning"
        return "ok"

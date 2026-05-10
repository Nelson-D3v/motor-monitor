"""
Service layer — business logic and orchestration.
This is the contract between UI and storage/model layers.
"""

from typing import List, Optional, Tuple
from backend.models import Equipment, SensorReading
import backend.storage as storage


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

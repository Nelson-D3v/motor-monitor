"""
Data models for the Motor Monitoring System.
Decoupled from any frontend framework.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Equipment:
    """Represents a registered industrial motor/equipment."""
    tag: str                          # Unique identification TAG (e.g. MOT-001)
    model: str
    manufacturer: str
    power_kw: float                   # Nominal power in kW
    voltage_v: float                  # Nominal voltage in V
    current_a: float                  # Nominal current in A
    frequency_hz: float               # Electrical frequency in Hz
    rpm: int                          # Nominal RPM
    frame: str                        # Frame size (e.g. IEC 160M)
    protection_class: str             # IP class (e.g. IP55)
    insulation_class: str             # Insulation class (e.g. F)
    installation_location: str
    responsible_technician: str
    notes: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "active"            # active | maintenance | decommissioned

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Equipment":
        return cls(**data)


@dataclass
class SensorReading:
    """Represents a raw sensor reading associated with an equipment."""
    equipment_id: str
    timestamp: str
    raw_voltage: float        # ADC raw value 0-4095 (12-bit)
    raw_current: float        # ADC raw value 0-4095
    raw_temperature: float    # ADC raw value 0-4095
    raw_vibration: float      # ADC raw value 0-4095
    raw_rpm: float            # Pulse counter raw value
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SensorReading":
        return cls(**data)


# Equipment status options
EQUIPMENT_STATUS = {
    "active": {"label": "Ativo", "color": "#22c55e"},
    "maintenance": {"label": "Manutenção", "color": "#f59e0b"},
    "decommissioned": {"label": "Descomissionado", "color": "#ef4444"},
}

# Insulation class options
INSULATION_CLASSES = ["A", "B", "F", "H"]

# Protection class options
PROTECTION_CLASSES = ["IP21", "IP44", "IP54", "IP55", "IP65", "IP66", "TEFC"]

# Common manufacturers
MANUFACTURERS = [
    "WEG", "ABB", "Siemens", "Nidec", "Voges", "SEW-Eurodrive",
    "Baldor", "Leroy-Somer", "Toshiba", "Outro"
]

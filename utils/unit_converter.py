"""
Unit conversion utilities.
Converts raw ADC/sensor values to meaningful engineering units.
Fully decoupled from UI — pure functions.
"""

from dataclasses import dataclass
from typing import Optional


# ── Sensor calibration constants ─────────────────────────────────────────────
# These represent typical sensor configurations; adjust per hardware.

ADC_RESOLUTION = 4095          # 12-bit ADC
ADC_VREF = 3.3                 # Reference voltage (V)

# Voltage sensor: ZMPT101B — maps 0–4095 to 0–500V AC (after rectification)
VOLTAGE_SENSOR_MAX_V = 500.0

# Current sensor: ACS712-30A — maps 0–4095 → 0–30A
CURRENT_SENSOR_MAX_A = 30.0

# Temperature sensor: NTC thermistor — maps 0–4095 → -20°C to 150°C
TEMP_SENSOR_MIN_C = -20.0
TEMP_SENSOR_MAX_C = 150.0

# Vibration sensor: ADXL345 — maps 0–4095 → 0–16g
VIBRATION_SENSOR_MAX_G = 16.0

# RPM sensor: Hall-effect pulse counter — raw pulses/sec × 60 = RPM
RPM_PULSES_PER_REV = 1         # 1 magnet per revolution


@dataclass
class ConvertedReading:
    """Engineering-unit representation of a sensor reading."""
    voltage_v: float
    current_a: float
    temperature_c: float
    vibration_g: float
    rpm: float
    power_kw: float             # Derived: V × I × PF × √3 (3-phase assumed)
    timestamp: str
    raw: dict                   # Original raw values preserved

    # Alarm thresholds (set by comparison with nominal)
    voltage_status: str = "ok"       # ok | warning | critical
    current_status: str = "ok"
    temperature_status: str = "ok"
    vibration_status: str = "ok"
    rpm_status: str = "ok"


def adc_to_voltage(raw: float) -> float:
    """Convert 12-bit ADC reading to voltage (V)."""
    return round((raw / ADC_RESOLUTION) * VOLTAGE_SENSOR_MAX_V, 2)


def adc_to_current(raw: float) -> float:
    """Convert 12-bit ADC reading to current (A)."""
    return round((raw / ADC_RESOLUTION) * CURRENT_SENSOR_MAX_A, 2)


def adc_to_temperature(raw: float) -> float:
    """Convert 12-bit ADC reading to temperature (°C)."""
    temp_range = TEMP_SENSOR_MAX_C - TEMP_SENSOR_MIN_C
    return round(TEMP_SENSOR_MIN_C + (raw / ADC_RESOLUTION) * temp_range, 1)


def adc_to_vibration(raw: float) -> float:
    """Convert 12-bit ADC reading to vibration (g)."""
    return round((raw / ADC_RESOLUTION) * VIBRATION_SENSOR_MAX_G, 3)


def pulses_to_rpm(raw_pulses_per_sec: float) -> float:
    """Convert pulse frequency to RPM."""
    return round((raw_pulses_per_sec / RPM_PULSES_PER_REV) * 60, 0)


def derive_power(voltage_v: float, current_a: float, power_factor: float = 0.85) -> float:
    """Derive active power (kW) from voltage and current (3-phase)."""
    return round((voltage_v * current_a * power_factor * 1.732) / 1000, 3)


def _threshold_status(value: float, nominal: float,
                      warn_pct: float = 0.10, crit_pct: float = 0.20) -> str:
    """Return 'ok', 'warning', or 'critical' based on deviation from nominal."""
    if nominal <= 0:
        return "ok"
    deviation = abs(value - nominal) / nominal
    if deviation >= crit_pct:
        return "critical"
    if deviation >= warn_pct:
        return "warning"
    return "ok"


def _temp_status(temp_c: float) -> str:
    if temp_c >= 100:
        return "critical"
    if temp_c >= 75:
        return "warning"
    return "ok"


def _vibration_status(g: float) -> str:
    if g >= 8.0:
        return "critical"
    if g >= 4.0:
        return "warning"
    return "ok"


def convert_reading(raw_reading: dict, nominal: Optional[dict] = None) -> ConvertedReading:
    """
    Convert a raw sensor reading dict to engineering units.

    Args:
        raw_reading: dict with keys raw_voltage, raw_current, raw_temperature,
                     raw_vibration, raw_rpm, timestamp, equipment_id
        nominal: dict with voltage_v, current_a, rpm for threshold comparison
    """
    v = adc_to_voltage(raw_reading["raw_voltage"])
    a = adc_to_current(raw_reading["raw_current"])
    t = adc_to_temperature(raw_reading["raw_temperature"])
    g = adc_to_vibration(raw_reading["raw_vibration"])
    r = pulses_to_rpm(raw_reading["raw_rpm"])
    p = derive_power(v, a)

    n = nominal or {}
    return ConvertedReading(
        voltage_v=v,
        current_a=a,
        temperature_c=t,
        vibration_g=g,
        rpm=r,
        power_kw=p,
        timestamp=raw_reading["timestamp"],
        raw={
            "raw_voltage": raw_reading["raw_voltage"],
            "raw_current": raw_reading["raw_current"],
            "raw_temperature": raw_reading["raw_temperature"],
            "raw_vibration": raw_reading["raw_vibration"],
            "raw_rpm": raw_reading["raw_rpm"],
        },
        voltage_status=_threshold_status(v, n.get("voltage_v", v)),
        current_status=_threshold_status(a, n.get("current_a", a)),
        temperature_status=_temp_status(t),
        vibration_status=_vibration_status(g),
        rpm_status=_threshold_status(r, n.get("rpm", r)),
    )

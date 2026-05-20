/**
 * Generates equipment.json and readings.json for Sprint 2 demo.
 * 7 days of data at 30-min intervals with MOT-001 fault scenario.
 * Run: node generate_seed.js
 */

const fs = require("fs");
const path = require("path");
const { randomUUID } = require("crypto");

const DATA_DIR = path.join(__dirname, "data");
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR);

// ── Equipment definitions ────────────────────────────────────────────────────
const EQUIPMENT = [
  {
    id: "7abf18fc-6962-4612-adb6-2c6a1b3c09ef",
    tag: "MOT-001",
    model: "W22 IR3 Premium",
    manufacturer: "WEG",
    power_kw: 75.0,
    voltage_v: 380.0,
    current_a: 144.0,
    frequency_hz: 60.0,
    rpm: 1780,
    frame: "IEC 250M",
    protection_class: "IP55",
    insulation_class: "F",
    installation_location: "Sala de Bombas — Bloco A",
    responsible_technician: "Carlos Ferreira",
    notes: "Motor principal da bomba centrífuga P-101.",
    created_at: "2026-05-13T08:00:00.000000",
    updated_at: "2026-05-20T17:00:00.000000",
    status: "active",
  },
  {
    id: "1fed6776-620c-402f-917a-d2a80c5dffe3",
    tag: "MOT-002",
    model: "M3BP 315 SMC",
    manufacturer: "ABB",
    power_kw: 132.0,
    voltage_v: 440.0,
    current_a: 232.0,
    frequency_hz: 60.0,
    rpm: 1475,
    frame: "IEC 315M",
    protection_class: "IP65",
    insulation_class: "H",
    installation_location: "Compressor — Linha 2",
    responsible_technician: "Ana Lima",
    notes: "Acoplado a compressor de ar industrial.",
    created_at: "2026-05-13T08:05:00.000000",
    updated_at: "2026-05-20T17:00:00.000000",
    status: "active",
  },
  {
    id: "902ac75d-9ea9-4ace-8007-bc6b2877bf4f",
    tag: "MOT-003",
    model: "1LE1002",
    manufacturer: "Siemens",
    power_kw: 22.0,
    voltage_v: 220.0,
    current_a: 59.0,
    frequency_hz: 60.0,
    rpm: 1760,
    frame: "IEC 180L",
    protection_class: "IP54",
    insulation_class: "F",
    installation_location: "Transportador — Bloco A",
    responsible_technician: "Ricardo Souza",
    notes: "Transportador de esteira — saída da linha de montagem.",
    created_at: "2026-05-13T08:10:00.000000",
    updated_at: "2026-05-19T14:30:00.000000",
    status: "maintenance",
  },
];

// ── Helpers ──────────────────────────────────────────────────────────────────
function noise(x, pct = 0.05) {
  return Math.max(0, x * (1 + (Math.random() * 2 - 1) * pct));
}

function spike(x, chance = 0.05, mag = 1.15) {
  return Math.random() < chance ? x * mag : x;
}

function round1(x) { return Math.round(x * 10) / 10; }
function round2(x) { return Math.round(x * 100) / 100; }

// ── ADC constants (mirrors unit_converter.py) ────────────────────────────────
const ADC_RES     = 4095;
const V_SENS_MAX  = 500.0;
const A_SENS_MAX  = 30.0;

// ── Generate readings for one equipment ──────────────────────────────────────
function generateReadings(eq, days = 7, intervalMin = 30) {
  // Reference end: 2026-05-20 18:00
  const endMs    = new Date("2026-05-20T18:00:00").getTime();
  const total    = Math.round(days * 24 * 60 / intervalMin);  // 336
  const readings = [];

  const rawVNom   = (eq.voltage_v  / V_SENS_MAX) * ADC_RES;
  const rawANom   = (eq.current_a  / A_SENS_MAX) * ADC_RES;
  const rawRpmNom = eq.rpm / 60.0;

  for (let i = 0; i < total; i++) {
    const tsMs      = endMs - (total - i) * intervalMin * 60000;
    const ts        = new Date(tsMs).toISOString().replace("Z", "").replace("T", "T");
    const dayOffset = i / (24 * 60 / intervalMin);  // 0 … ~6.98

    // Default: normal
    let rawTemp = noise(1700, 0.10);   // ~51 °C
    let rawVibr = noise(410,  0.18);   // ~1.6 g
    let rawVolt = spike(noise(rawVNom, 0.05));

    // ── MOT-001 fault scenario ──────────────────────────────────────────────
    if (eq.tag === "MOT-001") {
      if (dayOffset >= 6.0) {
        // CRITICAL: temp 100-115 °C + vibration WARNING
        const p = (dayOffset - 6.0) / 1.0;
        rawTemp = noise(2900 + p * 300, 0.06);
        rawVibr = noise(900  + p * 300, 0.10);
      } else if (dayOffset >= 5.0) {
        // Escalating WARNING→CRITICAL: temp 82-102 °C
        const p = (dayOffset - 5.0) / 1.0;
        rawTemp = noise(2400 + p * 500, 0.07);
        rawVibr = noise(550  + p * 350, 0.13);
      } else if (dayOffset >= 4.0) {
        // Rising WARNING: temp 60-82 °C
        const p = (dayOffset - 4.0) / 1.0;
        rawTemp = noise(1900 + p * 500, 0.08);
        rawVibr = noise(430  + p * 120, 0.15);
      }
    }

    // ── MOT-003 voltage sag (explains maintenance status) ───────────────────
    if (eq.tag === "MOT-003" && dayOffset >= 5.5) {
      rawVolt = spike(noise(rawVNom * 0.87, 0.05));  // ~-13% → WARNING→CRITICAL
    }

    readings.push({
      equipment_id:    eq.id,
      timestamp:       ts,
      raw_voltage:     round1(rawVolt),
      raw_current:     round1(noise(rawANom, 0.08)),
      raw_temperature: round1(rawTemp),
      raw_vibration:   round1(rawVibr),
      raw_rpm:         round2(noise(rawRpmNom, 0.03)),
      id:              randomUUID(),
    });
  }
  return readings;
}

// ── Write files ──────────────────────────────────────────────────────────────
fs.writeFileSync(
  path.join(DATA_DIR, "equipment.json"),
  JSON.stringify(EQUIPMENT, null, 2),
  "utf8"
);
console.log("✅  equipment.json written (" + EQUIPMENT.length + " motors)");

const allReadings = [];
for (const eq of EQUIPMENT) {
  const r = generateReadings(eq);
  allReadings.push(...r);
  console.log("   " + eq.tag + " — " + r.length + " readings generated");
}

fs.writeFileSync(
  path.join(DATA_DIR, "readings.json"),
  JSON.stringify(allReadings, null, 2),
  "utf8"
);
console.log("✅  readings.json written (" + allReadings.length + " total readings)");
console.log("🌱  Sprint 2 seed data ready.");

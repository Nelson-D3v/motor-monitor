"""
Sprint 2 — Dashboard de Telemetria
Visualização operacional, séries temporais e saúde dos ativos.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import random
from datetime import datetime, timedelta

from utils.ui_helpers import (
    inject_css, render_sidebar, badge_html,
    section_header, sensor_status_color,
)
from backend.services import EquipmentService, SensorService
from utils.unit_converter import convert_reading
from backend.models import SensorReading

st.set_page_config(
    page_title="MotorSync — Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
render_sidebar()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:8px;">
    <div style="font-family:'Barlow Condensed',sans-serif; font-size:28px;
                font-weight:700; color:#e6edf3; line-height:1;">
        Dashboard de Telemetria
    </div>
    <div style="font-size:13px; color:#8b949e; margin-top:2px;">
        Visualização operacional &nbsp;·&nbsp; Séries temporais &nbsp;·&nbsp;
        Estado de saúde dos ativos
    </div>
</div>
<hr style="border-color:#30363d; margin:12px 0 24px;">
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def _extract_area(location: str) -> str:
    for sep in (" — ", " - ", " – "):
        if sep in location:
            return location.split(sep)[-1].strip()
    return location.strip()


def _health(reading) -> tuple[int, str, str]:
    """Return (score 0-100, label, hex-color)."""
    statuses = [
        reading.temperature_status,
        reading.vibration_status,
        reading.current_status,
        reading.voltage_status,
        reading.rpm_status,
    ]
    crit = statuses.count("critical")
    warn = statuses.count("warning")
    score = max(0, 100 - crit * 25 - warn * 10)
    if crit:
        return score, "CRÍTICO", "#ef4444"
    if warn:
        return score, "ATENÇÃO", "#f59e0b"
    return score, "NORMAL", "#22c55e"


# ── Navigation — Area → TAG ───────────────────────────────────────────────────
equipments = EquipmentService.list_equipment()
if not equipments:
    st.warning("Nenhum equipamento cadastrado. Acesse **Cadastro** para adicionar ativos.", icon="⚠️")
    st.stop()

ALL_AREAS = "Todas as áreas"
areas = sorted(set(_extract_area(e.installation_location) for e in equipments))

col_area, col_tag, col_btn = st.columns([2, 3, 1])

with col_area:
    selected_area = st.selectbox(
        "Área",
        [ALL_AREAS] + areas,
        label_visibility="collapsed",
    )

filtered_eq = (
    equipments if selected_area == ALL_AREAS
    else [e for e in equipments if _extract_area(e.installation_location) == selected_area]
)

with col_tag:
    if not filtered_eq:
        st.info("Nenhum equipamento nesta área.")
        st.stop()
    tag_options = {
        f"{e.tag}  —  {e.manufacturer} {e.model}": e
        for e in sorted(filtered_eq, key=lambda x: x.tag)
    }
    selected_label = st.selectbox("TAG", list(tag_options.keys()),
                                  label_visibility="collapsed")

eq = tag_options[selected_label]

with col_btn:
    gen_btn = st.button("⚡ Simular", width="stretch",
                        help="Gera uma nova leitura simulada e salva no histórico")

# ── Simulate a new reading on demand ─────────────────────────────────────────
if gen_btn:
    from utils.unit_converter import ADC_RESOLUTION, VOLTAGE_SENSOR_MAX_V, CURRENT_SENSOR_MAX_A
    rv = (eq.voltage_v / VOLTAGE_SENSOR_MAX_V) * ADC_RESOLUTION
    ra = (eq.current_a / CURRENT_SENSOR_MAX_A) * ADC_RESOLUTION
    rr = eq.rpm / 60.0
    n  = lambda x, p=0.05: max(0.0, x * (1.0 + random.uniform(-p, p)))
    SensorService.add_reading(SensorReading(
        equipment_id=eq.id,
        timestamp=datetime.now().isoformat(),
        raw_voltage=round(n(rv), 1),
        raw_current=round(n(ra, 0.08), 1),
        raw_temperature=round(n(1800, 0.10), 1),
        raw_vibration=round(n(410, 0.18), 1),
        raw_rpm=round(n(rr, 0.03), 2),
    ))
    st.toast(f"Leitura gerada para {eq.tag}", icon="✅")
    st.rerun()

# ── Load & convert readings ───────────────────────────────────────────────────
raw_readings = SensorService.get_readings(eq.id)

if not raw_readings:
    st.info(
        f"Nenhum dado de sensor para **{eq.tag}**. "
        "Clique em **⚡ Simular** para gerar dados de demonstração.",
        icon="📡",
    )
    st.stop()

nominal   = {"voltage_v": eq.voltage_v, "current_a": eq.current_a, "rpm": eq.rpm}
readings_sorted = sorted(raw_readings, key=lambda r: r.timestamp)
converted = [convert_reading(r.to_dict(), nominal) for r in readings_sorted]
latest    = converted[-1]

# ── Equipment header + health ─────────────────────────────────────────────────
score, health_label, health_color = _health(latest)
badge   = badge_html(eq.status)
area_lbl = _extract_area(eq.installation_location)
try:
    last_ts = datetime.fromisoformat(latest.timestamp).strftime("%d/%m/%Y %H:%M")
except Exception:
    last_ts = latest.timestamp

st.markdown(f"""
<div style="background:#1c2128; border:1px solid {health_color}; border-radius:12px;
            padding:20px 24px; margin-bottom:24px;">
    <div style="display:flex; justify-content:space-between; align-items:flex-start;
                flex-wrap:wrap; gap:16px;">
        <div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:13px;
                        color:#f97316; font-weight:700; letter-spacing:0.05em;">{eq.tag}</div>
            <div style="font-family:'Barlow Condensed',sans-serif; font-size:24px;
                        font-weight:700; color:#e6edf3; margin:4px 0;">
                {eq.manufacturer} {eq.model}
            </div>
            <div style="font-size:13px; color:#8b949e;">
                📍 {eq.installation_location}
                &nbsp;·&nbsp; Área: <strong style="color:#e6edf3;">{area_lbl}</strong>
            </div>
        </div>
        <div style="text-align:right;">
            {badge}
            <div style="margin-top:12px; display:flex; align-items:center;
                        gap:8px; justify-content:flex-end;">
                <div style="font-size:11px; color:#484f58; font-weight:600;">SAÚDE</div>
                <div style="background:#21262d; border-radius:999px;
                            width:110px; height:7px; overflow:hidden;">
                    <div style="height:100%; width:{score}%;
                                background:{health_color}; border-radius:999px;"></div>
                </div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:14px;
                            font-weight:700; color:{health_color};">{score}%</div>
                <span style="background:{health_color}22; color:{health_color};
                             padding:2px 8px; border-radius:4px;
                             font-size:11px; font-weight:700;">{health_label}</span>
            </div>
            <div style="font-size:11px; color:#484f58; margin-top:6px;">
                Última leitura: {last_ts}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Current telemetry ─────────────────────────────────────────────────────────
section_header("Telemetria Atual", f"Valores da última leitura — {last_ts}")

STATUS_ICONS = {"ok": "✅", "warning": "⚠️", "critical": "🚨"}

sensor_boxes = [
    ("Temperatura",  f"{latest.temperature_c:.1f}", "°C",  latest.temperature_status),
    ("Vibração",     f"{latest.vibration_g:.2f}",   "g",   latest.vibration_status),
    ("Corrente",     f"{latest.current_a:.1f}",     "A",   latest.current_status),
    ("Tensão",       f"{latest.voltage_v:.1f}",     "V",   latest.voltage_status),
    ("Velocidade",   f"{int(latest.rpm)}",           "RPM", latest.rpm_status),
    ("Potência",     f"{latest.power_kw:.2f}",      "kW",  "ok"),
]

cols = st.columns(6)
for col, (label, value, unit, status) in zip(cols, sensor_boxes):
    color = sensor_status_color(status)
    icon  = STATUS_ICONS.get(status, "")
    with col:
        st.markdown(f"""
        <div style="background:#1c2128; border:1px solid {color}; border-radius:8px;
                    padding:14px 12px; text-align:center;">
            <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.1em;
                        color:#484f58; font-weight:600; margin-bottom:4px;">{label}</div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:22px;
                        font-weight:700; color:{color}; line-height:1.1;">{value}</div>
            <div style="font-size:11px; color:#8b949e; margin-top:2px;">{unit}</div>
            <div style="font-size:15px; margin-top:5px;">{icon}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Time-range filter ─────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)

col_hdr, col_range = st.columns([3, 2])
with col_hdr:
    section_header("Série Temporal", f"{len(converted)} leituras no histórico")
with col_range:
    RANGES = {
        "6 h":    timedelta(hours=6),
        "12 h":   timedelta(hours=12),
        "24 h":   timedelta(hours=24),
        "7 dias": timedelta(days=7),
        "Todos":  None,
    }
    sel_range = st.radio(
        "Período", list(RANGES.keys()),
        horizontal=True, index=3, label_visibility="collapsed",
    )

delta = RANGES[sel_range]
try:
    ref_ts = datetime.fromisoformat(latest.timestamp)
    cutoff = (ref_ts - delta) if delta else None
    history = (
        [c for c in converted if datetime.fromisoformat(c.timestamp) >= cutoff]
        if cutoff else converted
    )
except Exception:
    history = converted

if len(history) < 2:
    history = converted[-48:]

# ── Build DataFrame ───────────────────────────────────────────────────────────
rows = []
for c in history:
    try:
        ts = datetime.fromisoformat(c.timestamp)
    except Exception:
        ts = c.timestamp
    rows.append({
        "ts":   ts,
        "temp": c.temperature_c,
        "vibr": c.vibration_g,
        "curr": c.current_a,
        "volt": c.voltage_v,
        "rpm":  c.rpm,
        "pwr":  c.power_kw,
    })
df = pd.DataFrame(rows)

# ── Plotly dark-theme helpers ─────────────────────────────────────────────────
_BG    = "#0d1117"
_PLOT  = "#1c2128"
_GRID  = "#21262d"
_FONT  = "#8b949e"
_TITLE = "#c9d1d9"


def _layout(title: str, y_label: str) -> dict:
    return dict(
        title=dict(text=title,
                   font=dict(color=_TITLE, size=13,
                             family="Barlow Condensed, sans-serif")),
        paper_bgcolor=_BG,
        plot_bgcolor=_PLOT,
        font=dict(color=_FONT, family="Barlow, sans-serif", size=11),
        xaxis=dict(gridcolor=_GRID, linecolor="#30363d",
                   tickfont=dict(size=10)),
        yaxis=dict(gridcolor=_GRID, linecolor="#30363d",
                   title=dict(text=y_label, font=dict(size=11))),
        margin=dict(l=55, r=10, t=40, b=35),
        showlegend=False,
        height=230,
    )


def _hline(fig, y: float, color: str, dash: str = "dash", label: str = ""):
    fig.add_hline(
        y=y, line_dash=dash, line_color=color, line_width=1,
        annotation_text=label,
        annotation_font_color=color, annotation_font_size=9,
        annotation_position="top right",
    )


# ── Chart 1 — Temperature ─────────────────────────────────────────────────────
c_series = [
    "#22c55e" if t < 75 else ("#f59e0b" if t < 100 else "#ef4444")
    for t in df["temp"]
]
fig_temp = go.Figure()
fig_temp.add_trace(go.Scatter(
    x=df["ts"], y=df["temp"], mode="lines+markers",
    line=dict(color="#f97316", width=2),
    marker=dict(size=4, color=c_series),
))
_hline(fig_temp, 75,  "#f59e0b", label="⚠️ 75°C")
_hline(fig_temp, 100, "#ef4444", label="🚨 100°C")
fig_temp.update_layout(**_layout("Temperatura", "°C"))

# ── Chart 2 — Vibration ───────────────────────────────────────────────────────
fig_vibr = go.Figure()
fig_vibr.add_trace(go.Scatter(
    x=df["ts"], y=df["vibr"], mode="lines+markers",
    line=dict(color="#f59e0b", width=2),
    marker=dict(size=4, color="#f59e0b"),
))
_hline(fig_vibr, 4.0, "#f59e0b", label="⚠️ 4 g")
_hline(fig_vibr, 8.0, "#ef4444", label="🚨 8 g")
fig_vibr.update_layout(**_layout("Vibração", "g"))

# ── Chart 3 — Current ────────────────────────────────────────────────────────
fig_curr = go.Figure()
fig_curr.add_trace(go.Scatter(
    x=df["ts"], y=df["curr"], mode="lines+markers",
    line=dict(color="#22c55e", width=2),
    marker=dict(size=4, color="#22c55e"),
))
_hline(fig_curr, eq.current_a * 1.10, "#f59e0b", label="⚠️ +10%")
_hline(fig_curr, eq.current_a * 1.20, "#ef4444", label="🚨 +20%")
_hline(fig_curr, eq.current_a * 0.80, "#f59e0b", dash="dot")
fig_curr.update_layout(**_layout("Corrente", "A"))

# ── Chart 4 — Voltage ────────────────────────────────────────────────────────
fig_volt = go.Figure()
fig_volt.add_trace(go.Scatter(
    x=df["ts"], y=df["volt"], mode="lines+markers",
    line=dict(color="#38bdf8", width=2),
    marker=dict(size=4, color="#38bdf8"),
))
_hline(fig_volt, eq.voltage_v * 1.10, "#f59e0b", label="⚠️ +10%")
_hline(fig_volt, eq.voltage_v * 1.20, "#ef4444", label="🚨 +20%")
_hline(fig_volt, eq.voltage_v * 0.90, "#f59e0b", dash="dot", label="⚠️ -10%")
_hline(fig_volt, eq.voltage_v * 0.80, "#ef4444", dash="dot", label="🚨 -20%")
fig_volt.update_layout(**_layout("Tensão", "V"))

# ── Chart 5 — RPM ────────────────────────────────────────────────────────────
fig_rpm = go.Figure()
fig_rpm.add_trace(go.Scatter(
    x=df["ts"], y=df["rpm"], mode="lines",
    line=dict(color="#a78bfa", width=2),
))
_hline(fig_rpm, eq.rpm * 1.10, "#f59e0b", label="⚠️ +10%")
_hline(fig_rpm, eq.rpm * 0.90, "#f59e0b", dash="dot", label="⚠️ -10%")
fig_rpm.update_layout(**_layout("Velocidade", "RPM"))

# ── Chart 6 — Power ──────────────────────────────────────────────────────────
fig_pwr = go.Figure()
fig_pwr.add_trace(go.Scatter(
    x=df["ts"], y=df["pwr"], mode="lines",
    line=dict(color="#d946ef", width=2),
    fill="tozeroy", fillcolor="rgba(217,70,239,0.05)",
))
fig_pwr.update_layout(**_layout("Potência Estimada", "kW"))

# ── Render 3 × 2 grid ────────────────────────────────────────────────────────
cfg = {"displayModeBar": False}

row1 = st.columns(3)
with row1[0]: st.plotly_chart(fig_temp, width="stretch", config=cfg)
with row1[1]: st.plotly_chart(fig_vibr, width="stretch", config=cfg)
with row1[2]: st.plotly_chart(fig_curr, width="stretch", config=cfg)

row2 = st.columns(3)
with row2[0]: st.plotly_chart(fig_volt, width="stretch", config=cfg)
with row2[1]: st.plotly_chart(fig_rpm,  width="stretch", config=cfg)
with row2[2]: st.plotly_chart(fig_pwr,  width="stretch", config=cfg)

# ── Motor nameplate ───────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
section_header("Placa do Motor", "Dados da placa de identificação — extração via visão computacional (simulada)")

notes_block = ""
if eq.notes:
    notes_block = (
        "<div style='margin-top:14px; padding-top:12px; border-top:1px solid #21262d;'>"
        "<div style='font-size:9px; letter-spacing:0.1em; color:#484f58; "
        "text-transform:uppercase; margin-bottom:4px;'>Observações</div>"
        f"<div style='font-size:13px; color:#8b949e;'>{eq.notes}</div>"
        "</div>"
    )

st.markdown(f"""
<div style="background:#0d1117; border:2px solid #30363d;
            border-top:2px solid #f97316; border-radius:8px;
            padding:24px 28px; max-width:740px;
            font-family:'JetBrains Mono',monospace;">

    <div style="display:flex; justify-content:space-between; align-items:center;
                border-bottom:1px solid #21262d; padding-bottom:14px; margin-bottom:18px;">
        <div>
            <div style="font-size:10px; letter-spacing:0.12em; color:#484f58;
                        text-transform:uppercase; margin-bottom:3px;">Fabricante</div>
            <div style="font-size:20px; font-weight:700; color:#f97316;
                        font-family:'Barlow Condensed',sans-serif;">{eq.manufacturer}</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:10px; letter-spacing:0.12em; color:#484f58;
                        text-transform:uppercase; margin-bottom:3px;">TAG</div>
            <div style="font-size:18px; font-weight:700; color:#f97316;">{eq.tag}</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:10px; letter-spacing:0.12em; color:#484f58;
                        text-transform:uppercase; margin-bottom:3px;">Modelo</div>
            <div style="font-size:16px; font-weight:600; color:#e6edf3;">{eq.model}</div>
        </div>
    </div>

    <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:18px;">
        <div>
            <div style="font-size:9px; letter-spacing:0.1em; color:#484f58;
                        text-transform:uppercase;">Potência Nominal</div>
            <div style="font-size:18px; font-weight:700; color:#e6edf3;
                        margin-top:2px;">{eq.power_kw} <span style="font-size:12px;color:#8b949e;">kW</span></div>
        </div>
        <div>
            <div style="font-size:9px; letter-spacing:0.1em; color:#484f58;
                        text-transform:uppercase;">Tensão Nominal</div>
            <div style="font-size:18px; font-weight:700; color:#e6edf3;
                        margin-top:2px;">{eq.voltage_v} <span style="font-size:12px;color:#8b949e;">V</span></div>
        </div>
        <div>
            <div style="font-size:9px; letter-spacing:0.1em; color:#484f58;
                        text-transform:uppercase;">Corrente Nominal</div>
            <div style="font-size:18px; font-weight:700; color:#e6edf3;
                        margin-top:2px;">{eq.current_a} <span style="font-size:12px;color:#8b949e;">A</span></div>
        </div>
        <div>
            <div style="font-size:9px; letter-spacing:0.1em; color:#484f58;
                        text-transform:uppercase;">Velocidade</div>
            <div style="font-size:18px; font-weight:700; color:#e6edf3;
                        margin-top:2px;">{eq.rpm} <span style="font-size:12px;color:#8b949e;">RPM</span></div>
        </div>
        <div>
            <div style="font-size:9px; letter-spacing:0.1em; color:#484f58;
                        text-transform:uppercase;">Frequência</div>
            <div style="font-size:18px; font-weight:700; color:#e6edf3;
                        margin-top:2px;">{eq.frequency_hz} <span style="font-size:12px;color:#8b949e;">Hz</span></div>
        </div>
        <div>
            <div style="font-size:9px; letter-spacing:0.1em; color:#484f58;
                        text-transform:uppercase;">Carcaça</div>
            <div style="font-size:18px; font-weight:700; color:#e6edf3;
                        margin-top:2px;">{eq.frame}</div>
        </div>
    </div>

    <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:18px;
                margin-top:14px; border-top:1px solid #21262d; padding-top:14px;">
        <div>
            <div style="font-size:9px; letter-spacing:0.1em; color:#484f58;
                        text-transform:uppercase;">Proteção</div>
            <div style="font-size:15px; font-weight:600; color:#e6edf3;
                        margin-top:2px;">{eq.protection_class}</div>
        </div>
        <div>
            <div style="font-size:9px; letter-spacing:0.1em; color:#484f58;
                        text-transform:uppercase;">Isolamento</div>
            <div style="font-size:15px; font-weight:600; color:#e6edf3;
                        margin-top:2px;">Classe {eq.insulation_class}</div>
        </div>
        <div>
            <div style="font-size:9px; letter-spacing:0.1em; color:#484f58;
                        text-transform:uppercase;">Responsável Técnico</div>
            <div style="font-size:15px; font-weight:600; color:#e6edf3;
                        margin-top:2px;">{eq.responsible_technician}</div>
        </div>
    </div>

    {notes_block}

    <div style="margin-top:14px; padding-top:12px; border-top:1px dashed #30363d;
                display:flex; justify-content:space-between; align-items:center;
                font-size:10px; color:#484f58;">
        <div>📡 Dados extraídos via visão computacional (simulado) — Sprint 2</div>
        <div>ID <span style="color:#484f58;">{eq.id[:8]}…</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

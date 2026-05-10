"""
Page 3 — Dados Brutos
Sensor readings visualization with raw-to-engineering-unit conversion.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

from utils.ui_helpers import inject_css, render_sidebar, section_header, render_sensor_box, SENSOR_STATUS_ICON
from utils.unit_converter import convert_reading
from backend.services import EquipmentService, SensorService
from backend.models import SensorReading

st.set_page_config(
    page_title="MotorSync — Dados Brutos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
render_sidebar()

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:8px;">
    <div style="font-family:'Barlow Condensed',sans-serif; font-size:28px;
                font-weight:700; color:#e6edf3; line-height:1;">📊 Dados dos Sensores</div>
    <div style="font-size:13px; color:#8b949e; margin-top:2px;">
        Leituras brutas convertidas para unidades de engenharia
    </div>
</div>
<hr style="border-color:#30363d; margin:12px 0 24px;">
""", unsafe_allow_html=True)

# ── Equipment selector ────────────────────────────────────────────────────────
equipments = EquipmentService.list_equipment()
if not equipments:
    st.warning("Nenhum equipamento cadastrado. Cadastre um ativo primeiro.", icon="⚠️")
    st.page_link("pages/2_Cadastro.py", label="→ Cadastrar Equipamento")
    st.stop()

# Pre-select if coming from equipment page
pre_id = st.session_state.get("sensor_equipment_id", None)
eq_map = {f"{e.tag} — {e.manufacturer} {e.model}": e for e in equipments}
eq_labels = list(eq_map.keys())

default_idx = 0
if pre_id:
    for i, e in enumerate(equipments):
        if e.id == pre_id:
            default_idx = i
            break

col_sel, col_gen = st.columns([3, 1])
with col_sel:
    selected_label = st.selectbox("Selecionar Equipamento", eq_labels,
                                   index=default_idx, label_visibility="collapsed")
with col_gen:
    gen_btn = st.button("🔄  Gerar Dados Demo", use_container_width=True,
                        help="Gera leituras simuladas para demonstração")

eq = eq_map[selected_label]

# ── Generate demo readings if requested ───────────────────────────────────────
if gen_btn:
    from utils.unit_converter import ADC_RESOLUTION, VOLTAGE_SENSOR_MAX_V, CURRENT_SENSOR_MAX_A
    raw_v_nom = (eq.voltage_v / VOLTAGE_SENSOR_MAX_V) * ADC_RESOLUTION
    raw_a_nom = (eq.current_a / CURRENT_SENSOR_MAX_A) * ADC_RESOLUTION
    raw_rpm_nom = eq.rpm / 60.0
    now = datetime.now()

    for i in range(24):
        ts = (now - timedelta(hours=24 - i)).isoformat()
        noise = lambda x, p=0.05: max(0, x * (1 + random.uniform(-p, p)))
        reading = SensorReading(
            equipment_id=eq.id,
            timestamp=ts,
            raw_voltage=round(noise(raw_v_nom), 1),
            raw_current=round(noise(raw_a_nom, 0.08), 1),
            raw_temperature=round(noise(1800, 0.12), 1),
            raw_vibration=round(noise(410, 0.20), 1),
            raw_rpm=round(noise(raw_rpm_nom, 0.03), 2),
        )
        SensorService.add_reading(reading)
    st.success(f"✅  24 leituras geradas para {eq.tag}", icon="⚡")
    st.rerun()

# ── Load readings ─────────────────────────────────────────────────────────────
raw_readings = SensorService.get_readings(eq.id)

if not raw_readings:
    st.markdown(f"""
    <div style="text-align:center; padding:48px 20px; background:#1c2128;
                border:1px dashed #30363d; border-radius:12px; margin-top:16px;">
        <div style="font-size:40px; margin-bottom:12px;">📡</div>
        <div style="font-size:16px; font-weight:600; color:#8b949e;">
            Nenhuma leitura disponível para <span style="color:#f97316;">{eq.tag}</span>
        </div>
        <div style="font-size:12px; color:#484f58; margin-top:6px;">
            Conecte os sensores ou clique em "Gerar Dados Demo" para simular leituras.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Convert all readings
nominal = {"voltage_v": eq.voltage_v, "current_a": eq.current_a, "rpm": eq.rpm}
converted = [convert_reading(r.to_dict(), nominal) for r in raw_readings]
latest = converted[-1]  # Most recent

# ── Latest reading — Live panel ───────────────────────────────────────────────
section_header("Leitura Mais Recente", f"Última atualização: {latest.timestamp[:19].replace('T', ' ')}")

# Status summary banner
overall_statuses = [latest.voltage_status, latest.current_status,
                    latest.temperature_status, latest.vibration_status, latest.rpm_status]
if "critical" in overall_statuses:
    overall = "critical"
    overall_msg = "🚨  ATENÇÃO CRÍTICA — Um ou mais parâmetros fora do limite seguro"
    banner_color = "#ef4444"
    banner_bg = "#2d0e0e"
elif "warning" in overall_statuses:
    overall = "warning"
    overall_msg = "⚠️  ATENÇÃO — Parâmetros próximos ao limite nominal"
    banner_color = "#f59e0b"
    banner_bg = "#2d1f00"
else:
    overall = "ok"
    overall_msg = "✅  OPERAÇÃO NORMAL — Todos os parâmetros dentro dos limites"
    banner_color = "#22c55e"
    banner_bg = "#052e16"

st.markdown(f"""
<div style="background:{banner_bg}; border:1px solid {banner_color}; border-radius:8px;
            padding:12px 18px; margin-bottom:20px; font-size:14px; font-weight:600;
            color:{banner_color};">
    {overall_msg}
</div>
""", unsafe_allow_html=True)

# Sensor boxes
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    render_sensor_box("Tensão", f"{latest.voltage_v:.1f}", "V", latest.voltage_status)
with c2:
    render_sensor_box("Corrente", f"{latest.current_a:.1f}", "A", latest.current_status)
with c3:
    render_sensor_box("Temperatura", f"{latest.temperature_c:.1f}", "°C", latest.temperature_status)
with c4:
    render_sensor_box("Vibração", f"{latest.vibration_g:.2f}", "g", latest.vibration_status)
with c5:
    render_sensor_box("Velocidade", f"{int(latest.rpm)}", "RPM", latest.rpm_status)
with c6:
    render_sensor_box("Potência", f"{latest.power_kw:.2f}", "kW", "ok")

# ── Historical charts ─────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
section_header("Histórico de Leituras", f"{len(converted)} leituras carregadas")

# Build dataframe
df_data = []
for c in converted:
    try:
        ts = datetime.fromisoformat(c.timestamp)
    except Exception:
        ts = c.timestamp
    df_data.append({
        "Timestamp": ts,
        "Tensão (V)": c.voltage_v,
        "Corrente (A)": c.current_a,
        "Temperatura (°C)": c.temperature_c,
        "Vibração (g)": c.vibration_g,
        "RPM": c.rpm,
        "Potência (kW)": c.power_kw,
    })
df = pd.DataFrame(df_data).set_index("Timestamp")

# Chart tabs
tab1, tab2, tab3, tab4 = st.tabs(["⚡ Elétrico", "🌡️ Temperatura", "🔄 Velocidade", "📋 Tabela Completa"])

with tab1:
    col_v, col_i = st.columns(2)
    with col_v:
        st.markdown("**Tensão (V)**")
        st.markdown(f"""
        <div style="font-size:11px; color:#8b949e; margin:-8px 0 8px;">
            Nominal: <strong>{eq.voltage_v} V</strong> &nbsp;·&nbsp;
            Limite ±10%: {eq.voltage_v * 0.9:.0f} – {eq.voltage_v * 1.1:.0f} V
        </div>
        """, unsafe_allow_html=True)
        st.line_chart(df[["Tensão (V)"]], color=["#f97316"])
    with col_i:
        st.markdown("**Corrente (A)**")
        st.markdown(f"""
        <div style="font-size:11px; color:#8b949e; margin:-8px 0 8px;">
            Nominal: <strong>{eq.current_a} A</strong> &nbsp;·&nbsp;
            Limite: {eq.current_a * 1.1:.1f} A (FLA × 1.1)
        </div>
        """, unsafe_allow_html=True)
        st.line_chart(df[["Corrente (A)"]], color=["#22c55e"])

    st.markdown("**Potência Estimada (kW)**")
    st.line_chart(df[["Potência (kW)"]], color=["#a78bfa"])

with tab2:
    st.markdown("**Temperatura (°C)**")
    st.markdown("""
    <div style="font-size:11px; color:#8b949e; margin:-8px 0 8px;">
        Alarme ⚠️ &gt; 75°C &nbsp;·&nbsp; Crítico 🚨 &gt; 100°C
    </div>
    """, unsafe_allow_html=True)
    st.line_chart(df[["Temperatura (°C)"]], color=["#ef4444"])

with tab3:
    col_rpm, col_vib = st.columns(2)
    with col_rpm:
        st.markdown("**Velocidade (RPM)**")
        st.markdown(f"""
        <div style="font-size:11px; color:#8b949e; margin:-8px 0 8px;">
            Nominal: <strong>{eq.rpm} RPM</strong>
        </div>
        """, unsafe_allow_html=True)
        st.line_chart(df[["RPM"]], color=["#38bdf8"])
    with col_vib:
        st.markdown("**Vibração (g)**")
        st.markdown("""
        <div style="font-size:11px; color:#8b949e; margin:-8px 0 8px;">
            Alerta ⚠️ &gt; 4g &nbsp;·&nbsp; Crítico 🚨 &gt; 8g
        </div>
        """, unsafe_allow_html=True)
        st.line_chart(df[["Vibração (g)"]], color=["#f59e0b"])

with tab4:
    # Full table with raw + converted values
    st.markdown("**Dados Convertidos — Unidades de Engenharia**")
    st.dataframe(df.reset_index(), use_container_width=True, height=320,
                 column_config={
                     "Timestamp": st.column_config.DatetimeColumn("Data/Hora", format="DD/MM/YY HH:mm"),
                     "Tensão (V)": st.column_config.NumberColumn(format="%.1f V"),
                     "Corrente (A)": st.column_config.NumberColumn(format="%.1f A"),
                     "Temperatura (°C)": st.column_config.NumberColumn(format="%.1f °C"),
                     "Vibração (g)": st.column_config.NumberColumn(format="%.3f g"),
                     "RPM": st.column_config.NumberColumn(format="%.0f"),
                     "Potência (kW)": st.column_config.NumberColumn(format="%.3f kW"),
                 })

    # Raw values table
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    with st.expander("🔩  Valores Brutos do ADC (12-bit, 0–4095)", expanded=False):
        st.markdown("""
        <div style="font-size:12px; color:#8b949e; margin-bottom:12px; line-height:1.6;">
            Estes são os valores diretamente lidos dos conversores analógico-digital (ADC) antes de qualquer
            processamento. Cada valor está na escala 0–4095 (resolução de 12 bits).<br>
            A conversão utiliza os fatores de escala de cada sensor para transformá-los nas
            unidades físicas exibidas acima.
        </div>
        """, unsafe_allow_html=True)

        raw_data = []
        for r in raw_readings:
            try:
                ts = datetime.fromisoformat(r.timestamp)
            except Exception:
                ts = r.timestamp
            raw_data.append({
                "Timestamp": ts,
                "ADC Tensão": r.raw_voltage,
                "ADC Corrente": r.raw_current,
                "ADC Temperatura": r.raw_temperature,
                "ADC Vibração": r.raw_vibration,
                "Pulsos/s (RPM)": r.raw_rpm,
            })
        df_raw = pd.DataFrame(raw_data).set_index("Timestamp")
        st.dataframe(df_raw.reset_index(), use_container_width=True, height=280)

        # Conversion table reference
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        st.markdown("**Tabela de Conversão — Fórmulas Aplicadas**")
        st.markdown("""
        | Sensor | Tipo | Escala Raw | Fórmula | Unidade |
        |---|---|---|---|---|
        | Tensão | ZMPT101B | 0 – 4095 | `raw / 4095 × 500` | V (CA) |
        | Corrente | ACS712-30A | 0 – 4095 | `raw / 4095 × 30` | A |
        | Temperatura | NTC Thermistor | 0 – 4095 | `−20 + (raw / 4095) × 170` | °C |
        | Vibração | ADXL345 | 0 – 4095 | `raw / 4095 × 16` | g |
        | Velocidade | Hall Effect | pulsos/s | `pulsos/s × 60 / PPR` | RPM |
        | Potência | Derivada | — | `V × A × FP × √3 / 1000` | kW |
        """)

# ── Footer note ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:24px; padding:12px 16px; background:#161b22; border-radius:6px;
            border:1px solid #21262d; font-size:11px; color:#484f58;">
    💡 <strong style="color:#8b949e;">Sprint 1</strong> — Dados simulados para validação da interface.
    Na Sprint 2, este módulo receberá dados reais via MQTT/API e aplicará modelos preditivos
    para detecção de anomalias.
</div>
""", unsafe_allow_html=True)

"""
MotorSync — Motor Monitoring System
Sprint 3: Operational Intelligence — Alerts & Decision Support Panel

Entry point — this is now the "página inicial" the operator sees before
picking an equipment: active alerts, NLP summaries and recommended actions
come first; equipment KPIs / quick access (incl. the Sprint 2 Dashboard)
stay below for continuity.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from utils.ui_helpers import (
    inject_css, render_sidebar, badge_html, section_header,
    render_alert_card, render_recommendation_card,
)
from backend.services import EquipmentService, AlertService
from backend.models import ALERT_SEVERITY

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MotorSync — Painel de Alertas",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
render_sidebar()

# ── Session state defaults ───────────────────────────────────────────────────
st.session_state.setdefault("auto_refresh", False)
st.session_state.setdefault("refresh_interval", 30)
st.session_state.setdefault("last_scan_at", None)
st.session_state.setdefault("last_scan_count", 0)

equipments = EquipmentService.list_equipment()

# ── Header + refresh controls ────────────────────────────────────────────────
col_title, col_toggle, col_interval, col_btn = st.columns([4, 1.6, 1.4, 1.4])

with col_title:
    st.markdown("""
    <div>
        <div style="font-family:'Barlow Condensed',sans-serif; font-size:28px;
                    font-weight:700; color:#e6edf3; line-height:1;">
            🚨 Painel de Alertas e Estados
        </div>
        <div style="font-size:13px; color:#8b949e; margin-top:2px;">
            Acompanhamento proativo do parque de ativos — antes de abrir qualquer equipamento
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_toggle:
    st.session_state["auto_refresh"] = st.toggle(
        "Atualização automática", value=st.session_state["auto_refresh"]
    )

with col_interval:
    st.session_state["refresh_interval"] = st.selectbox(
        "Intervalo", [15, 30, 60, 120], index=[15, 30, 60, 120].index(st.session_state["refresh_interval"]),
        format_func=lambda s: f"{s}s", label_visibility="collapsed",
        disabled=not st.session_state["auto_refresh"],
    )

with col_btn:
    manual_refresh = st.button("🔄  Atualizar agora", use_container_width=True, type="primary")

# Auto-refresh via meta tag — keeps this dependency-free (no extra package)
if st.session_state["auto_refresh"]:
    st.markdown(
        f'<meta http-equiv="refresh" content="{st.session_state["refresh_interval"]}">',
        unsafe_allow_html=True,
    )

st.markdown("<hr style='border-color:#30363d; margin:12px 0 24px;'>", unsafe_allow_html=True)

# ── Run the scan (button click, timer reload, or first load) ────────────────
should_scan = manual_refresh or st.session_state["auto_refresh"] or st.session_state["last_scan_at"] is None

new_alerts = []
if should_scan and equipments:
    AlertService.ensure_demo_signal(equipments)

    # Guarantee at least one visible alert on demand, since there's no live
    # ML/IoT pipeline feeding this yet — satisfies the "simulate a notification
    # after refresh" requirement while keeping the scan/alert logic itself real.
    if manual_refresh or (st.session_state["auto_refresh"] and st.session_state["last_scan_count"] == 0):
        target = equipments[datetime.now().microsecond % len(equipments)]
        AlertService.inject_simulated_anomaly(target)

    new_alerts = AlertService.scan_all(equipments)
    st.session_state["last_scan_at"] = datetime.now().isoformat()
    st.session_state["last_scan_count"] = len(new_alerts)

if manual_refresh:
    if new_alerts:
        st.toast(f"{len(new_alerts)} novo(s) alerta(s) detectado(s).", icon="🚨")
    else:
        st.toast("Atualizado — nenhum novo alerta.", icon="✅")

# ── Current-state KPIs ────────────────────────────────────────────────────────
states = {eq.id: AlertService.equipment_state(eq.id) for eq in equipments}
n_critical = sum(1 for s in states.values() if s == "critical")
n_warning = sum(1 for s in states.values() if s == "warning")
n_ok = sum(1 for s in states.values() if s == "ok")

kpi_cols = st.columns(4)
kpi_defs = [
    ("Ativos Monitorados", len(equipments), "#30363d", "#e6edf3", "equipamentos com dados analisados"),
    ("Críticos", n_critical, ALERT_SEVERITY["critical"]["color"], ALERT_SEVERITY["critical"]["color"], "requerem ação imediata"),
    ("Atenção", n_warning, ALERT_SEVERITY["warning"]["color"], ALERT_SEVERITY["warning"]["color"], "desvio do baseline"),
    ("Saudáveis", n_ok, ALERT_SEVERITY["ok"]["color"], ALERT_SEVERITY["ok"]["color"], "dentro dos parâmetros nominais"),
]
for col, (label, value, border, color, sub) in zip(kpi_cols, kpi_defs):
    with col:
        st.markdown(f"""
        <div style="background:#1c2128; border:1px solid {border}; border-radius:10px;
                    padding:18px 22px;">
            <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.08em;
                        color:#484f58; font-weight:600;">{label}</div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:36px;
                        font-weight:700; color:{color}; line-height:1.1; margin:6px 0 2px;">{value}</div>
            <div style="font-size:12px; color:#8b949e;">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

last_scan_label = "—"
if st.session_state["last_scan_at"]:
    try:
        last_scan_label = datetime.fromisoformat(st.session_state["last_scan_at"]).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        last_scan_label = st.session_state["last_scan_at"]
st.markdown(f"""
<div style="font-size:11px; color:#484f58; margin:10px 0 0;">
    Última verificação: {last_scan_label}
    {"· atualização automática a cada " + str(st.session_state["refresh_interval"]) + "s" if st.session_state["auto_refresh"] else ""}
</div>
""", unsafe_allow_html=True)

# ── Active alerts + decision support ─────────────────────────────────────────
st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
history = AlertService.get_history(limit=50)
active_alerts = [a for a in history if a.status == "open"][:10]

if not equipments:
    st.info("Nenhum equipamento cadastrado ainda. Cadastre um ativo para começar a receber alertas.", icon="⚡")
elif active_alerts:
    section_header("Alertas Ativos", f"{len(active_alerts)} evento(s) exigindo atenção — resumo gerado por NLP")
    col_alerts, col_actions = st.columns([2.2, 1])

    with col_alerts:
        for alert in active_alerts:
            render_alert_card(alert)

    with col_actions:
        st.markdown("""
        <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.08em;
                    color:#484f58; font-weight:600; margin-bottom:10px;">
            Apoio à Decisão
        </div>
        """, unsafe_allow_html=True)
        for alert in active_alerts[:5]:
            render_recommendation_card(alert)
else:
    st.markdown("""
    <div style="background:#052e16; border:1px solid #22c55e; border-radius:8px;
                padding:16px 20px; color:#22c55e; font-size:14px; font-weight:600;">
        ✅ Nenhum alerta ativo — todos os ativos monitorados estão dentro dos parâmetros nominais.
    </div>
    """, unsafe_allow_html=True)

# ── Event history ─────────────────────────────────────────────────────────────
if history:
    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
    section_header("Histórico de Eventos", "Últimos alertas registrados pelo motor de análise")

    with st.expander(f"📜  Ver histórico completo ({len(history)} evento(s))", expanded=False):
        for alert in history:
            cfg = ALERT_SEVERITY.get(alert.severity, ALERT_SEVERITY["warning"])
            try:
                ts = datetime.fromisoformat(alert.created_at).strftime("%d/%m/%Y %H:%M")
            except Exception:
                ts = alert.created_at
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center;
                        padding:8px 4px; border-bottom:1px solid #21262d; font-size:12.5px;">
                <div>
                    <span class="badge {cfg['badge']}" style="margin-right:8px;">{cfg['icon']} {cfg['label']}</span>
                    <strong style="color:#e6edf3;">{alert.equipment_tag}</strong>
                    <span style="color:#8b949e;"> — {alert.message}</span>
                </div>
                <div style="color:#484f58; white-space:nowrap; margin-left:12px;">{ts}</div>
            </div>
            """, unsafe_allow_html=True)

# ── Quick access (Sprint 1 + 2 continuity) ────────────────────────────────────
st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)
section_header("Acesso Rápido", "Navegue para as demais seções do sistema")

col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    st.markdown("""
    <div style="background:#1c2128; border:1px solid #30363d; border-radius:10px;
                padding:20px; height:130px;">
        <div style="font-size:26px; margin-bottom:8px;">⚙️</div>
        <div style="font-family:'Barlow Condensed',sans-serif; font-size:17px;
                    font-weight:700; color:#e6edf3;">Equipamentos</div>
        <div style="font-size:12px; color:#8b949e; margin-top:4px;">
            Lista e consulta de ativos cadastrados
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_Equipamentos.py", label="→ Ver Equipamentos")

with col_b:
    st.markdown("""
    <div style="background:#1c2128; border:1px solid #f97316; border-radius:10px;
                padding:20px; height:130px;">
        <div style="font-size:26px; margin-bottom:8px;">📈</div>
        <div style="font-family:'Barlow Condensed',sans-serif; font-size:17px;
                    font-weight:700; color:#e6edf3;">Dashboard</div>
        <div style="font-size:12px; color:#8b949e; margin-top:4px;">
            Telemetria em tempo real e histórico
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/4_Dashboard.py", label="→ Abrir Dashboard")

with col_c:
    st.markdown("""
    <div style="background:#1c2128; border:1px solid #30363d; border-radius:10px;
                padding:20px; height:130px;">
        <div style="font-size:26px; margin-bottom:8px;">📝</div>
        <div style="font-family:'Barlow Condensed',sans-serif; font-size:17px;
                    font-weight:700; color:#e6edf3;">Novo Cadastro</div>
        <div style="font-size:12px; color:#8b949e; margin-top:4px;">
            Registrar novo ativo no sistema
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_Cadastro.py", label="→ Cadastrar Equipamento")

with col_d:
    st.markdown("""
    <div style="background:#1c2128; border:1px solid #30363d; border-radius:10px;
                padding:20px; height:130px;">
        <div style="font-size:26px; margin-bottom:8px;">📊</div>
        <div style="font-family:'Barlow Condensed',sans-serif; font-size:17px;
                    font-weight:700; color:#e6edf3;">Dados Brutos</div>
        <div style="font-size:12px; color:#8b949e; margin-top:4px;">
            Leituras convertidas dos sensores
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_Dados_Brutos.py", label="→ Ver Dados Brutos")

# ── Equipment overview list ───────────────────────────────────────────────────
if equipments:
    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
    section_header("Estado dos Ativos", "Estado operacional atual de cada equipamento monitorado")

    for eq in sorted(equipments, key=lambda x: x.updated_at, reverse=True):
        state = states.get(eq.id, "ok")
        state_cfg = ALERT_SEVERITY[state]
        badge = badge_html(eq.status)
        st.markdown(f"""
        <div class="equip-card" style="border-left:4px solid {state_cfg['color']};">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div class="tag">{eq.tag}</div>
                    <div class="name">{eq.manufacturer} {eq.model}</div>
                    <div class="meta">
                        {eq.power_kw} kW &nbsp;·&nbsp; {eq.voltage_v} V &nbsp;·&nbsp;
                        {eq.rpm} RPM &nbsp;·&nbsp; {eq.installation_location}
                    </div>
                </div>
                <div style="text-align:right;">
                    <span class="badge {state_cfg['badge']}">{state_cfg['icon']} {state_cfg['label']}</span>
                    <div style="margin-top:6px;">{badge}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Nenhum equipamento cadastrado. Use o menu **Cadastro** para adicionar o primeiro ativo.", icon="⚡")

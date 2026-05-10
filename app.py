"""
MotorSync — Motor Monitoring System
Sprint 1: Asset Fundamentals & Registration Interface

Entry point — Dashboard / Home screen.
"""

import streamlit as st
import sys
from pathlib import Path

# Ensure project root is on path regardless of working directory
sys.path.insert(0, str(Path(__file__).parent))

from utils.ui_helpers import inject_css, render_sidebar, badge_html, section_header
from backend.services import EquipmentService
from backend.models import EQUIPMENT_STATUS

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MotorSync — Painel Principal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
render_sidebar()

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
    <div>
        <div style="font-family:'Barlow Condensed',sans-serif; font-size:28px;
                    font-weight:700; color:#e6edf3; line-height:1;">
            Painel Principal
        </div>
        <div style="font-size:13px; color:#8b949e; margin-top:2px;">
            Visão geral dos ativos monitorados
        </div>
    </div>
</div>
<hr style="border-color:#30363d; margin:12px 0 24px;">
""", unsafe_allow_html=True)

# ── Load data ────────────────────────────────────────────────────────────────
equipments = EquipmentService.list_equipment()

# ── KPI Cards ────────────────────────────────────────────────────────────────
total = len(equipments)
active = sum(1 for e in equipments if e.status == "active")
maintenance = sum(1 for e in equipments if e.status == "maintenance")
decommissioned = sum(1 for e in equipments if e.status == "decommissioned")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div style="background:#1c2128; border:1px solid #30363d; border-radius:10px;
                padding:18px 22px;">
        <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.08em;
                    color:#484f58; font-weight:600;">Total de Ativos</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:36px;
                    font-weight:700; color:#e6edf3; line-height:1.1; margin:6px 0 2px;">{total}</div>
        <div style="font-size:12px; color:#8b949e;">equipamentos cadastrados</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background:#1c2128; border:1px solid #22c55e; border-radius:10px;
                padding:18px 22px;">
        <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.08em;
                    color:#484f58; font-weight:600;">Ativos Operando</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:36px;
                    font-weight:700; color:#22c55e; line-height:1.1; margin:6px 0 2px;">{active}</div>
        <div style="font-size:12px; color:#8b949e;">em operação normal</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background:#1c2128; border:1px solid #f59e0b; border-radius:10px;
                padding:18px 22px;">
        <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.08em;
                    color:#484f58; font-weight:600;">Em Manutenção</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:36px;
                    font-weight:700; color:#f59e0b; line-height:1.1; margin:6px 0 2px;">{maintenance}</div>
        <div style="font-size:12px; color:#8b949e;">aguardando retorno</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div style="background:#1c2128; border:1px solid #30363d; border-radius:10px;
                padding:18px 22px;">
        <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.08em;
                    color:#484f58; font-weight:600;">Descomissionados</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:36px;
                    font-weight:700; color:#6b7280; line-height:1.1; margin:6px 0 2px;">{decommissioned}</div>
        <div style="font-size:12px; color:#8b949e;">fora de operação</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)

# ── Quick access ─────────────────────────────────────────────────────────────
section_header("Acesso Rápido", "Navegue para as principais seções do sistema")

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown("""
    <div style="background:#1c2128; border:1px solid #30363d; border-radius:10px;
                padding:22px; height:130px;">
        <div style="font-size:28px; margin-bottom:8px;">⚙️</div>
        <div style="font-family:'Barlow Condensed',sans-serif; font-size:18px;
                    font-weight:700; color:#e6edf3;">Equipamentos</div>
        <div style="font-size:12px; color:#8b949e; margin-top:4px;">
            Lista e consulta de ativos cadastrados
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_Equipamentos.py", label="→ Ver Equipamentos")

with col_b:
    st.markdown("""
    <div style="background:#1c2128; border:1px solid #30363d; border-radius:10px;
                padding:22px; height:130px;">
        <div style="font-size:28px; margin-bottom:8px;">📝</div>
        <div style="font-family:'Barlow Condensed',sans-serif; font-size:18px;
                    font-weight:700; color:#e6edf3;">Novo Cadastro</div>
        <div style="font-size:12px; color:#8b949e; margin-top:4px;">
            Registrar novo ativo no sistema
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_Cadastro.py", label="→ Cadastrar Equipamento")

with col_c:
    st.markdown("""
    <div style="background:#1c2128; border:1px solid #30363d; border-radius:10px;
                padding:22px; height:130px;">
        <div style="font-size:28px; margin-bottom:8px;">📊</div>
        <div style="font-family:'Barlow Condensed',sans-serif; font-size:18px;
                    font-weight:700; color:#e6edf3;">Dados de Sensores</div>
        <div style="font-size:12px; color:#8b949e; margin-top:4px;">
            Visualizar leituras convertidas dos ativos
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_Dados_Brutos.py", label="→ Ver Dados Brutos")

# ── Recent equipment list ─────────────────────────────────────────────────────
if equipments:
    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
    section_header("Ativos Recentes", "Últimos equipamentos atualizados")

    for eq in sorted(equipments, key=lambda x: x.updated_at, reverse=True)[:5]:
        from datetime import datetime
        try:
            upd = datetime.fromisoformat(eq.updated_at).strftime("%d/%m/%Y %H:%M")
        except Exception:
            upd = eq.updated_at

        badge = badge_html(eq.status)
        st.markdown(f"""
        <div class="equip-card">
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
                    {badge}
                    <div style="font-size:11px; color:#484f58; margin-top:6px;">
                        Atualizado {upd}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Nenhum equipamento cadastrado. Use o menu **Cadastro** para adicionar o primeiro ativo.", icon="⚡")

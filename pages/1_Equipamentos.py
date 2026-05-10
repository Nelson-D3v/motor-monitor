"""
Page 1 — Equipamentos
List, search and filter registered equipment. Click to open technical sheet.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime

from utils.ui_helpers import inject_css, render_sidebar, badge_html, section_header, STATUS_CONFIG
from backend.services import EquipmentService

st.set_page_config(
    page_title="MotorSync — Equipamentos",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
render_sidebar()

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
    <div>
        <div style="font-family:'Barlow Condensed',sans-serif; font-size:28px;
                    font-weight:700; color:#e6edf3; line-height:1;">Equipamentos</div>
        <div style="font-size:13px; color:#8b949e; margin-top:2px;">
            Consulta e gerenciamento do parque de ativos
        </div>
    </div>
</div>
<hr style="border-color:#30363d; margin:12px 0 24px;">
""", unsafe_allow_html=True)

# ── Load data ────────────────────────────────────────────────────────────────
equipments = EquipmentService.list_equipment()

# ── Filters bar ──────────────────────────────────────────────────────────────
col_search, col_status, col_mfr, col_btn = st.columns([3, 2, 2, 1])

with col_search:
    search = st.text_input("🔍 Buscar", placeholder="TAG, modelo, fabricante, localização…", label_visibility="collapsed")

with col_status:
    status_options = {"Todos os status": None, **{v["label"]: k for k, v in STATUS_CONFIG.items()}}
    selected_status_label = st.selectbox("Status", list(status_options.keys()), label_visibility="collapsed")
    selected_status = status_options[selected_status_label]

with col_mfr:
    manufacturers = sorted(set(e.manufacturer for e in equipments)) if equipments else []
    mfr_options = ["Todos os fabricantes"] + manufacturers
    selected_mfr = st.selectbox("Fabricante", mfr_options, label_visibility="collapsed")

with col_btn:
    if st.button("➕ Novo", use_container_width=True, type="primary"):
        st.switch_page("pages/2_Cadastro.py")

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = equipments
if search:
    q = search.lower()
    filtered = [e for e in filtered if
                q in e.tag.lower() or q in e.model.lower() or
                q in e.manufacturer.lower() or q in e.installation_location.lower() or
                q in (e.notes or "").lower()]

if selected_status:
    filtered = [e for e in filtered if e.status == selected_status]

if selected_mfr != "Todos os fabricantes":
    filtered = [e for e in filtered if e.manufacturer == selected_mfr]

# ── Results count ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="font-size:12px; color:#8b949e; margin-bottom:16px;">
    Exibindo <strong style="color:#e6edf3;">{len(filtered)}</strong> de {len(equipments)} equipamentos
</div>
""", unsafe_allow_html=True)

# ── Table view ────────────────────────────────────────────────────────────────
if filtered:
    # Build dataframe for display
    rows = []
    for eq in filtered:
        try:
            upd = datetime.fromisoformat(eq.updated_at).strftime("%d/%m/%Y")
        except Exception:
            upd = "—"
        status_label = STATUS_CONFIG.get(eq.status, {}).get("label", eq.status)
        rows.append({
            "TAG": eq.tag,
            "Fabricante": eq.manufacturer,
            "Modelo": eq.model,
            "Potência (kW)": eq.power_kw,
            "Tensão (V)": eq.voltage_v,
            "RPM": eq.rpm,
            "Localização": eq.installation_location,
            "Status": status_label,
            "Atualizado": upd,
            "_id": eq.id,
        })

    df = pd.DataFrame(rows)
    display_df = df.drop(columns=["_id"])

    # Style the dataframe — usa .map() (pandas ≥ 2.0); fallback para .applymap() em versões antigas
    def color_status(val):
        colors = {
            "Ativo": "color: #22c55e",
            "Manutenção": "color: #f59e0b",
            "Descomissionado": "color: #6b7280",
        }
        return colors.get(val, "")

    styler = display_df.style
    styled = (
        styler.map(color_status, subset=["Status"])
        if hasattr(styler, "map")
        else styler.applymap(color_status, subset=["Status"])
    )

    st.dataframe(
        styled,
        use_container_width=True,
        height=min(400, 80 + len(filtered) * 35),
        hide_index=True,
    )

    # ── Card detail view ──────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    section_header("Ficha Técnica", "Selecione um equipamento para ver os detalhes completos")

    tag_options = {f"{e.tag} — {e.manufacturer} {e.model}": e.id for e in filtered}
    selected_label = st.selectbox("Equipamento", list(tag_options.keys()),
                                   label_visibility="collapsed")

    if selected_label:
        eq_id = tag_options[selected_label]
        eq = EquipmentService.get(eq_id)

        if eq:
            badge = badge_html(eq.status)
            try:
                created = datetime.fromisoformat(eq.created_at).strftime("%d/%m/%Y %H:%M")
                updated = datetime.fromisoformat(eq.updated_at).strftime("%d/%m/%Y %H:%M")
            except Exception:
                created = updated = "—"

            st.markdown(f"""
            <div style="background:#1c2128; border:1px solid #f97316; border-radius:12px;
                        padding:24px 28px; margin-top:12px;">

                <!-- Header -->
                <div style="display:flex; justify-content:space-between; align-items:flex-start;
                            border-bottom:1px solid #30363d; padding-bottom:16px; margin-bottom:20px;">
                    <div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:13px;
                                    color:#f97316; font-weight:700; letter-spacing:0.05em;">{eq.tag}</div>
                        <div style="font-family:'Barlow Condensed',sans-serif; font-size:24px;
                                    font-weight:700; color:#e6edf3; margin:4px 0;">
                            {eq.manufacturer} {eq.model}</div>
                        <div style="font-size:13px; color:#8b949e;">
                            📍 {eq.installation_location}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        {badge}
                        <div style="font-size:11px; color:#484f58; margin-top:8px;">
                            ID: <code style="color:#484f58;">{eq.id[:8]}…</code>
                        </div>
                    </div>
                </div>

                <!-- Technical specs grid -->
                <div style="display:grid; grid-template-columns: repeat(4,1fr); gap:16px; margin-bottom:20px;">
                    <div>
                        <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.08em;
                                    color:#484f58; font-weight:600;">Potência</div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:20px;
                                    font-weight:700; color:#e6edf3;">{eq.power_kw} <span style="font-size:13px;color:#8b949e;">kW</span></div>
                    </div>
                    <div>
                        <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.08em;
                                    color:#484f58; font-weight:600;">Tensão Nominal</div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:20px;
                                    font-weight:700; color:#e6edf3;">{eq.voltage_v} <span style="font-size:13px;color:#8b949e;">V</span></div>
                    </div>
                    <div>
                        <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.08em;
                                    color:#484f58; font-weight:600;">Corrente Nominal</div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:20px;
                                    font-weight:700; color:#e6edf3;">{eq.current_a} <span style="font-size:13px;color:#8b949e;">A</span></div>
                    </div>
                    <div>
                        <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.08em;
                                    color:#484f58; font-weight:600;">Velocidade</div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:20px;
                                    font-weight:700; color:#e6edf3;">{eq.rpm} <span style="font-size:13px;color:#8b949e;">RPM</span></div>
                    </div>
                </div>

                <!-- Secondary specs -->
                <div style="display:grid; grid-template-columns: repeat(4,1fr); gap:16px;
                            border-top:1px solid #21262d; padding-top:16px; margin-bottom:20px;">
                    <div>
                        <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.08em;
                                    color:#484f58; font-weight:600;">Frequência</div>
                        <div style="font-size:15px; font-weight:600; color:#e6edf3;">{eq.frequency_hz} Hz</div>
                    </div>
                    <div>
                        <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.08em;
                                    color:#484f58; font-weight:600;">Carcaça</div>
                        <div style="font-size:15px; font-weight:600; color:#e6edf3;">{eq.frame}</div>
                    </div>
                    <div>
                        <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.08em;
                                    color:#484f58; font-weight:600;">Proteção / Isolamento</div>
                        <div style="font-size:15px; font-weight:600; color:#e6edf3;">
                            {eq.protection_class} / Classe {eq.insulation_class}</div>
                    </div>
                    <div>
                        <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.08em;
                                    color:#484f58; font-weight:600;">Responsável Técnico</div>
                        <div style="font-size:15px; font-weight:600; color:#e6edf3;">{eq.responsible_technician}</div>
                    </div>
                </div>

                {"<div style='background:#161b22; border-radius:6px; padding:12px 14px; margin-bottom:16px;'>" +
                 "<div style='font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:#484f58;font-weight:600;margin-bottom:4px;'>Observações</div>" +
                 f"<div style='font-size:13px;color:#8b949e;'>{eq.notes}</div></div>"
                 if eq.notes else ""}

                <!-- Footer -->
                <div style="display:flex; gap:24px; font-size:11px; color:#484f58;">
                    <div>Cadastrado: {created}</div>
                    <div>Última atualização: {updated}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            col_edit, col_data, col_del = st.columns([1, 1, 4])

            with col_edit:
                if st.button("✏️  Editar Cadastro", use_container_width=True):
                    st.session_state["edit_equipment_id"] = eq.id
                    st.switch_page("pages/2_Cadastro.py")

            with col_data:
                if st.button("📊  Ver Dados do Sensor", use_container_width=True):
                    st.session_state["sensor_equipment_id"] = eq.id
                    st.switch_page("pages/3_Dados_Brutos.py")

else:
    st.markdown("""
    <div style="text-align:center; padding:60px 20px; color:#484f58;">
        <div style="font-size:48px;">⚙️</div>
        <div style="font-size:18px; font-weight:600; color:#8b949e; margin-top:12px;">
            Nenhum equipamento encontrado
        </div>
        <div style="font-size:13px; margin-top:6px;">
            Tente ajustar os filtros ou cadastre um novo ativo.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("➕ Cadastrar Primeiro Equipamento", type="primary"):
        st.switch_page("pages/2_Cadastro.py")
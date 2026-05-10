"""
Shared UI helpers — sidebar, theme injection, reusable components.
Keeps page files clean and consistent.
"""

import streamlit as st
from pathlib import Path

CSS_PATH = Path(__file__).parent.parent / "assets" / "style.css"

STATUS_CONFIG = {
    "active":        {"label": "Ativo",          "badge": "badge-ok",          "icon": "●"},
    "maintenance":   {"label": "Manutenção",      "badge": "badge-maintenance", "icon": "◐"},
    "decommissioned":{"label": "Descomissionado", "badge": "badge-inactive",    "icon": "○"},
}

SENSOR_STATUS_ICON = {
    "ok":       "✅",
    "warning":  "⚠️",
    "critical": "🚨",
}


def inject_css():
    """Inject the custom CSS theme."""
    if CSS_PATH.exists():
        css = CSS_PATH.read_text()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    # Also hide default Streamlit chrome decorations
    st.markdown("""
    <style>
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    </style>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the persistent navigation sidebar."""
    with st.sidebar:
        st.markdown("""
        <div style="padding: 0 0 20px;">
            <div style="font-family:'Barlow Condensed',sans-serif; font-size:22px;
                        font-weight:700; color:#f97316; letter-spacing:0.06em;">
                ⚡ MOTORSYNC
            </div>
            <div style="font-size:10px; color:#484f58; text-transform:uppercase;
                        letter-spacing:0.12em; margin-top:2px;">
                Monitor de Ativos Industriais
            </div>
        </div>
        <hr style="border-color:#30363d; margin: 0 0 16px;">
        """, unsafe_allow_html=True)

        st.markdown("**NAVEGAÇÃO**", help="Sprint 1 — Fundamentos do Ativo")
        st.page_link("app.py",                label="🏠  Painel Principal")
        st.page_link("pages/1_Equipamentos.py", label="⚙️  Equipamentos")
        st.page_link("pages/2_Cadastro.py",     label="📝  Cadastro / Edição")
        st.page_link("pages/3_Dados_Brutos.py", label="📊  Dados Brutos")

        st.markdown("<hr style='border-color:#30363d; margin:16px 0;'>", unsafe_allow_html=True)
        st.markdown("**PRÓXIMAS SPRINTS**")
        st.markdown("""
        <div style="color:#484f58; font-size:12px; line-height:1.8;">
            🔒 &nbsp;Análise Preditiva<br>
            🔒 &nbsp;Alertas & Notificações<br>
            🔒 &nbsp;Relatórios<br>
            🔒 &nbsp;Inteligência Artificial
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#30363d; margin:16px 0;'>", unsafe_allow_html=True)
        st.caption("v1.0.0 — Sprint 1")


def badge_html(status: str) -> str:
    """Return HTML badge for equipment status."""
    cfg = STATUS_CONFIG.get(status, STATUS_CONFIG["active"])
    return f'<span class="badge {cfg["badge"]}">{cfg["icon"]} {cfg["label"]}</span>'


def sensor_status_color(status: str) -> str:
    colors = {"ok": "#22c55e", "warning": "#f59e0b", "critical": "#ef4444"}
    return colors.get(status, "#8b949e")


def section_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div class="section-header">
        <h2>{title}</h2>
        {"<p>" + subtitle + "</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def render_sensor_box(label: str, value: str, unit: str, status: str = "ok"):
    color = sensor_status_color(status)
    st.markdown(f"""
    <div class="sensor-box {status}" style="border-color:{color};">
        <div class="label">{label}</div>
        <div class="value" style="color:{color};">{value}</div>
        <div class="unit">{unit}</div>
    </div>
    """, unsafe_allow_html=True)

"""
Page 2 — Cadastro / Edição
Technical registration form for industrial equipment.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from utils.ui_helpers import inject_css, render_sidebar, section_header
from backend.services import EquipmentService
from backend.models import INSULATION_CLASSES, PROTECTION_CLASSES, MANUFACTURERS

st.set_page_config(
    page_title="MotorSync — Cadastro",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
render_sidebar()

# ── Determine mode: new or edit ───────────────────────────────────────────────
edit_id = st.session_state.get("edit_equipment_id", None)
is_edit = edit_id is not None
existing = EquipmentService.get(edit_id) if is_edit else None

mode_title = f"Editar — {existing.tag}" if (is_edit and existing) else "Novo Cadastro"
mode_subtitle = "Atualize os dados técnicos do equipamento" if is_edit else "Preencha os dados técnicos do equipamento"

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:8px;">
    <div style="font-family:'Barlow Condensed',sans-serif; font-size:28px;
                font-weight:700; color:#e6edf3; line-height:1;">📝 {mode_title}</div>
    <div style="font-size:13px; color:#8b949e; margin-top:2px;">{mode_subtitle}</div>
</div>
<hr style="border-color:#30363d; margin:12px 0 24px;">
""", unsafe_allow_html=True)

# ── Helper: prefill value ─────────────────────────────────────────────────────
def pf(field, default=""):
    """Get existing value for a field when editing."""
    if existing:
        return getattr(existing, field, default)
    return default


def pf_idx(options: list, field: str, default_idx: int = 0):
    """Get index of existing value in options list."""
    if existing:
        val = getattr(existing, field, None)
        try:
            return options.index(val)
        except ValueError:
            pass
    return default_idx


# ── Form ──────────────────────────────────────────────────────────────────────
with st.form("equipment_form", clear_on_submit=False):

    # Section 1 — Identification
    section_header("Identificação do Ativo", "Informações de identificação e localização")

    col1, col2 = st.columns([1, 2])
    with col1:
        tag = st.text_input(
            "TAG de Identificação *",
            value=pf("tag"),
            placeholder="ex: MOT-001",
            help="Identificador único do equipamento no plant. Use formato TIPO-NÚMERO.",
        )
    with col2:
        installation_location = st.text_input(
            "Localização de Instalação *",
            value=pf("installation_location"),
            placeholder="ex: Sala de Bombas — Bloco A, Linha de Produção 2",
        )

    col3, col4 = st.columns(2)
    with col3:
        responsible_technician = st.text_input(
            "Responsável Técnico *",
            value=pf("responsible_technician"),
            placeholder="Nome do técnico ou engenheiro responsável",
        )
    with col4:
        status_options = {
            "Ativo": "active",
            "Em Manutenção": "maintenance",
            "Descomissionado": "decommissioned",
        }
        status_labels = list(status_options.keys())
        status_values = list(status_options.values())
        current_status = pf("status", "active")
        try:
            status_idx = status_values.index(current_status)
        except ValueError:
            status_idx = 0
        selected_status_label = st.selectbox("Status Operacional", status_labels, index=status_idx)
        status = status_options[selected_status_label]

    st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)

    # Section 2 — Equipment data
    section_header("Dados do Equipamento", "Placa de identificação e especificações de fábrica")

    col5, col6 = st.columns(2)
    with col5:
        mfr_list = MANUFACTURERS
        manufacturer = st.selectbox(
            "Fabricante *",
            mfr_list,
            index=pf_idx(mfr_list, "manufacturer"),
        )
    with col6:
        model = st.text_input(
            "Modelo *",
            value=pf("model"),
            placeholder="ex: W22 IR3 Premium, M3BP 315 SMC",
        )

    st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)

    # Section 3 — Electrical parameters
    section_header("Parâmetros Elétricos", "Dados de placa — tensão, corrente e frequência nominais")

    col7, col8, col9 = st.columns(3)
    with col7:
        power_kw = st.number_input(
            "Potência Nominal (kW) *",
            min_value=0.1, max_value=10000.0, step=0.5,
            value=float(pf("power_kw", 75.0)),
            format="%.2f",
        )
    with col8:
        voltage_v = st.number_input(
            "Tensão Nominal (V) *",
            min_value=24.0, max_value=13800.0, step=10.0,
            value=float(pf("voltage_v", 380.0)),
            format="%.1f",
        )
    with col9:
        current_a = st.number_input(
            "Corrente Nominal (A) *",
            min_value=0.1, max_value=5000.0, step=0.5,
            value=float(pf("current_a", 144.0)),
            format="%.1f",
        )

    col10, col11 = st.columns(2)
    with col10:
        frequency_hz = st.selectbox(
            "Frequência (Hz) *",
            [50.0, 60.0],
            index=0 if pf("frequency_hz", 60.0) == 50.0 else 1,
        )
    with col11:
        rpm = st.number_input(
            "Velocidade Nominal (RPM) *",
            min_value=100, max_value=50000, step=10,
            value=int(pf("rpm", 1780)),
        )

    st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)

    # Section 4 — Mechanical / protection
    section_header("Grau de Proteção e Isolamento", "Conformidade com normas ABNT / IEC")

    col12, col13, col14 = st.columns(3)
    with col12:
        frame = st.text_input(
            "Carcaça (Frame) *",
            value=pf("frame", "IEC 160M"),
            placeholder="ex: IEC 160M, 180L, 250M",
        )
    with col13:
        protection_class = st.selectbox(
            "Classe de Proteção (IP) *",
            PROTECTION_CLASSES,
            index=pf_idx(PROTECTION_CLASSES, "protection_class", 3),  # IP55 default
        )
    with col14:
        insulation_class = st.selectbox(
            "Classe de Isolamento *",
            INSULATION_CLASSES,
            index=pf_idx(INSULATION_CLASSES, "insulation_class", 2),  # F default
        )

    st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)

    # Section 5 — Notes
    section_header("Observações", "Informações adicionais, histórico ou particularidades")
    notes = st.text_area(
        "Notas Técnicas",
        value=pf("notes", ""),
        placeholder="Descreva particularidades, histórico de manutenção, ou informações relevantes…",
        height=100,
        label_visibility="collapsed",
    )

    st.markdown("<div style='margin:16px 0'></div>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#30363d;'>", unsafe_allow_html=True)

    # Action buttons
    col_save, col_cancel, col_space = st.columns([1, 1, 4])
    with col_save:
        submitted = st.form_submit_button(
            "💾  Salvar Cadastro" if not is_edit else "💾  Atualizar",
            type="primary",
            use_container_width=True,
        )
    with col_cancel:
        cancelled = st.form_submit_button("✕  Cancelar", use_container_width=True)

# ── Form submission handling ───────────────────────────────────────────────────
if submitted:
    # Validate required fields
    required = {
        "TAG": tag,
        "Fabricante": manufacturer,
        "Modelo": model,
        "Localização": installation_location,
        "Responsável Técnico": responsible_technician,
        "Carcaça": frame,
    }
    missing = [k for k, v in required.items() if not str(v).strip()]

    if missing:
        st.error(f"⚠️  Preencha os campos obrigatórios: **{', '.join(missing)}**")
    else:
        form_data = {
            "tag": tag.strip().upper(),
            "model": model.strip(),
            "manufacturer": manufacturer,
            "power_kw": power_kw,
            "voltage_v": voltage_v,
            "current_a": current_a,
            "frequency_hz": frequency_hz,
            "rpm": rpm,
            "frame": frame.strip(),
            "protection_class": protection_class,
            "insulation_class": insulation_class,
            "installation_location": installation_location.strip(),
            "responsible_technician": responsible_technician.strip(),
            "notes": notes.strip(),
            "status": status,
        }

        if is_edit and existing:
            success, message, _ = EquipmentService.update(edit_id, form_data)
        else:
            success, message, _ = EquipmentService.create(form_data)

        if success:
            st.success(f"✅  {message}")
            if is_edit:
                del st.session_state["edit_equipment_id"]
            st.balloons()
            st.markdown("**Redirecionando para a lista de equipamentos…**")
            st.page_link("pages/1_Equipamentos.py", label="→ Ir para Equipamentos agora")
        else:
            st.error(f"❌  {message}")

if cancelled:
    if "edit_equipment_id" in st.session_state:
        del st.session_state["edit_equipment_id"]
    st.switch_page("pages/1_Equipamentos.py")

# ── Help section ──────────────────────────────────────────────────────────────
with st.expander("ℹ️  Guia de Preenchimento", expanded=False):
    st.markdown("""
    | Campo | Descrição | Exemplo |
    |---|---|---|
    | **TAG** | Identificador único na planta. Convenção: TIPO-NÚMERO | `MOT-001`, `COMP-003`, `BON-012` |
    | **Potência** | Potência nominal do eixo em quilowatts | `75.0 kW` |
    | **Tensão** | Tensão de alimentação nominal (fase-fase) | `380 V`, `440 V`, `13800 V` |
    | **Corrente** | Corrente de plena carga em ampères | `144 A` |
    | **Carcaça** | Norma dimensional (IEC/NEMA) | `IEC 160M`, `NEMA 286T` |
    | **IP** | Índice de proteção contra sólidos e líquidos | `IP55` (poeira + jato d'água) |
    | **Isolamento** | Classe de isolamento (define limite de temperatura) | Classe `F` = 155°C |
    """)

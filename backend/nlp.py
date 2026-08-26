"""
NLP layer — textual summarization of alerts and operational states.

This module is a STUB: it produces template-based Portuguese text so the
front-end and data contract (Alert.summary / Alert.recommendation) are fully
wired end-to-end. Swap `generate_alert_summary` / `generate_recommendation`
for calls into the real NLP/ML service later — the return type (str) and
the `context` dict shape are the contract the rest of the app depends on.
"""

from typing import Optional

PARAMETER_UNIT = {
    "Tensão": "V",
    "Corrente": "A",
    "Temperatura": "°C",
    "Vibração": "g",
    "Velocidade": "RPM",
}

_CAUSE_HINTS = {
    "Tensão": "possível instabilidade na rede de alimentação ou conexão frouxa",
    "Corrente": "sobrecarga mecânica no eixo ou desequilíbrio de fases",
    "Temperatura": "ventilação obstruída, sobrecarga contínua ou falha de rolamento",
    "Vibração": "desalinhamento, desbalanceamento ou desgaste de rolamento",
    "Velocidade": "variação de carga ou escorregamento do rotor",
}


def generate_alert_summary(context: dict) -> str:
    """
    Build a short narrative summary for an alert.

    context keys: equipment_tag, parameter, severity, value, unit, nominal
    """
    tag = context["equipment_tag"]
    param = context["parameter"]
    severity = context["severity"]
    value = context["value"]
    unit = context.get("unit", "")
    nominal = context.get("nominal", value)

    deviation_pct = abs(value - nominal) / nominal * 100 if nominal else 0
    direction = "acima" if value >= nominal else "abaixo"
    severity_txt = "crítico" if severity == "critical" else "de atenção"
    cause = _CAUSE_HINTS.get(param, "causa a ser investigada pela equipe técnica")

    return (
        f"O equipamento {tag} apresentou um desvio {severity_txt} no parâmetro "
        f"{param.lower()}, registrando {value:g}{unit}, {deviation_pct:.0f}% {direction} "
        f"do valor nominal ({nominal:g}{unit}). Padrão consistente com {cause}."
    )


def generate_recommendation(context: dict) -> str:
    """Suggest an initial maintenance action based on severity and parameter."""
    param = context["parameter"]
    severity = context["severity"]

    if severity == "critical":
        base = f"Inspecionar {context['equipment_tag']} imediatamente e avaliar parada controlada."
    else:
        base = f"Programar inspeção de {context['equipment_tag']} na próxima janela de manutenção."

    extra = {
        "Temperatura": "Verificar sistema de ventilação/refrigeração e carga aplicada.",
        "Vibração": "Checar alinhamento, balanceamento e estado dos rolamentos.",
        "Corrente": "Medir corrente por fase e inspecionar carga mecânica acoplada.",
        "Tensão": "Verificar quadro de alimentação e conexões do circuito.",
        "Velocidade": "Avaliar variação de carga e integridade do acoplamento.",
    }.get(param, "Registrar ocorrência e acompanhar tendência nas próximas leituras.")

    return f"{base} {extra}"


def generate_state_description(equipment_tag: str, state: str) -> Optional[str]:
    """Free-text description of an equipment's current operational state."""
    descriptions = {
        "ok": f"{equipment_tag} opera dentro dos parâmetros nominais, sem desvios relevantes.",
        "warning": f"{equipment_tag} apresenta desvios de atenção; recomenda-se monitoramento próximo.",
        "critical": f"{equipment_tag} está em estado crítico; ação corretiva é recomendada com prioridade.",
    }
    return descriptions.get(state)

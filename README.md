# ⚡ MotorSync — Monitor de Ativos Industriais
### Sprint 1: Fundamentos do Ativo e Interface de Cadastro

> Sistema web para cadastro técnico, consulta e visualização de dados de motores e equipamentos industriais.

---

## 🗂️ Estrutura do Projeto

```
motor_monitor/
├── app.py                          # Entrada principal — Painel/Dashboard
├── pages/
│   ├── 1_Equipamentos.py          # Tela de consulta e ficha técnica
│   ├── 2_Cadastro.py              # Formulário de cadastro / edição
│   └── 3_Dados_Brutos.py          # Visualização de dados dos sensores
├── backend/                        # Camada de domínio (desacoplada do UI)
│   ├── __init__.py
│   ├── models.py                   # Dataclasses/modelos de dados
│   ├── storage.py                  # Persistência (JSON → swappable por DB)
│   └── services.py                 # Lógica de negócio / serviços
├── utils/
│   ├── unit_converter.py           # Conversão raw ADC → unidades físicas
│   └── ui_helpers.py               # Componentes e helpers de UI reutilizáveis
├── assets/
│   └── style.css                   # Tema visual industrial (dark mode)
├── data/
│   ├── equipment.json              # Persistência de equipamentos (auto-criado)
│   └── readings.json               # Persistência de leituras (auto-criado)
├── seed_data.py                    # Script de dados demo
└── requirements.txt
```

---

## 🚀 Como Executar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. (Opcional) Carregar dados de demonstração
```bash
python seed_data.py
```

### 3. Iniciar a aplicação
```bash
streamlit run app.py
```

A aplicação abre em `http://localhost:8501`

---

## 🧩 Arquitetura — Decisões de Design

### Desacoplamento Frontend / Backend

O projeto é organizado em camadas independentes:

```
[ Streamlit UI ]  ←→  [ Services ]  ←→  [ Storage ]  ←→  [ JSON / DB ]
                              ↕
                         [ Models ]
                              ↕
                       [ Unit Converter ]
```

- **`backend/models.py`** — Dataclasses puras. Zero dependência de Streamlit.
- **`backend/storage.py`** — Camada de acesso a dados. Trocar JSON por SQLite/Postgres é editar apenas este arquivo.
- **`backend/services.py`** — Lógica de negócio. Validações, regras, orquestrações.
- **`utils/unit_converter.py`** — Funções puras de conversão de unidades. Testável isoladamente.
- **`utils/ui_helpers.py`** — Componentes HTML/CSS reutilizáveis, sidebar, temas.

### Por que esta estrutura facilita os próximos sprints?

| Sprint | O que adicionar | Onde mexer |
|--------|----------------|------------|
| 2 — Modelo ML | Adicionar `ml/predictor.py` | Apenas `services.py` chama o predictor |
| 3 — API real | Substituir `storage.py` por cliente HTTP | Sem tocar em UI |
| 4 — Alertas | Adicionar `backend/alerting.py` | Services + nova página |
| 5 — Migrar para outro framework | Reescrever `pages/` e `utils/ui_helpers.py` | Backend intacto |

---

## 📡 Conversão de Unidades (Sprint 1)

| Sensor | Hardware | Raw (ADC 12-bit) | Fórmula | Saída |
|--------|----------|------------------|---------|-------|
| Tensão | ZMPT101B | 0 – 4095 | `raw / 4095 × 500` | V (CA) |
| Corrente | ACS712-30A | 0 – 4095 | `raw / 4095 × 30` | A |
| Temperatura | NTC Thermistor | 0 – 4095 | `−20 + (raw / 4095) × 170` | °C |
| Vibração | ADXL345 | 0 – 4095 | `raw / 4095 × 16` | g |
| Velocidade | Hall Effect | pulsos/s | `Hz × 60 / PPR` | RPM |
| Potência | Derivada | — | `V × I × FP × √3 / 1000` | kW |

---

## 🎨 UX / Design

- **Tema**: Industrial Dark — fundo `#0d1117`, acento âmbar `#f97316`
- **Cores semânticas**: Verde `#22c55e` (OK) · Âmbar `#f59e0b` (alerta) · Vermelho `#ef4444` (crítico)
- **Tipografia**: Barlow Condensed (display) + Barlow (UI) + JetBrains Mono (dados)
- **Sidebar persistente**: Menu estruturado para evolução incremental em sprints futuros
- **Human-in-the-loop**: Ações destrutivas (delete) são separadas; status de equipamento editável pelo operador; dados brutos sempre preservados e exibidos junto à conversão

---

## 📦 Dependências

```
streamlit >= 1.35.0
pandas >= 2.0.0
```

---

## 🔮 Roadmap

- **Sprint 2**: Ingestão de dados reais (MQTT / REST API) + modelo de detecção de anomalias
- **Sprint 3**: Dashboard de alertas em tempo real + notificações
- **Sprint 4**: Manutenção preditiva — ranking de risco dos ativos
- **Sprint 5**: Relatórios automáticos + exportação PDF

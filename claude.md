Readme bem organizado
Design bem clean e guiado com cores semânticas para ajudar o usuário.
Paine inicial bem legal e útil para não começar a aplicação "do nada"
Código bem organizado com separação de responsabilidades
Bom uso do metrics para formatação dos números com uma linguagem mais humana.
Bom uso do markdown com css e elementos html para auxiliar no design. Deixou o design bem bonito.
Bom uso de filtro trazer os equipamentos de forma mais fácil.
Só tem uma coisa que vale à pena dar uma olhada para o próximo sprint. Na página de equipamentos, eu formatei aqui e consegui visualizar, mas o código local e o publicado, na parte de ficha técnica tem um markdown bem grande com html e divs, mas ele não reconheceu como código html, e daí apareceu na tela todo o código html como uma string gigante, e não o que realmente deveria aparecer, que seriam os divs com blocks e tal.


Visualização Operacional e Dashboards de Ativos

Utilizando Streamlit ou Gradio

1. Contexto do Problema

Após estruturar a base de dados técnica na Sprint 1, o desafio agora é a digitalização visual. É necessário criar uma experiência de navegação onde o usuário consiga identificar o estado do motor (saudável ou crítico) através de elementos visuais e gráficos.

2. Objetivo da Sprint

Desenvolver uma interface de visualização operacional que conecte o cadastro do ativo (TAG) à sua localização e aos seus dados de telemetria em tempo real e históricos.

3. Requisitos Funcionais (Front-end)

Navegação por Planta/Área: Criar uma estrutura de navegação que permita ao usuário selecionar a planta ou área onde o motor está localizado.
Dashboard de Telemetria/Sensor: Exibição dos valores atuais do equipamento (ex: Temperatura, Vibração, Corrente) extraídos dos sensores.
Gráficos Temporais (Séries Temporais): Implementação de gráficos que mostrem a evolução histórica dos dados do motor para análise de tendências.
Alertas e Status: Criação de indicadores visuais (ex: cores verde/amarelo/vermelho) baseados em limites operacionais para indicar o estado de saúde do ativo.
Integração de Cadastro Visual: Exibição da imagem da placa do motor (simulada ou real) associada aos dados que foram extraídos via visão computacional.

4. Requisitos Técnicos

Visualização de Dados: Uso de gráficos básicos das bibliotecas, ou uso de bibliotecas de gráficos (como Plotly, Altair ou Matplotlib) integradas ao Streamlit ou Gradio
Persistência de Dados: Os gráficos devem consumir os dados históricos gerados ou armazenados na Sprint anterior.
UX/UI: A interface deve focar na "rastreabilidade e controle da exibição das informações" para o suporte operacional.

5. Entregáveis esperados

Código-fonte (GitHub): Atualização do repositório com as novas funcionalidades de dashboard.
Protótipo de Visualização: Interface funcional com navegação por TAG e gráficos de desempenho.
Vídeo de Demonstração: Apresentação da solução com foco na jornada do operador ao identificar uma possível falha no motor através dos gráficos.
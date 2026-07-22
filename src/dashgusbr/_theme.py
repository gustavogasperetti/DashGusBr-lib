"""Tema visual da dashgusbr (template Plotly + paleta).

Paleta validada para daltonismo (deutan/protan/tritan) em modo claro:
ordem fixa dos slots categóricos — nunca ciclar nem reordenar, a ordem é o
mecanismo de segurança para visão de cores. Sequencial = um matiz (azul),
claro→escuro. Cinza neutro para categorias "sem lado" (empates).
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

# Slots categóricos, em ordem fixa (identidade de séries)
CORES_CATEGORICAS = [
    "#2a78d6",  # 1 azul
    "#008300",  # 2 verde
    "#e87ba4",  # 3 magenta
    "#eda100",  # 4 amarelo
    "#1baf7a",  # 5 aqua
    "#eb6834",  # 6 laranja
    "#4a3aa7",  # 7 violeta
    "#e34948",  # 8 vermelho
]

AZUL = CORES_CATEGORICAS[0]
VERDE = CORES_CATEGORICAS[1]

# Cinza neutro para marcas sem identidade de série (ex.: empates)
CINZA_NEUTRO = "#898781"

# Rampa sequencial (magnitude): azul claro→escuro
RAMPA_SEQUENCIAL = [
    "#cde2fb",
    "#9ec5f4",
    "#6da7ec",
    "#3987e5",
    "#256abf",
    "#184f95",
    "#0d366b",
]

# Superfície e tinta (chrome do gráfico)
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_MUTED = "#898781"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"

FONTE = 'system-ui, -apple-system, "Segoe UI", sans-serif'

TEMA = "dashgusbr"


def escala_sequencial() -> list:
    """Rampa sequencial no formato de colorscale do Plotly (0..1)."""
    n = len(RAMPA_SEQUENCIAL) - 1
    return [[i / n, cor] for i, cor in enumerate(RAMPA_SEQUENCIAL)]


def registrar_tema() -> None:
    """Registra (idempotente) o template ``dashgusbr`` no Plotly.

    Não altera o template default global do usuário: cada figura da
    biblioteca pede ``template="dashgusbr"`` explicitamente.
    """
    template = go.layout.Template(
        layout=go.Layout(
            paper_bgcolor=SUPERFICIE,
            plot_bgcolor=SUPERFICIE,
            colorway=CORES_CATEGORICAS,
            font=dict(family=FONTE, color=TINTA, size=13),
            title=dict(font=dict(size=16, color=TINTA), x=0, xanchor="left"),
            margin=dict(l=64, r=32, t=64, b=48),
            xaxis=dict(
                gridcolor=GRADE,
                linecolor=EIXO,
                zerolinecolor=EIXO,
                ticks="outside",
                tickcolor=EIXO,
                title=dict(font=dict(color=TINTA_SECUNDARIA)),
                tickfont=dict(color=TINTA_MUTED, size=12),
            ),
            yaxis=dict(
                gridcolor=GRADE,
                linecolor=EIXO,
                zerolinecolor=EIXO,
                ticks="outside",
                tickcolor=EIXO,
                title=dict(font=dict(color=TINTA_SECUNDARIA)),
                tickfont=dict(color=TINTA_MUTED, size=12),
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                font=dict(color=TINTA_SECUNDARIA, size=12),
            ),
            hoverlabel=dict(
                bgcolor="#ffffff",
                bordercolor=GRADE,
                font=dict(family=FONTE, color=TINTA, size=12),
            ),
            hovermode="closest",
        )
    )
    pio.templates[TEMA] = template


registrar_tema()

"""Tema visual da dashgusbr (templates Plotly + paleta).

Paleta validada para daltonismo (deutan/protan/tritan) em modo claro:
ordem fixa dos slots categóricos — nunca ciclar nem reordenar, a ordem é o
mecanismo de segurança para visão de cores. Sequencial = um matiz (azul),
claro→escuro. Cinza neutro para categorias "sem lado" (empates).

Dois templates são registrados: ``dashgusbr`` (claro, padrão) e
``dashgusbr_escuro`` — troque com ``template="dashgusbr_escuro"`` em
qualquer ``plot_*``/``viz.*``.
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
TEMA_ESCURO = "dashgusbr_escuro"

# Chrome do modo escuro (mesma paleta categórica: os matizes seguem seguros
# sobre fundo escuro; só o chrome — superfície, tinta, grade — inverte)
SUPERFICIE_ESCURA = "#16181d"
TINTA_CLARA = "#f2f1ec"
TINTA_CLARA_SECUNDARIA = "#b6b4ac"
TINTA_CLARA_MUTED = "#898781"
GRADE_ESCURA = "#2c2f36"
EIXO_ESCURO = "#43464e"


def escala_sequencial() -> list:
    """Rampa sequencial no formato de colorscale do Plotly (0..1)."""
    n = len(RAMPA_SEQUENCIAL) - 1
    return [[i / n, cor] for i, cor in enumerate(RAMPA_SEQUENCIAL)]


def cor_texto_para(cor_fundo: str) -> str:
    """Cor de texto (escura ou clara) legível sobre a cor de fundo dada.

    Usa a luminância relativa (WCAG) do hex para decidir: fundos escuros
    (ex.: barras pretas do Corinthians) recebem texto claro; fundos claros,
    texto escuro. Aceita ``#rgb`` e ``#rrggbb``.

    Examples
    --------
    >>> cor_texto_para("#1b1b1b")
    '#f2f1ec'
    >>> cor_texto_para("#eda100")
    '#0b0b0b'
    """
    hex_ = cor_fundo.lstrip("#")
    if len(hex_) == 3:
        hex_ = "".join(c * 2 for c in hex_)
    r, g, b = (int(hex_[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def _linear(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    luminancia = 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)
    return TINTA if luminancia > 0.35 else TINTA_CLARA


def _template(
    superficie: str,
    tinta: str,
    tinta_secundaria: str,
    tinta_muted: str,
    grade: str,
    eixo: str,
    hover_bg: str,
) -> go.layout.Template:
    return go.layout.Template(
        layout=go.Layout(
            paper_bgcolor=superficie,
            plot_bgcolor=superficie,
            colorway=CORES_CATEGORICAS,
            font=dict(family=FONTE, color=tinta, size=13),
            title=dict(font=dict(size=16, color=tinta), x=0, xanchor="left"),
            margin=dict(l=64, r=32, t=64, b=48),
            xaxis=dict(
                gridcolor=grade,
                linecolor=eixo,
                zerolinecolor=eixo,
                ticks="outside",
                tickcolor=eixo,
                title=dict(font=dict(color=tinta_secundaria)),
                tickfont=dict(color=tinta_muted, size=12),
            ),
            yaxis=dict(
                gridcolor=grade,
                linecolor=eixo,
                zerolinecolor=eixo,
                ticks="outside",
                tickcolor=eixo,
                title=dict(font=dict(color=tinta_secundaria)),
                tickfont=dict(color=tinta_muted, size=12),
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                font=dict(color=tinta_secundaria, size=12),
            ),
            hoverlabel=dict(
                bgcolor=hover_bg,
                bordercolor=grade,
                font=dict(family=FONTE, color=tinta, size=12),
            ),
            hovermode="closest",
        )
    )


def registrar_tema() -> None:
    """Registra (idempotente) os templates ``dashgusbr`` e ``dashgusbr_escuro``.

    Não altera o template default global do usuário: cada figura da
    biblioteca pede ``template="dashgusbr"`` explicitamente; o modo escuro
    é opt-in via ``template="dashgusbr_escuro"``.
    """
    pio.templates[TEMA] = _template(
        SUPERFICIE, TINTA, TINTA_SECUNDARIA, TINTA_MUTED, GRADE, EIXO, "#ffffff"
    )
    pio.templates[TEMA_ESCURO] = _template(
        SUPERFICIE_ESCURA,
        TINTA_CLARA,
        TINTA_CLARA_SECUNDARIA,
        TINTA_CLARA_MUTED,
        GRADE_ESCURA,
        EIXO_ESCURO,
        "#22252b",
    )


registrar_tema()

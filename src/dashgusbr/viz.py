"""Visualizações Plotly da dashgusbr.

Funções puras: recebem os DataFrames/dicts produzidos por
:mod:`dashgusbr.analytics` e devolvem ``plotly.graph_objects.Figure``.
Todas usam o template ``dashgusbr`` (:mod:`dashgusbr._theme`) sem alterar
o template default global do usuário.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.graph_objects as go

from ._theme import (
    AZUL,
    CINZA_NEUTRO,
    CORES_CATEGORICAS,
    TEMA,
    TINTA_SECUNDARIA,
    VERDE,
    escala_sequencial,
    registrar_tema,
)

registrar_tema()


# ---------------------------------------------------------------------------
# Classificação
# ---------------------------------------------------------------------------


def classificacao(tabela: pd.DataFrame, titulo: Optional[str] = None) -> go.Figure:
    """Barras horizontais de pontos da tabela de classificação.

    Espera a saída de :func:`dashgusbr.analytics.classificacao`. Série única
    (magnitude) → um matiz só, sem legenda; o detalhe (V/E/D, saldo,
    aproveitamento) fica no hover.
    """
    dados = tabela.sort_values("posicao", ascending=False)  # 1º no topo do eixo y
    rotulos = dados["posicao"].astype(str) + "º " + dados["time"]

    fig = go.Figure(
        go.Bar(
            x=dados["pontos"],
            y=rotulos,
            orientation="h",
            marker=dict(color=AZUL),
            text=dados["pontos"],
            textposition="outside",
            textfont=dict(color=TINTA_SECUNDARIA, size=12),
            customdata=dados[
                ["vitorias", "empates", "derrotas", "saldo", "aproveitamento"]
            ],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Pontos: %{x}<br>"
                "V %{customdata[0]} · E %{customdata[1]} · D %{customdata[2]}<br>"
                "Saldo: %{customdata[3]} · Aproveitamento: %{customdata[4]}%"
                "<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        template=TEMA,
        title=titulo or "Classificação",
        xaxis_title="Pontos",
        yaxis=dict(title=None, showgrid=False),
        showlegend=False,
        bargap=0.35,
        height=max(360, 96 + 24 * len(dados)),
    )
    return fig


# ---------------------------------------------------------------------------
# Evolução e histórico
# ---------------------------------------------------------------------------


def evolucao(evolucoes: pd.DataFrame, titulo: Optional[str] = None) -> go.Figure:
    """Linhas de pontos acumulados jogo a jogo (um ou mais times).

    Espera a saída de :func:`dashgusbr.analytics.evolucao_pontos` — ou a
    concatenação de várias, uma por time (coluna ``time`` identifica a série).
    Cores seguem a ordem fixa dos slots categóricos; com uma série só, a
    legenda some (o título nomeia a série).
    """
    times = list(pd.unique(evolucoes["time"]))
    if len(times) > len(CORES_CATEGORICAS):
        raise ValueError(
            f"Máximo de {len(CORES_CATEGORICAS)} times por gráfico; "
            "divida em mais de uma figura."
        )

    fig = go.Figure()
    for i, time in enumerate(times):
        serie = evolucoes[evolucoes["time"] == time]
        fig.add_trace(
            go.Scatter(
                x=serie["jogo"],
                y=serie["pontos_acumulados"],
                mode="lines",
                name=time,
                line=dict(color=CORES_CATEGORICAS[i], width=2),
                customdata=serie[["adversario", "gols_pro", "gols_contra"]],
                hovertemplate=(
                    f"<b>{time}</b> — jogo %{{x}}<br>"
                    "vs %{customdata[0]}: %{customdata[1]} x %{customdata[2]}<br>"
                    "Acumulado: %{y} pts<extra></extra>"
                ),
            )
        )
        # rótulo direto no fim da linha (até 4 séries)
        if len(times) <= 4:
            ultimo = serie.iloc[-1]
            fig.add_annotation(
                x=ultimo["jogo"],
                y=ultimo["pontos_acumulados"],
                text=f" {time}",
                showarrow=False,
                xanchor="left",
                font=dict(color=TINTA_SECUNDARIA, size=12),
            )

    fig.update_layout(
        template=TEMA,
        title=titulo or "Evolução de pontos na temporada",
        xaxis_title="Jogo",
        yaxis_title="Pontos acumulados",
        showlegend=len(times) > 1,
        hovermode="x unified",
    )
    return fig


def historico(
    historico_df: pd.DataFrame,
    metrica: str = "aproveitamento",
    titulo: Optional[str] = None,
) -> go.Figure:
    """Linha do desempenho de um time temporada a temporada.

    Espera a saída de :func:`dashgusbr.analytics.historico_time`. A métrica
    padrão é o aproveitamento (%), comparável entre a era de 2 e a de 3
    pontos por vitória — pontos absolutos e nº de jogos variam de formato
    para formato.
    """
    if metrica not in historico_df.columns:
        raise ValueError(f"Métrica {metrica!r} não existe no histórico.")
    time = historico_df["time"].iloc[0] if "time" in historico_df.columns else ""

    fig = go.Figure(
        go.Scatter(
            x=historico_df["ano_campeonato"],
            y=historico_df[metrica],
            mode="lines+markers",
            line=dict(color=AZUL, width=2),
            marker=dict(size=8, color=AZUL),
            customdata=historico_df[["posicao", "pontos", "jogos"]],
            hovertemplate=(
                "<b>%{x}</b><br>"
                f"{metrica}: %{{y}}<br>"
                "Posição: %{customdata[0]}º · %{customdata[1]} pts em "
                "%{customdata[2]} jogos<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        template=TEMA,
        title=titulo or f"{time} — {metrica} por temporada".strip(),
        xaxis_title="Temporada",
        yaxis_title=metrica.replace("_", " ").capitalize(),
        showlegend=False,
    )
    if metrica == "aproveitamento":
        fig.update_yaxes(range=[0, 100], ticksuffix="%")
    return fig


# ---------------------------------------------------------------------------
# Confronto direto
# ---------------------------------------------------------------------------


def confronto(resumo: dict, titulo: Optional[str] = None) -> go.Figure:
    """Barras do confronto direto: vitórias de cada time e empates.

    Espera o dict de :func:`dashgusbr.analytics.confronto`. Cada time recebe
    um slot categórico fixo; o empate — categoria sem lado — usa o cinza
    neutro, nunca um terceiro matiz.
    """
    time_a, time_b = resumo["time_a"], resumo["time_b"]
    categorias = [f"Vitórias<br>{time_a}", "Empates", f"Vitórias<br>{time_b}"]
    valores = [resumo["vitorias_a"], resumo["empates"], resumo["vitorias_b"]]
    cores = [AZUL, CINZA_NEUTRO, VERDE]

    fig = go.Figure(
        go.Bar(
            x=categorias,
            y=valores,
            marker=dict(color=cores),
            text=valores,
            textposition="outside",
            textfont=dict(color=TINTA_SECUNDARIA, size=13),
            hovertemplate="%{x}: %{y} jogos<extra></extra>",
        )
    )
    fig.update_layout(
        template=TEMA,
        title=titulo
        or f"{time_a} x {time_b} — {resumo['jogos']} jogos no Brasileirão",
        yaxis_title="Jogos",
        xaxis=dict(showgrid=False),
        showlegend=False,
        bargap=0.45,
    )
    fig.add_annotation(
        text=(
            f"Gols: {time_a} {resumo['gols_a']} × "
            f"{resumo['gols_b']} {time_b}"
        ),
        xref="paper",
        yref="paper",
        x=0,
        y=1.08,
        showarrow=False,
        font=dict(color=TINTA_SECUNDARIA, size=12),
        xanchor="left",
    )
    return fig


# ---------------------------------------------------------------------------
# Estatísticas do campeonato
# ---------------------------------------------------------------------------


def gols_por_temporada(
    estatisticas: pd.DataFrame, titulo: Optional[str] = None
) -> go.Figure:
    """Linha da média de gols por jogo em cada temporada.

    Espera a saída de :func:`dashgusbr.analytics.estatisticas_temporada`.
    """
    fig = go.Figure(
        go.Scatter(
            x=estatisticas["ano_campeonato"],
            y=estatisticas["media_gols"],
            mode="lines",
            line=dict(color=AZUL, width=2),
            customdata=estatisticas[["jogos", "gols"]],
            hovertemplate=(
                "<b>%{x}</b><br>Média: %{y} gols/jogo<br>"
                "%{customdata[1]} gols em %{customdata[0]} jogos<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        template=TEMA,
        title=titulo or "Média de gols por jogo, temporada a temporada",
        xaxis_title="Temporada",
        yaxis_title="Gols por jogo",
        yaxis=dict(rangemode="tozero"),
        showlegend=False,
    )
    return fig


def mandante_visitante(
    estatisticas: pd.DataFrame, titulo: Optional[str] = None
) -> go.Figure:
    """Linhas do fator casa: % de vitórias do mandante, empates e do visitante.

    Espera a saída de :func:`dashgusbr.analytics.estatisticas_temporada`.
    Mandante e visitante recebem slots categóricos; o empate usa o cinza
    neutro.
    """
    series = [
        ("Vitória do mandante", "pct_vitorias_mandante", AZUL),
        ("Empate", "pct_empates", CINZA_NEUTRO),
        ("Vitória do visitante", "pct_vitorias_visitante", VERDE),
    ]
    fig = go.Figure()
    for nome, coluna, cor in series:
        fig.add_trace(
            go.Scatter(
                x=estatisticas["ano_campeonato"],
                y=estatisticas[coluna],
                mode="lines",
                name=nome,
                line=dict(color=cor, width=2),
                hovertemplate=f"{nome}: %{{y}}%<extra>%{{x}}</extra>",
            )
        )
    fig.update_layout(
        template=TEMA,
        title=titulo or "Fator casa por temporada",
        xaxis_title="Temporada",
        yaxis_title="% dos jogos",
        yaxis=dict(range=[0, 100], ticksuffix="%"),
        hovermode="x unified",
    )
    return fig


def distribuicao_placares(
    matriz: pd.DataFrame, titulo: Optional[str] = None
) -> go.Figure:
    """Heatmap da frequência de placares (mandante × visitante).

    Espera a saída de :func:`dashgusbr.analytics.distribuicao_placares`.
    Magnitude → rampa sequencial de um matiz, claro→escuro; o último bin
    agrega os placares acima do corte (rotulado ``N+``).
    """
    max_gols = int(matriz.index.max())
    rotulos = [str(g) if g < max_gols else f"{g}+" for g in matriz.index]

    fig = go.Figure(
        go.Heatmap(
            z=matriz.values,
            x=rotulos,
            y=rotulos,
            colorscale=escala_sequencial(),
            xgap=2,
            ygap=2,
            colorbar=dict(title="Jogos", outlinewidth=0),
            hovertemplate=(
                "Mandante %{y} x %{x} Visitante<br>%{z} jogos<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        template=TEMA,
        title=titulo or "Distribuição de placares",
        xaxis=dict(title="Gols do visitante", showgrid=False, side="bottom"),
        yaxis=dict(title="Gols do mandante", showgrid=False, autorange="reversed"),
        height=520,
    )
    return fig

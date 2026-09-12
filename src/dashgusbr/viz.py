"""Visualizações Plotly da dashgusbr.

Funções puras: recebem os DataFrames/dicts produzidos por
:mod:`dashgusbr.analytics` e devolvem ``plotly.graph_objects.Figure``.
Todas usam o template ``dashgusbr`` (:mod:`dashgusbr._theme`) sem alterar
o template default global do usuário.

Personalização
--------------
Toda função aceita:

- ``titulo=``: sobrescreve o título padrão;
- ``cores=``: cor única (str) ou lista de cores, substituindo a paleta padrão;
- ``**layout_kwargs``: repassados a ``fig.update_layout`` por último — servem
  para ``width``/``height``, ``font``, ``template="dashgusbr_escuro"`` etc.

Gráficos com rótulos de valor aceitam ``mostrar_valores=False`` e os com
legenda, ``mostrar_legenda=``; rótulos que caem DENTRO de uma barra recebem
cor de texto automática por luminância (legíveis sobre barras escuras).

Gráficos por time também aceitam ``usar_cores_times=True`` para pintar cada
clube com sua cor oficial (:mod:`dashgusbr._cores_times`). O recurso é
opt-in: cores de clube não são seguras para daltonismo.
"""

from __future__ import annotations

from typing import Optional, Sequence, Union

import pandas as pd
import plotly.graph_objects as go

from ._cores_times import _normalizar, cores_para_times
from ._theme import (
    AZUL,
    CINZA_NEUTRO,
    CORES_CATEGORICAS,
    TEMA,
    TINTA_SECUNDARIA,
    VERDE,
    cor_texto_para,
    escala_sequencial,
    registrar_tema,
)

registrar_tema()

VERMELHO = CORES_CATEGORICAS[7]

Cores = Union[str, Sequence[str], None]


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _como_lista(cores: Cores, n: int, padrao: "list[str]") -> "list[str]":
    """Normaliza o parâmetro ``cores`` para uma lista de ``n`` cores."""
    if cores is None:
        base = list(padrao)
    elif isinstance(cores, str):
        base = [cores]
    else:
        base = list(cores)
    if not base:
        base = list(padrao)
    return [base[i % len(base)] for i in range(n)]


def _resolver_na_serie(times: pd.Series, nome: str) -> str:
    """Casa ``nome`` com um dos times da série, tolerando acento e caixa.

    As funções de ``viz`` não veem a OBT (não podem usar
    ``analytics._resolver_time``), mas o contrato é o mesmo: nome
    desconhecido é erro com as opções, nunca um destaque silenciosamente
    vazio.
    """
    opcoes = list(dict.fromkeys(times))
    alvo = _normalizar(nome)
    for time in opcoes:
        if _normalizar(time) == alvo:
            return time
    raise ValueError(
        f"{nome!r} não está nesta tabela. Opções: {', '.join(sorted(opcoes))}."
    )


def _finalizar(fig: go.Figure, layout_kwargs: dict) -> go.Figure:
    """Aplica os ajustes de layout do usuário por último (eles têm a palavra final)."""
    if layout_kwargs:
        fig.update_layout(**layout_kwargs)
    return fig


# ---------------------------------------------------------------------------
# Classificação
# ---------------------------------------------------------------------------


def classificacao(
    tabela: pd.DataFrame,
    titulo: Optional[str] = None,
    cores: Cores = None,
    mostrar_valores: bool = True,
    destaque: Union[str, Sequence[str], None] = None,
    **layout_kwargs,
) -> go.Figure:
    """Barras horizontais de pontos da tabela de classificação.

    Espera a saída de :func:`dashgusbr.analytics.classificacao`. Série única
    (magnitude) → um matiz só, sem legenda; o detalhe (V/E/D, saldo,
    aproveitamento) fica no hover. ``mostrar_valores=False`` esconde os
    rótulos de pontos.

    ``destaque="Palmeiras"`` pinta só esse time com a cor da série e apaga os
    demais em cinza neutro — é o modo usado pelo painel de classificação do
    dashboard por time. Uma lista (``destaque=["Palmeiras", "Corinthians"]``)
    acende vários, um slot de cor por time, para comparar campanhas na mesma
    tabela. Os nomes são resolvidos com a mesma tolerância a acentos e caixa
    do resto da biblioteca; nome fora da tabela é erro.
    """
    dados = tabela.sort_values("posicao", ascending=False)  # 1º no topo do eixo y
    rotulos = dados["posicao"].astype(str) + "º " + dados["time"]
    (cor,) = _como_lista(cores, 1, [AZUL])
    if destaque is None:  # série única: uma cor só (não uma lista de cores iguais)
        paleta = cor
        tinta_interna = cor_texto_para(cor)
    else:
        pedidos = [destaque] if isinstance(destaque, str) else list(destaque)
        alvos = [_resolver_na_serie(dados["time"], nome) for nome in pedidos]
        do_alvo = dict(zip(alvos, _como_lista(cores, len(alvos), CORES_CATEGORICAS)))
        paleta = [do_alvo.get(time, CINZA_NEUTRO) for time in dados["time"]]
        tinta_interna = [cor_texto_para(c) for c in paleta]

    fig = go.Figure(
        go.Bar(
            x=dados["pontos"],
            y=rotulos,
            orientation="h",
            marker=dict(color=paleta),
            text=dados["pontos"] if mostrar_valores else None,
            textposition="outside",
            textfont=dict(color=TINTA_SECUNDARIA, size=12),
            insidetextfont=dict(color=tinta_interna),
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
    return _finalizar(fig, layout_kwargs)


# ---------------------------------------------------------------------------
# Evolução e histórico
# ---------------------------------------------------------------------------


def evolucao(
    evolucoes: pd.DataFrame,
    titulo: Optional[str] = None,
    cores: Cores = None,
    usar_cores_times: bool = False,
    mostrar_legenda: Optional[bool] = None,
    **layout_kwargs,
) -> go.Figure:
    """Linhas de pontos acumulados jogo a jogo (um ou mais times).

    Espera a saída de :func:`dashgusbr.analytics.evolucao_pontos` — ou a
    concatenação de várias, uma por time (coluna ``time`` identifica a série).
    Cores seguem a ordem fixa dos slots categóricos; com uma série só, a
    legenda some (o título nomeia a série). ``usar_cores_times=True`` pinta
    cada clube com sua cor oficial.
    """
    times = list(pd.unique(evolucoes["time"]))
    if cores is None and not usar_cores_times and len(times) > len(CORES_CATEGORICAS):
        raise ValueError(
            f"Máximo de {len(CORES_CATEGORICAS)} times por gráfico; "
            "divida em mais de uma figura."
        )
    if cores is None and usar_cores_times:
        paleta = cores_para_times(times)
    else:
        paleta = _como_lista(cores, len(times), CORES_CATEGORICAS)

    fig = go.Figure()
    for i, time in enumerate(times):
        serie = evolucoes[evolucoes["time"] == time]
        fig.add_trace(
            go.Scatter(
                x=serie["jogo"],
                y=serie["pontos_acumulados"],
                mode="lines",
                name=time,
                line=dict(color=paleta[i], width=2),
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
        showlegend=mostrar_legenda if mostrar_legenda is not None else len(times) > 1,
        hovermode="x unified",
    )
    return _finalizar(fig, layout_kwargs)


def historico(
    historico_df: pd.DataFrame,
    metrica: str = "aproveitamento",
    titulo: Optional[str] = None,
    cores: Cores = None,
    usar_cores_times: bool = False,
    mostrar_legenda: Optional[bool] = None,
    **layout_kwargs,
) -> go.Figure:
    """Linha do desempenho temporada a temporada — de um ou mais times.

    Espera a saída de :func:`dashgusbr.analytics.historico_time` — ou a
    concatenação de várias, uma por time (a coluna ``time`` identifica a
    série), para comparar carreiras na mesma figura. A métrica padrão é o
    aproveitamento (%), comparável entre a era de 2 e a de 3 pontos por
    vitória — pontos absolutos e nº de jogos variam de formato para formato.
    """
    if metrica not in historico_df.columns:
        raise ValueError(f"Métrica {metrica!r} não existe no histórico.")
    if "time" in historico_df.columns:
        times = list(pd.unique(historico_df["time"]))
    else:
        times = [""]
    padrao = cores_para_times(times) if usar_cores_times and times[0] else CORES_CATEGORICAS
    paleta = _como_lista(cores, len(times), padrao)

    fig = go.Figure()
    for i, time in enumerate(times):
        serie = (
            historico_df[historico_df["time"] == time]
            if "time" in historico_df.columns
            else historico_df
        )
        fig.add_trace(
            go.Scatter(
                x=serie["ano_campeonato"],
                y=serie[metrica],
                mode="lines+markers",
                name=time,
                line=dict(color=paleta[i], width=2),
                marker=dict(size=8, color=paleta[i]),
                customdata=serie[["posicao", "pontos", "jogos"]],
                hovertemplate=(
                    f"<b>{time} — %{{x}}</b><br>" if time else "<b>%{x}</b><br>"
                )
                + (
                    f"{metrica}: %{{y}}<br>"
                    "Posição: %{customdata[0]}º · %{customdata[1]} pts em "
                    "%{customdata[2]} jogos<extra></extra>"
                ),
            )
        )
    um_time = times[0] if len(times) == 1 else ""
    fig.update_layout(
        template=TEMA,
        title=titulo or f"{um_time} — {metrica} por temporada".strip(" —"),
        xaxis_title="Temporada",
        yaxis_title=metrica.replace("_", " ").capitalize(),
        showlegend=(
            mostrar_legenda if mostrar_legenda is not None else len(times) > 1
        ),
    )
    if metrica == "aproveitamento":
        fig.update_yaxes(range=[0, 100], ticksuffix="%")
    return _finalizar(fig, layout_kwargs)


# ---------------------------------------------------------------------------
# Confronto direto
# ---------------------------------------------------------------------------


def confronto(
    resumo: dict,
    titulo: Optional[str] = None,
    cores: Cores = None,
    usar_cores_times: bool = False,
    mostrar_valores: bool = True,
    **layout_kwargs,
) -> go.Figure:
    """Barras do confronto direto: vitórias de cada time e empates.

    Espera o dict de :func:`dashgusbr.analytics.confronto`. Cada time recebe
    um slot categórico fixo; o empate — categoria sem lado — usa o cinza
    neutro, nunca um terceiro matiz. ``usar_cores_times=True`` usa as cores
    oficiais dos dois clubes.
    """
    time_a, time_b = resumo["time_a"], resumo["time_b"]
    categorias = [f"Vitórias<br>{time_a}", "Empates", f"Vitórias<br>{time_b}"]
    valores = [resumo["vitorias_a"], resumo["empates"], resumo["vitorias_b"]]
    if cores is None and usar_cores_times:
        cor_a, cor_b = cores_para_times([time_a, time_b])
        paleta = [cor_a, CINZA_NEUTRO, cor_b]
    else:
        paleta = _como_lista(cores, 3, [AZUL, CINZA_NEUTRO, VERDE])

    fig = go.Figure(
        go.Bar(
            x=categorias,
            y=valores,
            marker=dict(color=paleta),
            text=valores if mostrar_valores else None,
            textposition="outside",
            textfont=dict(color=TINTA_SECUNDARIA, size=13),
            insidetextfont=dict(color=[cor_texto_para(c) for c in paleta]),
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
    return _finalizar(fig, layout_kwargs)


def desempenho_contra(
    tabela: pd.DataFrame,
    top: int = 15,
    titulo: Optional[str] = None,
    cores: Cores = None,
    mostrar_valores: bool = True,
    **layout_kwargs,
) -> go.Figure:
    """Barras horizontais do aproveitamento de um time contra cada adversário.

    Espera a saída de :func:`dashgusbr.analytics.desempenho_contra`. Mostra os
    ``top`` adversários mais enfrentados; o detalhe (jogos, V/E/D, saldo) fica
    no hover.
    """
    dados = tabela.head(top).iloc[::-1]  # mais enfrentado no topo do eixo y
    time = tabela.attrs.get("time", "")
    (cor,) = _como_lista(cores, 1, [AZUL])

    fig = go.Figure(
        go.Bar(
            x=dados["aproveitamento"],
            y=dados["adversario"],
            orientation="h",
            marker=dict(color=cor),
            text=dados["aproveitamento"].map(lambda v: f"{v}%")
            if mostrar_valores
            else None,
            textposition="outside",
            textfont=dict(color=TINTA_SECUNDARIA, size=12),
            insidetextfont=dict(color=cor_texto_para(cor)),
            customdata=dados[["jogos", "vitorias", "empates", "derrotas", "saldo"]],
            hovertemplate=(
                "<b>vs %{y}</b><br>"
                "Aproveitamento: %{x}%<br>"
                "%{customdata[0]} jogos · V %{customdata[1]} · "
                "E %{customdata[2]} · D %{customdata[3]}<br>"
                "Saldo: %{customdata[4]}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        template=TEMA,
        title=titulo or f"{time} — aproveitamento por adversário".strip(" —"),
        xaxis=dict(title="Aproveitamento", range=[0, 100], ticksuffix="%"),
        yaxis=dict(title=None, showgrid=False),
        showlegend=False,
        bargap=0.35,
        height=max(360, 96 + 24 * len(dados)),
    )
    return _finalizar(fig, layout_kwargs)


# ---------------------------------------------------------------------------
# Casa × fora
# ---------------------------------------------------------------------------


def casa_fora(
    resumo: pd.DataFrame,
    titulo: Optional[str] = None,
    cores: Cores = None,
    mostrar_valores: bool = True,
    mostrar_legenda: bool = True,
    **layout_kwargs,
) -> go.Figure:
    """Barras agrupadas de V/E/D como mandante e como visitante.

    Espera a saída de :func:`dashgusbr.analytics.casa_fora`. Vitória e derrota
    recebem slots categóricos; o empate usa o cinza neutro.
    """
    time = resumo.attrs.get("time", "")
    dados = resumo.set_index("local")
    locais = [loc for loc in ("mandante", "visitante") if loc in dados.index]
    rotulos = [loc.capitalize() for loc in locais]
    paleta = _como_lista(cores, 3, [AZUL, CINZA_NEUTRO, VERMELHO])

    series = [("Vitórias", "vitorias"), ("Empates", "empates"), ("Derrotas", "derrotas")]
    fig = go.Figure()
    for (nome, coluna), cor in zip(series, paleta):
        fig.add_trace(
            go.Bar(
                x=rotulos,
                y=[dados.loc[loc, coluna] for loc in locais],
                name=nome,
                marker=dict(color=cor),
                text=[dados.loc[loc, coluna] for loc in locais]
                if mostrar_valores
                else None,
                textposition="outside",
                textfont=dict(color=TINTA_SECUNDARIA, size=12),
                insidetextfont=dict(color=cor_texto_para(cor)),
                hovertemplate=f"{nome}: %{{y}} jogos<extra>%{{x}}</extra>",
            )
        )
    fig.update_layout(
        template=TEMA,
        title=titulo or f"{time} — desempenho em casa × fora".strip(" —"),
        yaxis_title="Jogos",
        xaxis=dict(showgrid=False),
        barmode="group",
        bargap=0.3,
        showlegend=mostrar_legenda,
    )
    for loc, rotulo in zip(locais, rotulos):
        fig.add_annotation(
            x=rotulo,
            y=0,
            yshift=-34,
            yref="y",
            text=f"aproveitamento {dados.loc[loc, 'aproveitamento']}%",
            showarrow=False,
            font=dict(color=TINTA_SECUNDARIA, size=11),
        )
    return _finalizar(fig, layout_kwargs)


# ---------------------------------------------------------------------------
# Forma recente e sequências
# ---------------------------------------------------------------------------


ROTULO_RESULTADO = {"V": "Vitórias", "E": "Empates", "D": "Derrotas"}


def forma(
    jogos: pd.DataFrame,
    titulo: Optional[str] = None,
    cores: Cores = None,
    mostrar_valores: bool = True,
    mostrar_legenda: bool = True,
    **layout_kwargs,
) -> go.Figure:
    """Barras dos pontos jogo a jogo nos últimos jogos do time.

    Espera a saída de :func:`dashgusbr.analytics.forma_recente` (do jogo mais
    antigo ao mais recente). Uma série por resultado — vitória e derrota
    recebem slots categóricos, o empate usa o cinza neutro —, com o placar no
    rótulo e o adversário no eixo (``(C)`` em casa, ``(F)`` fora).
    """
    if jogos.empty:
        raise ValueError("Sem jogos para desenhar a forma recente.")
    time = jogos.attrs.get("time", "")
    aproveitamento = jogos.attrs.get("aproveitamento")
    paleta = dict(zip("VED", _como_lista(cores, 3, [AZUL, CINZA_NEUTRO, VERMELHO])))

    posicoes = list(range(len(jogos)))
    marca = {"mandante": "C", "visitante": "F"}
    eixo = [
        f"{adv} ({marca.get(local, '?')})"
        for adv, local in zip(jogos["adversario"], jogos["local"])
    ]
    placares = [
        f"{int(gp)} x {int(gc)}"
        for gp, gc in zip(jogos["gols_pro"], jogos["gols_contra"])
    ]

    fig = go.Figure()
    for resultado, nome in ROTULO_RESULTADO.items():
        marcados = [i for i in posicoes if jogos["resultado"].iloc[i] == resultado]
        if not marcados:
            continue
        cor = paleta[resultado]
        fig.add_trace(
            go.Bar(
                x=marcados,
                y=[jogos["pontos"].iloc[i] for i in marcados],
                name=nome,
                offsetgroup="forma",  # um jogo por posição: sem deslocar as barras
                marker=dict(color=cor),
                text=[placares[i] for i in marcados] if mostrar_valores else None,
                textposition="outside",
                textfont=dict(color=TINTA_SECUNDARIA, size=11),
                insidetextfont=dict(color=cor_texto_para(cor)),
                customdata=[
                    [eixo[i], placares[i], str(jogos["data"].iloc[i])[:10]]
                    for i in marcados
                ],
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "%{customdata[1]} · %{y} ponto(s)<br>"
                    "%{customdata[2]}<extra></extra>"
                ),
            )
        )

    sufixo = f" — {aproveitamento}% de aproveitamento" if aproveitamento else ""
    fig.update_layout(
        template=TEMA,
        title=titulo or f"{time} — últimos {len(jogos)} jogos{sufixo}".strip(" —"),
        xaxis=dict(
            title=None,
            showgrid=False,
            tickmode="array",
            tickvals=posicoes,
            ticktext=eixo,
            tickangle=-30,
        ),
        yaxis=dict(title="Pontos", dtick=1, rangemode="tozero"),
        barmode="group",
        bargap=0.35,
        showlegend=mostrar_legenda,
    )
    return _finalizar(fig, layout_kwargs)


ROTULO_SEQUENCIA = {
    "vitorias": "Vitórias seguidas",
    "invencibilidade": "Jogos invicto",
    "derrotas": "Derrotas seguidas",
    "sem_vencer": "Jogos sem vencer",
}


def sequencias(
    seq: pd.DataFrame,
    titulo: Optional[str] = None,
    cores: Cores = None,
    mostrar_valores: bool = True,
    **layout_kwargs,
) -> go.Figure:
    """Barras das maiores sequências do time (recordes do recorte).

    Espera a saída de :func:`dashgusbr.analytics.sequencias`. Cada tipo tem
    sua cor (as boas em azul/verde, as ruins em vermelho/cinza) porque as
    quatro barras não são a mesma grandeza; o período de cada recorde fica no
    hover.
    """
    time = seq.attrs.get("time", "")
    paleta = dict(
        zip(
            ROTULO_SEQUENCIA,
            _como_lista(cores, 4, [AZUL, VERDE, VERMELHO, CINZA_NEUTRO]),
        )
    )
    dados = seq.iloc[::-1]  # a primeira linha no topo do eixo y
    rotulos = [ROTULO_SEQUENCIA.get(t, t) for t in dados["tipo"]]
    barras = [paleta.get(t, AZUL) for t in dados["tipo"]]

    def _periodo(inicio, fim) -> str:
        if pd.isna(inicio) or pd.isna(fim):
            return "sem registro"
        return f"{str(inicio)[:10]} → {str(fim)[:10]}"

    fig = go.Figure(
        go.Bar(
            x=dados["tamanho"],
            y=rotulos,
            orientation="h",
            marker=dict(color=barras),
            text=dados["tamanho"] if mostrar_valores else None,
            textposition="outside",
            textfont=dict(color=TINTA_SECUNDARIA, size=12),
            insidetextfont=dict(color=[cor_texto_para(c) for c in barras]),
            customdata=[
                _periodo(i, f) for i, f in zip(dados["inicio"], dados["fim"])
            ],
            hovertemplate=(
                "<b>%{y}</b><br>%{x} jogos<br>%{customdata}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        template=TEMA,
        title=titulo or f"{time} — maiores sequências".strip(" —"),
        xaxis=dict(title="Jogos", rangemode="tozero", dtick=1),
        yaxis=dict(title=None, showgrid=False),
        showlegend=False,
        bargap=0.4,
    )
    return _finalizar(fig, layout_kwargs)


# ---------------------------------------------------------------------------
# Estatísticas do campeonato
# ---------------------------------------------------------------------------


def gols_por_temporada(
    estatisticas: pd.DataFrame,
    titulo: Optional[str] = None,
    cores: Cores = None,
    **layout_kwargs,
) -> go.Figure:
    """Linha da média de gols por jogo em cada temporada.

    Espera a saída de :func:`dashgusbr.analytics.estatisticas_temporada`.
    """
    (cor,) = _como_lista(cores, 1, [AZUL])
    fig = go.Figure(
        go.Scatter(
            x=estatisticas["ano_campeonato"],
            y=estatisticas["media_gols"],
            mode="lines",
            line=dict(color=cor, width=2),
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
    return _finalizar(fig, layout_kwargs)


def mandante_visitante(
    estatisticas: pd.DataFrame,
    titulo: Optional[str] = None,
    cores: Cores = None,
    mostrar_legenda: bool = True,
    **layout_kwargs,
) -> go.Figure:
    """Linhas do fator casa: % de vitórias do mandante, empates e do visitante.

    Espera a saída de :func:`dashgusbr.analytics.estatisticas_temporada`.
    Mandante e visitante recebem slots categóricos; o empate usa o cinza
    neutro.
    """
    paleta = _como_lista(cores, 3, [AZUL, CINZA_NEUTRO, VERDE])
    series = [
        ("Vitória do mandante", "pct_vitorias_mandante", paleta[0]),
        ("Empate", "pct_empates", paleta[1]),
        ("Vitória do visitante", "pct_vitorias_visitante", paleta[2]),
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
        showlegend=mostrar_legenda,
    )
    return _finalizar(fig, layout_kwargs)


def distribuicao_placares(
    matriz: pd.DataFrame,
    titulo: Optional[str] = None,
    **layout_kwargs,
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
    return _finalizar(fig, layout_kwargs)


def estados(
    stats: pd.DataFrame,
    titulo: Optional[str] = None,
    cores: Cores = None,
    **layout_kwargs,
) -> go.Figure:
    """Barras de jogos como mandante por estado (UF).

    Espera a saída de :func:`dashgusbr.analytics.estatisticas_estados`. O
    detalhe (gols, clubes distintos, fator casa) fica no hover.
    """
    dados = stats.sort_values("jogos", ascending=True)
    (cor,) = _como_lista(cores, 1, [AZUL])

    fig = go.Figure(
        go.Bar(
            x=dados["jogos"],
            y=dados["estado"],
            orientation="h",
            marker=dict(color=cor),
            customdata=dados[["gols", "times", "pct_vitorias_mandante"]],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "%{x} jogos como mandante · %{customdata[0]} gols<br>"
                "%{customdata[1]} clubes · mandante vence %{customdata[2]}%"
                "<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        template=TEMA,
        title=titulo or "Jogos por estado (mando de campo)",
        xaxis_title="Jogos como mandante",
        yaxis=dict(title=None, showgrid=False),
        showlegend=False,
        bargap=0.35,
        height=max(360, 96 + 20 * len(dados)),
    )
    return _finalizar(fig, layout_kwargs)


def lideres(
    contagem: pd.DataFrame,
    top: int = 15,
    titulo: Optional[str] = None,
    cores: Cores = None,
    mostrar_valores: bool = True,
    **layout_kwargs,
) -> go.Figure:
    """Barras de quantas vezes cada clube terminou líder dos pontos corridos.

    Espera a saída de :func:`dashgusbr.analytics.contagem_lideres`. Atenção:
    líder da fase de pontos corridos ≠ campeão nas eras de mata-mata.
    """
    dados = contagem.head(top).iloc[::-1]
    (cor,) = _como_lista(cores, 1, [AZUL])

    fig = go.Figure(
        go.Bar(
            x=dados["lideracas"],
            y=dados["time"],
            orientation="h",
            marker=dict(color=cor),
            text=dados["lideracas"] if mostrar_valores else None,
            textposition="outside",
            textfont=dict(color=TINTA_SECUNDARIA, size=12),
            insidetextfont=dict(color=cor_texto_para(cor)),
            customdata=dados[["anos"]],
            hovertemplate=(
                "<b>%{y}</b>: %{x} vez(es) líder<br>%{customdata[0]}"
                "<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        template=TEMA,
        title=titulo or "Líderes da fase de pontos corridos, por clube",
        xaxis_title="Vezes na liderança",
        yaxis=dict(title=None, showgrid=False),
        showlegend=False,
        bargap=0.35,
        height=max(360, 96 + 24 * len(dados)),
    )
    return _finalizar(fig, layout_kwargs)


# ---------------------------------------------------------------------------
# Confronto no tempo, saldos e mapa
# ---------------------------------------------------------------------------


def evolucao_confronto(
    linha_tempo: pd.DataFrame,
    titulo: Optional[str] = None,
    cores: Cores = None,
    usar_cores_times: bool = False,
    **layout_kwargs,
) -> go.Figure:
    """Linha do saldo acumulado de um confronto direto ao longo dos anos.

    Espera a saída de :func:`dashgusbr.analytics.evolucao_confronto`. Saldo
    positivo = vantagem do ``time_a``; a linha do zero é o equilíbrio. Uma
    série só → a cor identifica o time de referência.
    """
    time_a = linha_tempo.attrs.get("time_a", "Time A")
    time_b = linha_tempo.attrs.get("time_b", "Time B")
    padrao = cores_para_times([time_a]) if usar_cores_times else [AZUL]
    (cor,) = _como_lista(cores, 1, padrao)

    fig = go.Figure(
        go.Scatter(
            x=linha_tempo["data"],
            y=linha_tempo["saldo_acumulado"],
            mode="lines",
            line=dict(color=cor, width=2, shape="hv"),
            customdata=linha_tempo[["mandante", "placar", "visitante"]],
            hovertemplate=(
                "%{x|%d/%m/%Y}<br>"
                "%{customdata[0]} %{customdata[1]} %{customdata[2]}<br>"
                f"Saldo de {time_a}: %{{y}}<extra></extra>"
            ),
        )
    )
    fig.add_hline(y=0, line=dict(color=CINZA_NEUTRO, width=1, dash="dot"))
    fig.update_layout(
        template=TEMA,
        title=titulo or f"{time_a} x {time_b} — saldo do confronto na história",
        xaxis_title="Ano",
        yaxis_title=f"Saldo de vitórias de {time_a}",
        showlegend=False,
    )
    return _finalizar(fig, layout_kwargs)


def distribuicao_saldos(
    contagem: pd.DataFrame,
    titulo: Optional[str] = None,
    cores: Cores = None,
    mostrar_valores: bool = False,
    **layout_kwargs,
) -> go.Figure:
    """Histograma do saldo de gols por jogo (mandante − visitante).

    Espera a saída de :func:`dashgusbr.analytics.distribuicao_saldos`. A
    assimetria para a direita é o fator casa; o zero (empates) usa o cinza
    neutro, sem lado.
    """
    (cor,) = _como_lista(cores, 1, [AZUL])
    paleta = [CINZA_NEUTRO if s == 0 else cor for s in contagem["saldo"]]
    maximo = int(contagem["saldo"].max())
    rotulos = [
        f"{s:+d}" if abs(s) < maximo else f"{s:+d}{'+' if s > 0 else ''}"
        for s in contagem["saldo"]
    ]

    fig = go.Figure(
        go.Bar(
            x=rotulos,
            y=contagem["jogos"],
            marker=dict(color=paleta),
            text=contagem["jogos"] if mostrar_valores else None,
            textposition="outside",
            textfont=dict(color=TINTA_SECUNDARIA, size=11),
            insidetextfont=dict(color=[cor_texto_para(c) for c in paleta]),
            hovertemplate="Saldo %{x}: %{y} jogos<extra></extra>",
        )
    )
    fig.update_layout(
        template=TEMA,
        title=titulo or "Distribuição do saldo de gols por jogo",
        xaxis=dict(title="Saldo do mandante (gols)", showgrid=False),
        yaxis_title="Jogos",
        showlegend=False,
        bargap=0.2,
    )
    return _finalizar(fig, layout_kwargs)


def mapa_estados(
    stats: pd.DataFrame,
    geojson: dict,
    metrica: str = "jogos",
    titulo: Optional[str] = None,
    **layout_kwargs,
) -> go.Figure:
    """Mapa coroplético do Brasil com uma métrica por UF.

    Espera a saída de :func:`dashgusbr.analytics.estatisticas_estados` e um
    GeoJSON dos estados cujas features tenham a sigla da UF em
    ``properties.sigla`` (use :func:`dashgusbr.data.carregar_geojson_estados`).
    Magnitude → rampa sequencial de um matiz.
    """
    if metrica not in stats.columns:
        raise ValueError(f"Métrica {metrica!r} não existe nas estatísticas por UF.")

    fig = go.Figure(
        go.Choropleth(
            geojson=geojson,
            featureidkey="properties.sigla",
            locations=stats["estado"],
            z=stats[metrica],
            colorscale=escala_sequencial(),
            marker=dict(line=dict(color="#ffffff", width=0.5)),
            colorbar=dict(title=metrica.replace("_", " ").capitalize(), outlinewidth=0),
            customdata=stats[["jogos", "gols", "times"]],
            hovertemplate=(
                "<b>%{location}</b><br>"
                f"{metrica}: %{{z}}<br>"
                "%{customdata[0]} jogos · %{customdata[1]} gols · "
                "%{customdata[2]} clubes<extra></extra>"
            ),
        )
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        template=TEMA,
        title=titulo or f"Brasileirão por estado — {metrica.replace('_', ' ')}",
        height=560,
    )
    return _finalizar(fig, layout_kwargs)

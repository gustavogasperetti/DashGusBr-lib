"""Dashboards prontos da dashgusbr: o retrato de um time em uma só figura.

A ideia é chamar pelo time e receber um painel completo, sem montar gráfico
por gráfico::

    from dashgusbr import Brasileirao

    br = Brasileirao()
    br.dashboard("Palmeiras").show()              # campeonato atual da base
    br.dashboard("Palmeiras", ano_campeonato=2020).show()   # temporada antiga

O conjunto inicial de painéis é fixo (:data:`PAINEIS_PADRAO`) — é o padrão
que faz dois times, ou duas temporadas do mesmo time, serem comparáveis de
bate-pronto. A personalização acontece *em cima* desse padrão:

- ``incluir=["sequencias"]``       acrescenta painéis do catálogo;
- ``remover=["adversarios"]``      tira painéis do padrão;
- ``incluir=[minha_figura]``       acrescenta um gráfico seu (uma
  ``go.Figure`` pronta, ou uma função ``lambda ctx: go.Figure``);
- ``paineis=[...]``                ignora o padrão e define a lista inteira;
- ``registrar_painel(...)``        publica um painel seu no catálogo, para
  reusar pelo nome em qualquer dashboard.

Veja o catálogo com :func:`paineis_disponiveis` (ou ``br.paineis()``).

Cada painel é uma ``go.Figure`` independente (quase sempre uma função de
:mod:`dashgusbr.viz`); o módulo apenas as compõe em uma grade de subplots,
remapeando eixos, anotações, formas e barras de cor para a célula certa.
Legendas viram uma mini-legenda por painel — uma legenda global em um
dashboard alto ficaria longe do gráfico que ela explica.

Limite conhecido: cada painel entra em UMA célula, com um par de eixos. Uma
figura com eixo secundário (``yaxis2``) cabe como painel, mas as séries dela
são desenhadas todas no mesmo eixo — para eixo duplo, exporte essa figura
separadamente com :func:`dashgusbr.salvar_html`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping, Optional, Sequence, Union

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import analytics, viz
from ._cores_times import cor_time
from ._theme import (
    AZUL,
    CINZA_NEUTRO,
    TEMA,
    TEMA_ESCURO,
    TINTA,
    TINTA_CLARA,
    TINTA_CLARA_SECUNDARIA,
    TINTA_SECUNDARIA,
    VERDE,
    registrar_tema,
)

registrar_tema()

VERMELHO = viz.VERMELHO

# Grade interna: 6 colunas dividem exato por 1, 2, 3 e 6 painéis por linha.
COLUNAS_GRADE = 6

ALTURA_KPI = 116  # altura da faixa de indicadores
ESPACO_LINHA = 96  # respiro vertical entre linhas de painéis (px)
MARGEM_TOPO = 120  # espaço do título + subtítulo
MARGEM_BASE = 64
MARGEM_ESQUERDA = 68
MARGEM_DIREITA = 56

# A figura é responsiva (sem ``width``), mas o espaço para os rótulos do eixo
# y é pedido em px: esta é a largura de referência para convertê-lo em fração.
LARGURA_NOMINAL = 1200


# ---------------------------------------------------------------------------
# Contexto: o recorte que todo painel recebe
# ---------------------------------------------------------------------------


class Contexto:
    """O recorte de um dashboard: base, time já resolvido e temporada.

    É o único argumento que um painel recebe. Os filtros derivados
    (:attr:`df_ano`, :attr:`df_time_ano`) são preguiçosos e ficam em cache —
    um dashboard com oito painéis não refaz oito vezes o mesmo filtro.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        time: str,
        ano: int,
        cor: str = AZUL,
        cores_times: bool = False,
    ) -> None:
        self.df = df
        self.time = time
        self.ano = ano
        self.cor = cor
        self.cores_times = cores_times
        self._df_ano: Optional[pd.DataFrame] = None
        self._df_time_ano: Optional[pd.DataFrame] = None

    @property
    def df_ano(self) -> pd.DataFrame:
        """Todas as partidas da temporada do recorte."""
        if self._df_ano is None:
            self._df_ano = self.df[self.df["ano_campeonato"] == self.ano]
        return self._df_ano

    @property
    def df_time_ano(self) -> pd.DataFrame:
        """Só as partidas do time na temporada do recorte."""
        if self._df_time_ano is None:
            base = self.df_ano
            self._df_time_ano = base[
                (base["mandante"] == self.time) | (base["visitante"] == self.time)
            ]
        return self._df_time_ano

    def __repr__(self) -> str:
        return f"Contexto(time={self.time!r}, ano={self.ano})"


Construtor = Callable[[Contexto], object]


@dataclass(frozen=True)
class Painel:
    """Um painel do catálogo: como construir a figura e como rotulá-la.

    ``construir`` recebe o :class:`Contexto` e devolve uma ``go.Figure`` —
    ou, quando ``tipo="kpi"``, uma lista de ``go.Indicator``.
    """

    nome: str
    construir: Construtor
    titulo: Union[str, Callable[[Contexto], str], None] = None
    descricao: str = ""
    tipo: str = "xy"  # "xy" (subplot cartesiano) ou "kpi" (faixa de números)
    largura: int = 1  # em painéis: 1 = uma célula, 2 = duas células
    altura_min: int = 0  # px; a linha inteira cresce para caber o painel
    margem_esquerda: int = 0  # px que os rótulos do eixo y precisam à esquerda


# ---------------------------------------------------------------------------
# Painéis do catálogo
# ---------------------------------------------------------------------------


def _linha_do_time(ctx: Contexto) -> pd.Series:
    """A linha do time na classificação da temporada (erro claro se não jogou)."""
    tabela = analytics.classificacao(ctx.df, ctx.ano)
    linha = tabela[tabela["time"] == ctx.time]
    if linha.empty:
        raise ValueError(
            f"{ctx.time!r} não disputou a fase de pontos corridos de {ctx.ano}."
        )
    return linha.iloc[0]


def _temporada_anterior(ctx: Contexto) -> Optional[pd.Series]:
    """A campanha do time na temporada anterior que ele disputou, se houver."""
    corridos = analytics._pontos_corridos(ctx.df)
    do_time = corridos[
        (corridos["mandante"] == ctx.time) | (corridos["visitante"] == ctx.time)
    ]
    anteriores = do_time["ano_campeonato"].dropna()
    anteriores = anteriores[anteriores < ctx.ano]
    if anteriores.empty:
        return None
    anterior = Contexto(ctx.df, ctx.time, int(anteriores.max()))
    try:
        return _linha_do_time(anterior)
    except ValueError:  # jogou no ano, mas não entrou na classificação
        return None


def _painel_indicadores(ctx: Contexto) -> "list[go.Indicator]":
    """Faixa de números da campanha: posição, pontos, V/E/D e aproveitamento."""
    atual = _linha_do_time(ctx)
    anterior = _temporada_anterior(ctx)

    # (rótulo, coluna, sufixo, formato, compara com a temporada anterior?, menor é melhor?)
    kpis = [
        ("Posição", "posicao", "º", None, True, True),
        ("Pontos", "pontos", "", None, True, False),
        ("Vitórias", "vitorias", "", None, False, False),
        ("Empates", "empates", "", None, False, False),
        ("Derrotas", "derrotas", "", None, False, False),
        ("Aproveitamento", "aproveitamento", "%", ".1f", True, False),
    ]

    indicadores = []
    for rotulo, coluna, sufixo, formato, comparar, menor_melhor in kpis:
        referencia = (
            float(anterior[coluna]) if comparar and anterior is not None else None
        )
        indicador = go.Indicator(
            mode="number+delta" if referencia is not None else "number",
            value=float(atual[coluna]),
            number=dict(
                font=dict(size=32),
                suffix=sufixo,
                valueformat=formato or "d",
            ),
            title=dict(text=rotulo, font=dict(size=12)),
        )
        if referencia is not None:
            indicador.delta = dict(
                reference=referencia,
                valueformat=formato or "d",
                font=dict(size=12),
                increasing=dict(color=VERMELHO if menor_melhor else VERDE),
                decreasing=dict(color=VERDE if menor_melhor else VERMELHO),
            )
        indicadores.append(indicador)
    return indicadores


def _painel_evolucao(ctx: Contexto) -> go.Figure:
    evolucao = analytics.evolucao_pontos(ctx.df, ctx.time, ctx.ano)
    fig = viz.evolucao(evolucao, cores=ctx.cor, mostrar_legenda=False)
    fig.layout.annotations = ()  # o título do painel já nomeia a série
    return fig


def _painel_classificacao(ctx: Contexto) -> go.Figure:
    return viz.classificacao(
        analytics.classificacao(ctx.df, ctx.ano),
        cores=ctx.cor,
        destaque=ctx.time,
        mostrar_valores=False,
    )


def _painel_casa_fora(ctx: Contexto) -> go.Figure:
    return viz.casa_fora(analytics.casa_fora(ctx.df, ctx.time, ano=ctx.ano))


def _painel_forma(ctx: Contexto) -> go.Figure:
    return viz.forma(analytics.forma_recente(ctx.df_ano, ctx.time, n=8))


def _painel_adversarios(ctx: Contexto) -> go.Figure:
    return viz.desempenho_contra(
        analytics.desempenho_contra(ctx.df_ano, ctx.time), top=12, cores=ctx.cor
    )


def _painel_adversarios_historico(ctx: Contexto) -> go.Figure:
    return viz.desempenho_contra(
        analytics.desempenho_contra(ctx.df, ctx.time, min_jogos=5),
        top=12,
        cores=ctx.cor,
    )


def _painel_historico(ctx: Contexto) -> go.Figure:
    fig = viz.historico(
        analytics.historico_time(ctx.df, ctx.time),
        metrica="aproveitamento",
        cores=ctx.cor,
    )
    fig.add_vline(  # marca onde, na carreira do clube, está a temporada aberta
        x=ctx.ano,
        line=dict(color=CINZA_NEUTRO, width=1, dash="dot"),
    )
    return fig


def _painel_posicao(ctx: Contexto) -> go.Figure:
    fig = viz.historico(
        analytics.historico_time(ctx.df, ctx.time), metrica="posicao", cores=ctx.cor
    )
    fig.update_yaxes(autorange="reversed", title="Posição final")
    return fig


def _painel_sequencias(ctx: Contexto) -> go.Figure:
    return viz.sequencias(analytics.sequencias(ctx.df, ctx.time, ano=ctx.ano))


def _painel_placares(ctx: Contexto) -> go.Figure:
    return viz.distribuicao_placares(
        analytics.distribuicao_placares(ctx.df_time_ano, max_gols=4)
    )


def _painel_saldos(ctx: Contexto) -> go.Figure:
    return viz.distribuicao_saldos(
        analytics.distribuicao_saldos(ctx.df_time_ano, max_saldo=4), cores=ctx.cor
    )


def _catalogo_inicial() -> "list[Painel]":
    return [
        Painel(
            nome="indicadores",
            construir=_painel_indicadores,
            tipo="kpi",
            descricao="Campanha em números, com a variação sobre a temporada anterior",
        ),
        Painel(
            nome="evolucao",
            construir=_painel_evolucao,
            titulo=lambda ctx: f"Pontos acumulados em {ctx.ano}",
            descricao="Pontuação acumulada jogo a jogo na temporada",
        ),
        Painel(
            nome="casa_fora",
            construir=_painel_casa_fora,
            titulo=lambda ctx: f"Casa × fora em {ctx.ano}",
            descricao="V/E/D como mandante e como visitante na temporada",
        ),
        Painel(
            nome="classificacao",
            construir=_painel_classificacao,
            titulo=lambda ctx: f"Classificação de {ctx.ano}",
            descricao="Tabela da temporada com o time destacado",
            altura_min=520,
            margem_esquerda=156,  # "12º Athletico Paranaense" cabe inteiro
        ),
        Painel(
            nome="adversarios",
            construir=_painel_adversarios,
            titulo=lambda ctx: f"Aproveitamento por adversário em {ctx.ano}",
            descricao="Retrospecto contra cada adversário da temporada",
            altura_min=440,
            margem_esquerda=140,
        ),
        Painel(
            nome="forma",
            construir=_painel_forma,
            titulo=lambda ctx: f"Últimos jogos de {ctx.ano}",
            descricao="Pontos jogo a jogo no fim da temporada",
        ),
        Painel(
            nome="historico",
            construir=_painel_historico,
            titulo="Aproveitamento por temporada",
            descricao="Toda a história do clube na base, com a temporada marcada",
        ),
        Painel(
            nome="posicao",
            construir=_painel_posicao,
            titulo="Posição final por temporada",
            descricao="Toda a história do clube, do 1º lugar para baixo",
        ),
        Painel(
            nome="sequencias",
            construir=_painel_sequencias,
            titulo=lambda ctx: f"Maiores sequências em {ctx.ano}",
            descricao="Recordes de vitórias, invencibilidade, derrotas e jejum",
            margem_esquerda=124,
        ),
        Painel(
            nome="placares",
            construir=_painel_placares,
            titulo=lambda ctx: f"Placares dos jogos em {ctx.ano}",
            descricao="Heatmap dos placares das partidas do time na temporada",
            altura_min=420,
        ),
        Painel(
            nome="saldos",
            construir=_painel_saldos,
            titulo=lambda ctx: f"Saldo por jogo em {ctx.ano}",
            descricao="Distribuição do saldo de gols dos jogos do time",
        ),
        Painel(
            nome="adversarios_historico",
            construir=_painel_adversarios_historico,
            titulo="Aproveitamento por adversário (história)",
            descricao="Retrospecto contra quem o clube mais enfrentou na base",
            altura_min=440,
            margem_esquerda=140,
        ),
    ]


#: Catálogo de painéis disponíveis, por nome (veja :func:`registrar_painel`).
PAINEIS: "dict[str, Painel]" = {p.nome: p for p in _catalogo_inicial()}

#: Os painéis que todo dashboard por time traz — o padrão comparável.
PAINEIS_PADRAO = (
    "indicadores",
    "evolucao",
    "casa_fora",
    "classificacao",
    "adversarios",
    "forma",
    "historico",
)


def registrar_painel(
    nome: str,
    construir: Construtor,
    titulo: Union[str, Callable[[Contexto], str], None] = None,
    descricao: str = "",
    largura: int = 1,
    altura_min: int = 0,
    margem_esquerda: int = 0,
    tipo: str = "xy",
) -> Painel:
    """Publica um painel seu no catálogo, reusável pelo nome.

    ``construir`` recebe o :class:`Contexto` (base, time resolvido, temporada
    e os filtros derivados) e devolve uma ``go.Figure``::

        from dashgusbr import dashboard

        dashboard.registrar_painel(
            "gols_pro",
            lambda ctx: px.bar(...),
            titulo="Gols marcados por temporada",
        )
        br.dashboard("Santos", incluir=["gols_pro"])

    Registrar com um nome já existente substitui o painel anterior.
    """
    painel = Painel(
        nome=nome,
        construir=construir,
        titulo=titulo,
        descricao=descricao,
        largura=largura,
        altura_min=altura_min,
        margem_esquerda=margem_esquerda,
        tipo=tipo,
    )
    PAINEIS[nome] = painel
    return painel


def paineis_disponiveis() -> pd.DataFrame:
    """O catálogo de painéis: nome, se entra no padrão e o que cada um mostra."""
    return pd.DataFrame(
        [
            {
                "painel": p.nome,
                "padrao": p.nome in PAINEIS_PADRAO,
                "descricao": p.descricao,
            }
            for p in PAINEIS.values()
        ]
    )


# ---------------------------------------------------------------------------
# Seleção dos painéis
# ---------------------------------------------------------------------------


def _como_sequencia(item) -> list:
    if item is None:
        return []
    if isinstance(item, Mapping):
        return [(titulo, valor) for titulo, valor in item.items()]
    if isinstance(item, (str, Painel, go.Figure)) or callable(item):
        return [item]
    return list(item)


def _como_painel(item, indice: int) -> Painel:
    """Aceita nome do catálogo, ``Painel``, figura, função ou ``(título, item)``."""
    titulo = None
    if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str):
        titulo, item = item

    if isinstance(item, Painel):
        return item
    if isinstance(item, str):
        if item not in PAINEIS:
            raise ValueError(
                f"Painel {item!r} não existe. Disponíveis: "
                f"{', '.join(sorted(PAINEIS))}."
            )
        return PAINEIS[item]
    if isinstance(item, go.Figure):
        return Painel(
            nome=titulo or f"personalizado_{indice}",
            construir=lambda ctx, figura=item: figura,
            titulo=titulo,
            descricao="Figura fornecida pelo usuário",
        )
    if callable(item):
        return Painel(
            nome=titulo or getattr(item, "__name__", f"personalizado_{indice}"),
            construir=item,
            titulo=titulo,
            descricao="Painel fornecido pelo usuário",
        )
    raise TypeError(
        "Painel inválido: use o nome de um painel do catálogo, uma go.Figure, "
        f"uma função (ctx) -> go.Figure ou um Painel — recebido {type(item).__name__}."
    )


def _selecionar(paineis, incluir, remover) -> "list[Painel]":
    escolhidos = [
        _como_painel(item, i)
        for i, item in enumerate(
            _como_sequencia(paineis) if paineis is not None else list(PAINEIS_PADRAO)
        )
    ]
    for item in _como_sequencia(remover):
        nome = item.nome if isinstance(item, Painel) else item
        restantes = [p for p in escolhidos if p.nome != nome]
        if len(restantes) == len(escolhidos):
            raise ValueError(
                f"Painel {nome!r} não está no dashboard. Presentes: "
                f"{', '.join(p.nome for p in escolhidos)}."
            )
        escolhidos = restantes
    for i, item in enumerate(_como_sequencia(incluir)):
        painel = _como_painel(item, len(escolhidos) + i)
        if painel.nome not in {p.nome for p in escolhidos}:
            escolhidos.append(painel)
    if not escolhidos:
        raise ValueError("Nenhum painel selecionado para o dashboard.")
    return escolhidos


# ---------------------------------------------------------------------------
# Montagem da grade
# ---------------------------------------------------------------------------


@dataclass
class _Celula:
    painel: Painel
    conteudo: object  # go.Figure ou go.Indicator
    coluna: int  # 1-based, na grade de COLUNAS_GRADE colunas
    colspan: int


@dataclass
class _Linha:
    celulas: "list[_Celula]" = field(default_factory=list)
    altura: int = 0


def _distribuir(total: int, n: int) -> "list[int]":
    """Divide ``total`` colunas entre ``n`` células, o resto nas primeiras."""
    base, resto = divmod(total, n)
    return [base + (1 if i < resto else 0) for i in range(n)]


def _montar_linhas(construidos, colunas: int, altura_linha: int) -> "list[_Linha]":
    """Distribui os painéis já construídos nas linhas da grade."""
    largura_celula = COLUNAS_GRADE // colunas
    linhas: "list[_Linha]" = []
    atual = _Linha()
    ocupado = 0

    for painel, conteudo in construidos:
        if painel.tipo == "kpi":
            if atual.celulas:
                linhas.append(atual)
                atual, ocupado = _Linha(), 0
            indicadores = list(conteudo)
            # a faixa de números ocupa linhas inteiras, até 6 indicadores cada
            for inicio in range(0, len(indicadores), COLUNAS_GRADE):
                bloco = indicadores[inicio : inicio + COLUNAS_GRADE]
                linha = _Linha(altura=ALTURA_KPI)
                coluna = 1
                for indicador, span in zip(
                    bloco, _distribuir(COLUNAS_GRADE, len(bloco))
                ):
                    linha.celulas.append(_Celula(painel, indicador, coluna, span))
                    coluna += span
                linhas.append(linha)
            continue

        largura = min(painel.largura, colunas) * largura_celula
        if ocupado + largura > COLUNAS_GRADE and atual.celulas:
            linhas.append(atual)
            atual, ocupado = _Linha(), 0
        atual.celulas.append(_Celula(painel, conteudo, ocupado + 1, largura))
        atual.altura = max(atual.altura or altura_linha, painel.altura_min)
        ocupado += largura

    if atual.celulas:
        linhas.append(atual)
    return linhas


def _margens_horizontais(linhas: "list[_Linha]", colunas: int) -> "tuple[int, float]":
    """Quanto espaço reservar à esquerda da figura e entre as colunas.

    Barras horizontais (classificação, adversários) escrevem nomes de clube
    fora da área do gráfico: na primeira coluna eles caem na margem da
    figura, nas demais caem na calha entre as colunas. Sem essa reserva, o
    Plotly corta os rótulos da primeira coluna e deixa os das outras por cima
    do painel vizinho.
    """
    esquerda = MARGEM_ESQUERDA
    calha_px = 0
    for linha in linhas:
        for celula in linha.celulas:
            if celula.coluna == 1:
                esquerda = max(esquerda, celula.painel.margem_esquerda)
            else:
                calha_px = max(calha_px, celula.painel.margem_esquerda)
    disponivel = max(LARGURA_NOMINAL - esquerda - MARGEM_DIREITA, 240)
    # o teto mantém cada painel pelo menos tão largo quanto a calha
    teto = 1 / (2 * colunas - 1)
    return esquerda, min(teto, max(0.04, calha_px / disponivel))


# ---------------------------------------------------------------------------
# Cópia de uma figura para dentro de uma célula
# ---------------------------------------------------------------------------

_EIXO_IGNORADO = ("domain", "anchor", "matches", "overlaying", "scaleanchor")


def _nome_eixo(ref: str) -> str:
    """``"x3"`` → ``"xaxis3"`` (o nome do eixo no layout)."""
    return f"{ref[0]}axis{ref[1:]}"


def _remapear(ref, alvo: str) -> str:
    """Aponta uma referência de eixo da figura solta para a célula de destino."""
    if ref is None:
        return alvo
    if ref == "paper" or str(ref).endswith(" domain"):
        return f"{alvo} domain"
    return alvo


def _cor_da_trace(trace) -> str:
    """A cor que representa a série na mini-legenda."""
    for caminho in ("marker", "line"):
        objeto = trace[caminho] if caminho in trace else None
        cor = getattr(objeto, "color", None)
        if isinstance(cor, str):
            return cor
    return CINZA_NEUTRO


def _copiar_figura(destino: go.Figure, origem: go.Figure, linha: int, coluna: int):
    """Transplanta as traces, eixos, anotações e formas de ``origem`` para a célula.

    Devolve ``(ref_x, ref_y, legenda)`` — as referências de eixo da célula e
    os pares ``(nome, cor)`` que virariam legenda na figura solta.
    """
    ref_x = ref_y = None
    legenda: "list[tuple[str, str]]" = []
    mostrar_legenda = origem.layout.showlegend is not False

    for trace in origem.data:
        destino.add_trace(trace, row=linha, col=coluna)
        nova = destino.data[-1]
        if ref_x is None:
            ref_x = nova.xaxis or "x"
            ref_y = nova.yaxis or "y"
        if "showlegend" in nova:
            if mostrar_legenda and nova.name and nova.showlegend is not False:
                legenda.append((nova.name, _cor_da_trace(nova)))
            nova.showlegend = False
        if "colorbar" in nova:  # heatmaps: a barra de cor cola na própria célula
            dominio_x = destino.layout[_nome_eixo(ref_x)].domain
            dominio_y = destino.layout[_nome_eixo(ref_y)].domain
            nova.colorbar.update(
                x=dominio_x[1] + 0.006,
                xanchor="left",
                y=(dominio_y[0] + dominio_y[1]) / 2,
                yanchor="middle",
                len=dominio_y[1] - dominio_y[0],
                thickness=10,
            )

    if ref_x is None:  # figura sem traces: nada a transplantar
        return None, None, legenda

    for eixo, atualizar in (
        (origem.layout.xaxis, destino.update_xaxes),
        (origem.layout.yaxis, destino.update_yaxes),
    ):
        props = eixo.to_plotly_json()
        for chave in _EIXO_IGNORADO:
            props.pop(chave, None)
        if props:
            atualizar(row=linha, col=coluna, **props)

    for anotacao in origem.layout.annotations:
        dados = anotacao.to_plotly_json()
        dados["xref"] = _remapear(dados.get("xref"), ref_x)
        dados["yref"] = _remapear(dados.get("yref"), ref_y)
        destino.add_annotation(**dados)

    for forma in origem.layout.shapes:
        dados = forma.to_plotly_json()
        dados["xref"] = _remapear(dados.get("xref"), ref_x)
        dados["yref"] = _remapear(dados.get("yref"), ref_y)
        destino.add_shape(**dados)

    return ref_x, ref_y, legenda


# ---------------------------------------------------------------------------
# O dashboard
# ---------------------------------------------------------------------------


def _titulo_do_painel(painel: Painel, ctx: Contexto, figura) -> str:
    if callable(painel.titulo):
        return painel.titulo(ctx)
    if painel.titulo:
        return painel.titulo
    titulo_figura = getattr(getattr(figura, "layout", None), "title", None)
    return (getattr(titulo_figura, "text", None) or painel.nome).strip()


def _subtitulo(ctx: Contexto) -> str:
    jogos = ctx.df_time_ano.dropna(subset=["gols_mandante", "gols_visitante"])
    partes = [f"Temporada {ctx.ano}", f"{len(jogos)} jogos"]
    if not jogos.empty and jogos["data"].notna().any():
        partes.append(f"dados até {jogos['data'].max():%d/%m/%Y}")
    return " · ".join(partes)


def dashboard_time(
    df: pd.DataFrame,
    time: str,
    ano_campeonato: Optional[int] = None,
    *,
    ano: Optional[int] = None,
    paineis: Optional[Sequence] = None,
    incluir: Optional[Sequence] = None,
    remover: Optional[Sequence] = None,
    colunas: int = 2,
    altura_linha: int = 340,
    titulo: Optional[str] = None,
    subtitulo: Optional[str] = None,
    cores_times: bool = False,
    template: Optional[str] = None,
    **layout_kwargs,
) -> go.Figure:
    """O dashboard de um time em uma temporada, em uma única ``go.Figure``.

    Sem ``ano_campeonato``, usa o campeonato atual da base (a última
    temporada que o time disputou, via
    :func:`dashgusbr.analytics.ultima_temporada`) — informe
    ``ano_campeonato=2020`` para ver uma temporada antiga com exatamente os
    mesmos painéis.

    Parameters
    ----------
    df:
        A OBT completa (``dashgusbr.carregar_dados()``).
    time:
        Nome do clube, tolerante a acento e caixa ("gremio" → "Grêmio").
    ano_campeonato:
        Temporada do recorte. ``None`` = campeonato atual da base. Também
        aceito como ``ano=``.
    paineis:
        Substitui a lista padrão inteira (:data:`PAINEIS_PADRAO`).
    incluir, remover:
        Ajustam a lista padrão sem reescrevê-la. ``incluir`` aceita nomes do
        catálogo, ``go.Figure`` prontas, funções ``(ctx) -> go.Figure`` e
        pares ``("Meu título", figura_ou_função)``.
    colunas:
        Painéis por linha: 1, 2 (padrão), 3 ou 6.
    altura_linha:
        Altura base de cada linha, em px; painéis densos (classificação,
        adversários) esticam a linha deles.
    cores_times:
        ``True`` pinta as séries do clube com a cor oficial dele (opt-in: cor
        de clube não é segura para daltonismo).
    template:
        ``"dashgusbr_escuro"`` para o tema escuro.
    **layout_kwargs:
        Repassados a ``fig.update_layout`` por último (``width``, ``font``…).

    Examples
    --------
    >>> dashboard_time(df, "Palmeiras")                       # doctest: +SKIP
    >>> dashboard_time(df, "Palmeiras", 2020)                 # doctest: +SKIP
    >>> dashboard_time(df, "Santos", incluir=["sequencias"])  # doctest: +SKIP
    """
    if colunas not in (1, 2, 3, 6):
        raise ValueError(f"'colunas' deve ser 1, 2, 3 ou 6 — recebido {colunas!r}.")

    time = analytics._resolver_time(df, time)
    escolhido = ano_campeonato if ano_campeonato is not None else ano
    if escolhido is None:
        escolhido = analytics.ultima_temporada(df, time)
    else:
        analytics._validar_ano(df, int(escolhido))
    ctx = Contexto(
        df=df,
        time=time,
        ano=int(escolhido),
        cor=cor_time(time, AZUL) if cores_times else AZUL,
        cores_times=cores_times,
    )

    selecionados = _selecionar(paineis, incluir, remover)
    construidos = [(painel, painel.construir(ctx)) for painel in selecionados]
    linhas = _montar_linhas(construidos, colunas, altura_linha)

    alturas = [linha.altura or altura_linha for linha in linhas]
    util = sum(alturas) + ESPACO_LINHA * (len(linhas) - 1)
    total = MARGEM_TOPO + util + MARGEM_BASE
    esquerda, calha = _margens_horizontais(linhas, colunas)

    specs = []
    for linha in linhas:
        spec = [None] * COLUNAS_GRADE
        for celula in linha.celulas:
            spec[celula.coluna - 1] = {
                "type": "indicator" if celula.painel.tipo == "kpi" else "xy",
                "colspan": celula.colspan,
            }
        specs.append(spec)

    fig = make_subplots(
        rows=len(linhas),
        cols=COLUNAS_GRADE,
        specs=specs,
        row_heights=[a / sum(alturas) for a in alturas],
        vertical_spacing=(ESPACO_LINHA / util) if len(linhas) > 1 else 0.0,
        horizontal_spacing=calha,
    )

    # títulos e mini-legendas são texto nosso: precisam inverter no tema escuro
    escuro = template is not None and (
        template == TEMA_ESCURO or "dark" in template or "escuro" in template
    )
    tinta = TINTA_CLARA if escuro else TINTA
    tinta_2 = TINTA_CLARA_SECUNDARIA if escuro else TINTA_SECUNDARIA

    for numero, linha in enumerate(linhas, start=1):
        for celula in linha.celulas:
            if celula.painel.tipo == "kpi":
                fig.add_trace(celula.conteudo, row=numero, col=celula.coluna)
                continue
            ref_x, ref_y, legenda = _copiar_figura(
                fig, celula.conteudo, numero, celula.coluna
            )
            if ref_x is None:
                continue
            _rotular(
                fig,
                ref_x,
                ref_y,
                _titulo_do_painel(celula.painel, ctx, celula.conteudo),
                legenda,
                tinta,
                tinta_2,
            )

    for anotacao in fig.layout.annotations:  # herdadas das figuras dos painéis
        if anotacao.font is not None and anotacao.font.color == TINTA_SECUNDARIA:
            anotacao.font.color = tinta_2

    fig.update_layout(
        template=template or TEMA,
        title=dict(
            text=titulo or f"{time} — Brasileirão {ctx.ano}",
            font=dict(size=22, color=tinta),
            x=0,
            xanchor="left",
            y=1 - 30 / total,
            yanchor="top",
            yref="container",
        ),
        height=total,
        margin=dict(l=esquerda, r=MARGEM_DIREITA, t=MARGEM_TOPO, b=MARGEM_BASE),
        showlegend=False,
        barmode="group",
        bargap=0.3,
        hovermode="closest",
    )
    fig.add_annotation(  # y=1 é o topo da área de plotagem; o subtítulo sobe na margem
        text=subtitulo if subtitulo is not None else _subtitulo(ctx),
        xref="paper",
        yref="paper",
        x=0,
        xanchor="left",
        y=1,
        yanchor="bottom",
        yshift=40,
        showarrow=False,
        font=dict(size=13, color=tinta_2),
    )
    if layout_kwargs:
        fig.update_layout(**layout_kwargs)
    return fig


def _rotular(fig, ref_x, ref_y, titulo, legenda, tinta, tinta_2) -> None:
    """Título do painel à esquerda e, quando há séries nomeadas, a mini-legenda."""
    fig.add_annotation(
        text=f"<b>{titulo}</b>",
        xref=f"{ref_x} domain",
        yref=f"{ref_y} domain",
        x=0,
        xanchor="left",
        y=1,
        yanchor="bottom",
        yshift=8,
        showarrow=False,
        font=dict(size=13, color=tinta),
    )
    if legenda:
        marcas = "  ".join(
            f"<span style='color:{cor}'>■</span> {nome}" for nome, cor in legenda
        )
        fig.add_annotation(
            text=marcas,
            xref=f"{ref_x} domain",
            yref=f"{ref_y} domain",
            x=1,
            xanchor="right",
            y=1,
            yanchor="bottom",
            yshift=8,
            showarrow=False,
            font=dict(size=11, color=tinta_2),
        )

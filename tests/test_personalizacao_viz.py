"""Personalização dos gráficos: titulo=, cores=, layout_kwargs, cores por time."""

import plotly.graph_objects as go

from dashgusbr import analytics, viz
from dashgusbr._cores_times import cores_para_times
from dashgusbr._theme import CINZA_NEUTRO

# -- titulo=, layout_kwargs e cores= -----------------------------------------


def test_titulo_customizado(obt):
    fig = viz.classificacao(analytics.classificacao(obt, 2023), titulo="Meu título")
    assert fig.layout.title.text == "Meu título"


def test_layout_kwargs_tem_a_palavra_final(obt):
    fig = viz.classificacao(
        analytics.classificacao(obt, 2023), width=900, height=500
    )
    assert fig.layout.width == 900
    assert fig.layout.height == 500  # sobrescreve a altura automática


def test_layout_kwargs_troca_template(obt):
    fig = viz.gols_por_temporada(
        analytics.estatisticas_temporada(obt), template="plotly_dark"
    )
    assert fig.layout.template is not None


def test_cores_customizadas_serie_unica(obt):
    fig = viz.classificacao(analytics.classificacao(obt, 2023), cores="#ff5722")
    assert fig.data[0].marker.color == "#ff5722"


def test_cores_customizadas_multiplas_series(obt):
    evolucoes = analytics.corrida_titulo(obt, 2023, n=2)
    fig = viz.evolucao(evolucoes, cores=["#111111", "#222222"])
    assert [t.line.color for t in fig.data] == ["#111111", "#222222"]


# -- cores oficiais dos times --------------------------------------------------


def test_evolucao_com_cores_times(obt):
    evolucoes = analytics.corrida_titulo(obt, 2023, n=2)
    times = list(evolucoes["time"].unique())
    fig = viz.evolucao(evolucoes, usar_cores_times=True)
    assert [t.line.color for t in fig.data] == cores_para_times(times)


def test_confronto_com_cores_times(obt):
    resumo = analytics.confronto(obt, "Palmeiras", "Santos")
    fig = viz.confronto(resumo, usar_cores_times=True)
    cor_a, cor_b = cores_para_times(["Palmeiras", "Santos"])
    assert list(fig.data[0].marker.color) == [cor_a, CINZA_NEUTRO, cor_b]


def test_historico_com_cores_times(obt):
    fig = viz.historico(
        analytics.historico_time(obt, "Palmeiras"), usar_cores_times=True
    )
    assert fig.data[0].line.color == "#006437"


def test_cores_explicitas_vencem_cores_times(obt):
    fig = viz.historico(
        analytics.historico_time(obt, "Palmeiras"),
        cores="#ababab",
        usar_cores_times=True,
    )
    assert fig.data[0].line.color == "#ababab"


# -- novas visualizações (smoke) ------------------------------------------------


def test_viz_casa_fora(obt):
    fig = viz.casa_fora(analytics.casa_fora(obt, "Palmeiras"))
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 3  # vitórias, empates, derrotas
    assert "Palmeiras" in fig.layout.title.text


def test_viz_desempenho_contra(obt):
    fig = viz.desempenho_contra(analytics.desempenho_contra(obt, "Palmeiras"))
    assert isinstance(fig, go.Figure)
    assert list(fig.data[0].y) == ["Botafogo", "Santos"]  # invertido p/ eixo y


def test_viz_estados(obt):
    fig = viz.estados(analytics.estatisticas_estados(obt))
    assert isinstance(fig, go.Figure)
    assert set(fig.data[0].y) == {"SP", "RJ"}


def test_viz_lideres(obt):
    fig = viz.lideres(analytics.contagem_lideres(obt))
    assert isinstance(fig, go.Figure)
    assert list(fig.data[0].y) == ["Palmeiras"]
    assert list(fig.data[0].x) == [2]

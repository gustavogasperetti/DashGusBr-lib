import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from dashgusbr import analytics, viz
from dashgusbr._theme import TEMA


def test_template_registrado():
    assert TEMA in pio.templates


def test_classificacao_retorna_barras(obt):
    fig = viz.classificacao(analytics.classificacao(obt, 1971))
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].type == "bar"
    assert fig.layout.showlegend is False


def test_evolucao_uma_serie_sem_legenda(obt):
    evolucao = analytics.evolucao_pontos(obt, "Palmeiras", 1971)
    fig = viz.evolucao(evolucao)
    assert len(fig.data) == 1
    assert fig.layout.showlegend is False


def test_evolucao_varias_series_com_legenda(obt):
    evolucoes = pd.concat(
        [
            analytics.evolucao_pontos(obt, "Palmeiras", 1971),
            analytics.evolucao_pontos(obt, "Santos", 1971),
        ],
        ignore_index=True,
    )
    fig = viz.evolucao(evolucoes)
    assert len(fig.data) == 2
    assert fig.layout.showlegend is True


def test_historico(obt):
    fig = viz.historico(analytics.historico_time(obt, "Palmeiras"))
    assert isinstance(fig, go.Figure)
    assert fig.layout.yaxis.range == (0, 100)


def test_confronto_tres_categorias(obt):
    fig = viz.confronto(analytics.confronto(obt, "Palmeiras", "Santos"))
    assert len(fig.data[0].x) == 3
    assert list(fig.data[0].y) == [3, 0, 1]


def test_gols_por_temporada(obt):
    fig = viz.gols_por_temporada(analytics.estatisticas_temporada(obt))
    assert isinstance(fig, go.Figure)


def test_mandante_visitante_tres_series(obt):
    fig = viz.mandante_visitante(analytics.estatisticas_temporada(obt))
    assert len(fig.data) == 3


def test_distribuicao_placares_heatmap(obt):
    fig = viz.distribuicao_placares(analytics.distribuicao_placares(obt, max_gols=3))
    assert fig.data[0].type == "heatmap"
    assert list(fig.data[0].x) == ["0", "1", "2", "3+"]

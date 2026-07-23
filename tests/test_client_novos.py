"""Smoke tests dos novos métodos da fachada Brasileirao."""

import pandas as pd
import plotly.graph_objects as go
import pytest

from dashgusbr import Brasileirao


@pytest.fixture()
def br(caminho_csv) -> Brasileirao:
    return Brasileirao(fonte=caminho_csv, cache=False)


def test_plot_tabela_com_titulo_e_layout(br):
    fig = br.plot_tabela(2023, titulo="Custom", width=800)
    assert fig.layout.title.text == "Custom"
    assert fig.layout.width == 800


def test_plot_corrida_titulo(br):
    fig = br.plot_corrida_titulo(2023, n=2, cores_times=True)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2


def test_plot_confronto_cores_times(br):
    fig = br.plot_confronto("palmeiras", "santos", cores_times=True)
    assert list(fig.data[0].marker.color)[0] == "#006437"


def test_casa_fora_e_plot(br):
    assert br.casa_fora("Palmeiras")["jogos"].sum() == 7
    assert isinstance(br.plot_casa_fora("Palmeiras", ano=2023), go.Figure)


def test_sequencias_forma_resumo(br):
    assert not br.sequencias("Palmeiras").empty
    assert len(br.forma("Palmeiras", n=3)) == 3
    assert br.resumo("Palmeiras")["jogos"] == 8


def test_contra_e_plot(br):
    tabela = br.contra("Palmeiras")
    assert list(tabela["adversario"]) == ["Santos", "Botafogo"]
    assert isinstance(br.plot_contra("Palmeiras", top=1), go.Figure)


def test_estados_lideres_ranking(br):
    assert isinstance(br.estados(), pd.DataFrame)
    assert br.lideres()["time"].tolist() == ["Palmeiras", "Palmeiras"]
    assert br.ranking().iloc[0]["time"] == "Palmeiras"
    assert isinstance(br.plot_estados(), go.Figure)
    assert isinstance(br.plot_lideres(), go.Figure)


def test_classicos_e_fases(br):
    assert set(br.classicos()["grupo"]) == {"Clássico estadual", "Demais jogos"}
    assert set(br.fases()["grupo"]) == {"Mata-mata", "Fase de pontos"}

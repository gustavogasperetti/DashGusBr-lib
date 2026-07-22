import plotly.graph_objects as go
import pytest

from dashgusbr import Brasileirao


@pytest.fixture()
def br(caminho_csv) -> Brasileirao:
    return Brasileirao(fonte=caminho_csv, cache=False)


def test_carga_preguicosa(br):
    assert "não carregado" in repr(br)
    br.anos()
    assert "partidas" in repr(br)


def test_anos_e_times(br):
    assert br.anos() == [1971, 2023]
    assert br.times() == ["Botafogo", "Palmeiras", "Santos"]
    assert br.times(ano=1971) == ["Botafogo", "Palmeiras", "Santos"]


def test_partidas_filtra_por_ano_e_time(br):
    assert len(br.partidas()) == 11
    assert len(br.partidas(ano=2023)) == 5
    assert len(br.partidas(ano=2023, time="Santos")) == 3


def test_tabela_e_plots(br):
    tabela = br.tabela(1971)
    assert tabela.iloc[0]["time"] == "Palmeiras"

    assert isinstance(br.plot_tabela(1971), go.Figure)
    assert isinstance(br.plot_evolucao("Palmeiras", 1971), go.Figure)
    assert isinstance(br.plot_evolucao(["Palmeiras", "Santos"], 1971), go.Figure)
    assert isinstance(br.plot_historico("Palmeiras"), go.Figure)
    assert isinstance(br.plot_confronto("Palmeiras", "Santos"), go.Figure)
    assert isinstance(br.plot_gols_por_temporada(), go.Figure)
    assert isinstance(br.plot_mandante_visitante(), go.Figure)
    assert isinstance(br.plot_placares(), go.Figure)


def test_goleadas(br):
    assert br.goleadas(n=2).iloc[0]["placar"] == "5 x 0"


@pytest.mark.rede
def test_smoke_facade_com_dados_reais():
    """Fluxo completo contra a OBT real do GitHub (requer internet)."""
    br = Brasileirao()
    anos = br.anos()
    assert anos[0] == 1971
    tabela = br.tabela(2023)
    assert len(tabela) == 20
    assert tabela["jogos"].eq(38).all()
    fig = br.plot_tabela(2023)
    assert isinstance(fig, go.Figure)

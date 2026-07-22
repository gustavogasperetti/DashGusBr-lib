import pytest

from dashgusbr import analytics


# -- classificação -----------------------------------------------------------


def test_classificacao_1971_ordem_e_pontos_era_2_pontos(obt):
    tabela = analytics.classificacao(obt, 1971)
    assert list(tabela["time"]) == ["Palmeiras", "Botafogo", "Santos"]
    assert list(tabela["pontos"]) == [5, 4, 3]
    assert list(tabela["posicao"]) == [1, 2, 3]
    palmeiras = tabela.iloc[0]
    assert palmeiras["jogos"] == 4
    assert (palmeiras["vitorias"], palmeiras["empates"], palmeiras["derrotas"]) == (2, 1, 1)
    assert (palmeiras["gols_pro"], palmeiras["gols_contra"], palmeiras["saldo"]) == (7, 3, 4)
    # vitória valia 2 pontos em 1971: 5 pts em 4 jogos = 62.5%
    assert palmeiras["aproveitamento"] == 62.5


def test_classificacao_2023_exclui_mata_mata(obt):
    tabela = analytics.classificacao(obt, 2023)
    palmeiras = tabela[tabela["time"] == "Palmeiras"].iloc[0]
    # o 5x0 da final (mata-mata) não conta: 3 jogos e 7 pontos, não 4 e 10
    assert palmeiras["jogos"] == 3
    assert palmeiras["pontos"] == 7
    assert palmeiras["aproveitamento"] == 77.8


def test_classificacao_ano_inexistente(obt):
    with pytest.raises(ValueError, match="1999"):
        analytics.classificacao(obt, 1999)


# -- evolução e histórico -----------------------------------------------------


def test_evolucao_pontos_acumula_por_data(obt):
    evolucao = analytics.evolucao_pontos(obt, "Palmeiras", 1971)
    assert list(evolucao["jogo"]) == [1, 2, 3, 4]
    assert list(evolucao["pontos_acumulados"]) == [2, 4, 4, 5]
    assert list(evolucao["adversario"]) == ["Santos", "Botafogo", "Santos", "Botafogo"]


def test_evolucao_time_com_sugestao_de_grafia(obt):
    with pytest.raises(ValueError, match="Palmeiras"):
        analytics.evolucao_pontos(obt, "Palmeirras", 1971)


def test_historico_time_atravessa_eras(obt):
    historico = analytics.historico_time(obt, "Palmeiras")
    assert list(historico["ano_campeonato"]) == [1971, 2023]
    assert list(historico["aproveitamento"]) == [62.5, 77.8]
    assert list(historico["posicao"]) == [1, 1]


# -- confronto direto ---------------------------------------------------------


def test_confronto_inclui_todas_as_fases(obt):
    resumo = analytics.confronto(obt, "Palmeiras", "Santos")
    assert resumo["jogos"] == 4
    assert resumo["vitorias_a"] == 3
    assert resumo["vitorias_b"] == 1
    assert resumo["empates"] == 0
    assert (resumo["gols_a"], resumo["gols_b"]) == (9, 2)
    assert len(resumo["partidas"]) == 4


def test_confronto_e_simetrico(obt):
    ida = analytics.confronto(obt, "Palmeiras", "Santos")
    volta = analytics.confronto(obt, "Santos", "Palmeiras")
    assert ida["vitorias_a"] == volta["vitorias_b"]
    assert ida["gols_a"] == volta["gols_b"]


def test_confronto_exige_times_diferentes(obt):
    with pytest.raises(ValueError):
        analytics.confronto(obt, "Santos", "Santos")


# -- estatísticas do campeonato ------------------------------------------------


def test_estatisticas_temporada(obt):
    stats = analytics.estatisticas_temporada(obt).set_index("ano_campeonato")
    assert stats.loc[1971, "jogos"] == 6
    assert stats.loc[1971, "gols"] == 13
    assert stats.loc[1971, "media_gols"] == 2.17
    assert stats.loc[1971, "pct_vitorias_mandante"] == 50.0
    # mata-mata fora: 2023 tem 4 jogos de pontos corridos, não 5
    assert stats.loc[2023, "jogos"] == 4
    assert stats.loc[2023, "media_gols"] == 2.0


def test_distribuicao_placares_agrupa_no_ultimo_bin(obt):
    matriz = analytics.distribuicao_placares(obt, max_gols=3)
    assert int(matriz.values.sum()) == 11
    assert matriz.loc[3, 0] == 1  # o 5x0 clipado para 3+
    assert matriz.loc[1, 1] == 2


def test_maiores_goleadas(obt):
    goleadas = analytics.maiores_goleadas(obt, n=1)
    assert goleadas.iloc[0]["placar"] == "5 x 0"
    assert goleadas.iloc[0]["mandante"] == "Palmeiras"
    assert goleadas.iloc[0]["diferenca"] == 5

"""Testes das análises novas (casa/fora, sequências, contra, líderes, estados...).

Valores esperados calculados à mão sobre a mini-OBT do conftest:
1971 (vitória=2): P 2x0 S · S 1x1 B · B 0x3 P · S 2x1 P · B 1x0 S · P 1x1 B
2023 (vitória=3): P 1x0 S · S 2x2 B · B 1x2 P · P 0x0 B · [final] P 5x0 S
"""

import pandas as pd
import pytest

from dashgusbr import analytics

# -- resolução tolerante de nomes -------------------------------------------


def test_resolver_time_aceita_caixa_diferente(obt):
    tabela = analytics.historico_time(obt, "palmeiras")
    assert (tabela["time"] == "Palmeiras").all()


def test_resolver_time_erro_com_sugestao(obt):
    with pytest.raises(ValueError, match="Palmeiras"):
        analytics.evolucao_pontos(obt, "Palmeirras", 2023)


# -- casa × fora -------------------------------------------------------------


def test_casa_fora_palmeiras_historico(obt):
    resumo = analytics.casa_fora(obt, "Palmeiras")
    assert resumo.attrs["time"] == "Palmeiras"
    casa = resumo[resumo["local"] == "mandante"].iloc[0]
    fora = resumo[resumo["local"] == "visitante"].iloc[0]

    assert casa["jogos"] == 4 and casa["vitorias"] == 2 and casa["empates"] == 2
    assert casa["pontos"] == 7  # 2+1 (1971) + 3+1 (2023)
    assert casa["aproveitamento"] == 70.0  # 7 de 10 possíveis

    assert fora["jogos"] == 3 and fora["vitorias"] == 2 and fora["derrotas"] == 1
    assert fora["pontos"] == 5
    assert fora["aproveitamento"] == 71.4  # 5 de 7 possíveis


def test_casa_fora_recorte_por_ano(obt):
    resumo = analytics.casa_fora(obt, "Palmeiras", ano=2023)
    assert resumo["jogos"].sum() == 3  # mata-mata não conta


# -- sequências e forma -------------------------------------------------------


def test_sequencias_palmeiras(obt):
    seq = analytics.sequencias(obt, "Palmeiras").set_index("tipo")
    assert seq.loc["vitorias", "tamanho"] == 2
    assert seq.loc["invencibilidade", "tamanho"] == 5  # E V V E V (j6..j11)
    assert seq.loc["derrotas", "tamanho"] == 1
    assert seq.loc["sem_vencer", "tamanho"] == 2


def test_sequencias_sem_ocorrencia_zera(obt):
    # Botafogo 2023: E, D, E — nunca venceu no ano
    seq = analytics.sequencias(obt, "Botafogo", ano=2023).set_index("tipo")
    assert seq.loc["vitorias", "tamanho"] == 0
    assert pd.isna(seq.loc["vitorias", "inicio"])


def test_forma_recente(obt):
    forma = analytics.forma_recente(obt, "Palmeiras", n=3)
    assert list(forma["resultado"]) == ["V", "E", "V"]  # j9, j10, j11
    assert forma.attrs["aproveitamento"] == 77.8  # 7 de 9


# -- contra adversários -------------------------------------------------------


def test_desempenho_contra(obt):
    tabela = analytics.desempenho_contra(obt, "Palmeiras")
    assert tabela.attrs["time"] == "Palmeiras"
    assert list(tabela["adversario"]) == ["Santos", "Botafogo"]  # 80% > 70%
    santos = tabela.iloc[0]
    assert santos["jogos"] == 4 and santos["vitorias"] == 3
    assert santos["aproveitamento"] == 80.0


def test_desempenho_contra_min_jogos(obt):
    tabela = analytics.desempenho_contra(obt, "Palmeiras", min_jogos=5)
    assert tabela.empty


# -- corrida, líderes e ranking ----------------------------------------------


def test_corrida_titulo(obt):
    corrida = analytics.corrida_titulo(obt, 2023, n=2)
    assert set(corrida["time"]) == {"Palmeiras", "Botafogo"}


def test_lideres_temporada(obt):
    lideres = analytics.lideres_temporada(obt)
    assert list(lideres["ano_campeonato"]) == [1971, 2023]
    assert list(lideres["time"]) == ["Palmeiras", "Palmeiras"]


def test_contagem_lideres(obt):
    contagem = analytics.contagem_lideres(obt)
    assert contagem.iloc[0]["time"] == "Palmeiras"
    assert contagem.iloc[0]["lideracas"] == 2
    assert contagem.iloc[0]["anos"] == "1971, 2023"


def test_ranking_historico(obt):
    ranking = analytics.ranking_historico(obt)
    assert list(ranking["time"]) == ["Palmeiras", "Botafogo", "Santos"]
    palmeiras = ranking.iloc[0]
    assert palmeiras["posicao"] == 1
    assert palmeiras["temporadas"] == 2
    assert palmeiras["pontos"] == 12
    assert palmeiras["aproveitamento"] == 70.6  # 12 de 17 possíveis


def test_ranking_historico_min_temporadas(obt):
    ranking = analytics.ranking_historico(obt, min_temporadas=3)
    assert ranking.empty


# -- resumo do clube -----------------------------------------------------------


def test_resumo_time(obt):
    resumo = analytics.resumo_time(obt, "Palmeiras")
    assert resumo["time"] == "Palmeiras"
    assert resumo["temporadas"] == 2
    assert (resumo["primeira_temporada"], resumo["ultima_temporada"]) == (1971, 2023)
    assert resumo["jogos"] == 8  # inclui o mata-mata
    assert (resumo["vitorias"], resumo["empates"], resumo["derrotas"]) == (5, 2, 1)
    assert resumo["gols_pro"] == 15 and resumo["gols_contra"] == 4
    assert resumo["aproveitamento"] == 75.0  # 15 de 20 possíveis
    assert resumo["melhor_campanha"]["posicao"] == 1
    assert resumo["maior_vitoria"]["placar"] == "5 x 0"
    assert resumo["maior_vitoria"]["adversario"] == "Santos"
    assert resumo["maior_derrota"]["placar"] == "1 x 2"


# -- estados e recortes ---------------------------------------------------------


def test_estatisticas_estados(obt):
    stats = analytics.estatisticas_estados(obt).set_index("estado")
    assert stats.loc["SP", "jogos"] == 8  # j1, j2, j4, j6, j7, j8, j10, j11
    assert stats.loc["RJ", "jogos"] == 3
    assert stats.loc["SP", "times"] == 2  # Palmeiras e Santos mandantes
    assert stats.loc["RJ", "pct_vitorias_mandante"] == 33.3


def test_comparar_classicos(obt):
    grupos = analytics.comparar_classicos(obt).set_index("grupo")
    assert grupos.loc["Clássico estadual", "jogos"] == 4
    assert grupos.loc["Demais jogos", "jogos"] == 7


def test_comparar_fases(obt):
    grupos = analytics.comparar_fases(obt).set_index("grupo")
    assert grupos.loc["Mata-mata", "jogos"] == 1
    assert grupos.loc["Mata-mata", "media_gols"] == 5.0
    assert grupos.loc["Fase de pontos", "jogos"] == 10

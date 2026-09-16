"""Histórico dos clubes entre 1972 e 2000, quando não havia pontos corridos.

Nessas temporadas a campanha vem das fases de grupos e classificatória; a
posição fica vazia porque não existe classificação geral única.
"""

import json

import pandas as pd
import pytest

from dashgusbr import analytics, dashboard, schema, viz

# -- recorte das fases de liga -------------------------------------------------


def test_tipos_de_fase_de_liga_incluem_grupos_e_classificatoria():
    assert schema.TIPO_FASE_PONTOS_CORRIDOS in schema.TIPOS_FASE_LIGA
    assert {"Fase de Grupos", "Fase Classificatória"} <= set(schema.TIPOS_FASE_LIGA)


def test_fases_liga_descartam_mata_mata(obt_eras):
    liga = analytics._fases_liga(obt_eras)
    assert set(liga["tipo_fase"]) == {
        "Pontos Corridos",
        "Fase de Grupos",
        "Fase Classificatória",
    }
    assert not liga["is_mata_mata"].any()


def test_formato_da_temporada(obt_eras):
    por_ano = obt_eras.groupby("ano_campeonato")
    assert analytics._formato_da_temporada(por_ano.get_group(1971)) == "pontos corridos"
    assert analytics._formato_da_temporada(por_ano.get_group(1985)) == "grupos"
    assert analytics._formato_da_temporada(por_ano.get_group(2023)) == "pontos corridos"


def test_formato_grupos_mesmo_com_repescagem_em_pontos_corridos(obt_eras):
    """Como 1989 na base real: poucos jogos 'Pontos Corridos' num ano de grupos."""
    temporada = obt_eras[obt_eras["ano_campeonato"] == 1985].copy()
    temporada.loc[temporada["id_partida"] == 14, "tipo_fase"] = "Pontos Corridos"
    assert analytics._formato_da_temporada(temporada) == "grupos"


# -- histórico do clube --------------------------------------------------------


def test_historico_inclui_temporada_de_grupos(obt_eras):
    historico = analytics.historico_time(obt_eras, "Palmeiras")
    assert list(historico["ano_campeonato"]) == [1971, 1985, 2023]
    assert list(historico["formato"]) == ["pontos corridos", "grupos", "pontos corridos"]


def test_campanha_de_grupos_soma_grupos_e_classificatoria_sem_mata_mata(obt_eras):
    historico = analytics.historico_time(obt_eras, "Palmeiras").set_index("ano_campeonato")
    campanha = historico.loc[1985]
    # jogos 12, 13 e 15 (a semifinal 16 não conta): 2V 1E, 5 de 6 pontos possíveis
    assert campanha["jogos"] == 3
    assert (campanha["vitorias"], campanha["empates"], campanha["derrotas"]) == (2, 1, 0)
    assert campanha["pontos"] == 5
    assert campanha["aproveitamento"] == pytest.approx(83.3)
    assert (campanha["gols_pro"], campanha["gols_contra"]) == (5, 1)


def test_posicao_fica_vazia_em_temporada_de_grupos(obt_eras):
    historico = analytics.historico_time(obt_eras, "Palmeiras")
    assert str(historico["posicao"].dtype) == "Int64"
    posicoes = historico.set_index("ano_campeonato")["posicao"]
    assert pd.isna(posicoes.loc[1985])
    assert (posicoes.loc[1971], posicoes.loc[2023]) == (1, 1)


def test_aproveitamento_de_grupos_e_normalizado_pela_era(obt_eras):
    """Santos em 1985: 1V 1D em fases de liga = 2 de 4 pontos (vitória valia 2)."""
    historico = analytics.historico_time(obt_eras, "Santos").set_index("ano_campeonato")
    assert historico.loc[1985, "pontos"] == 2
    assert historico.loc[1985, "aproveitamento"] == pytest.approx(50.0)


def test_temporadas_de_pontos_corridos_nao_mudam(obt, obt_eras):
    """Adicionar 1985 não altera as linhas de 1971 e 2023."""
    antes = analytics.historico_time(obt, "Palmeiras").drop(columns=["formato"])
    depois = (
        analytics.historico_time(obt_eras, "Palmeiras")
        .query("ano_campeonato != 1985")
        .drop(columns=["formato"])
        .reset_index(drop=True)
    )
    pd.testing.assert_frame_equal(antes, depois, check_dtype=False)


def test_clube_so_com_temporada_de_grupos(obt_eras):
    historico = analytics.historico_time(obt_eras, "Grêmio")
    assert list(historico["ano_campeonato"]) == [1985]
    assert historico["posicao"].isna().all()
    assert historico.loc[0, "aproveitamento"] == 0.0


def test_classificacao_continua_restrita_a_pontos_corridos(obt_eras):
    assert analytics.classificacao(obt_eras, 1985).empty
    with pytest.raises(ValueError, match="pontos corridos"):
        analytics.ultima_temporada(obt_eras, "Grêmio")


# -- resumo do clube -----------------------------------------------------------


def test_resumo_conta_temporada_de_grupos_e_ignora_na_melhor_pior_campanha(obt_eras):
    resumo = analytics.resumo_time(obt_eras, "Palmeiras")
    assert resumo["temporadas"] == 3
    assert resumo["melhor_campanha"]["ano"] in (1971, 2023)
    assert resumo["pior_campanha"]["ano"] in (1971, 2023)


def test_resumo_sem_pontos_corridos_nao_tem_melhor_nem_pior_campanha(obt_eras):
    resumo = analytics.resumo_time(obt_eras, "Grêmio")
    assert resumo["temporadas"] == 1
    assert resumo["melhor_campanha"] is None
    assert resumo["pior_campanha"] is None


# -- visualização e dashboard --------------------------------------------------


def test_viz_historico_marca_posicao_ausente_no_hover(obt_eras):
    fig = viz.historico(analytics.historico_time(obt_eras, "Palmeiras"))
    posicoes = [linha[0] for linha in fig.data[0].customdata]
    assert posicoes == ["1º", "—", "1º"]
    assert "º" not in fig.data[0].hovertemplate  # o sufixo já está no dado
    json.loads(fig.to_json())  # serializa sem tropeçar em <NA>


def test_viz_posicao_deixa_buraco_na_temporada_de_grupos(obt_eras):
    fig = viz.historico(analytics.historico_time(obt_eras, "Palmeiras"), metrica="posicao")
    y = list(fig.data[0].y)
    assert y[0] == 1 and y[2] == 1
    assert pd.isna(y[1])
    json.loads(fig.to_json())


def test_indicadores_comparam_com_temporada_de_grupos_exceto_posicao(obt_eras):
    fig = dashboard.dashboard_time(obt_eras, "Palmeiras", 2023, paineis=["indicadores"])
    kpis = {t.title.text: t for t in fig.data if t.type == "indicator"}
    assert kpis["Posição"].delta.reference is None  # 1985 não tem posição
    assert kpis["Pontos"].delta.reference == 5
    assert kpis["Aproveitamento"].delta.reference == pytest.approx(83.3)


def test_dashboard_historico_com_temporada_de_grupos(obt_eras):
    fig = dashboard.dashboard_time(
        obt_eras, ["Palmeiras", "Santos"], 2023, paineis=["historico", "posicao"]
    )
    assert {t.name for t in fig.data} == {"Palmeiras", "Santos"}
    json.loads(fig.to_json())

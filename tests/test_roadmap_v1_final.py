"""Testes dos itens finais do roadmap v1: tema escuro, contraste, novas
análises (confronto no tempo, viagem, décadas, saldos), validação de
consistência, mapa por UF, CLI e resolução de nomes em ``partidas``."""

import json

import plotly.io as pio
import pytest

from dashgusbr import Brasileirao, analytics, data, schema, viz
from dashgusbr.__main__ import main as cli_main
from dashgusbr._cores_times import cor_time
from dashgusbr._theme import TEMA_ESCURO, cor_texto_para


def _feature(sigla, coords):
    return {
        "type": "Feature",
        "properties": {"sigla": sigla},
        "geometry": {"type": "Polygon", "coordinates": [coords]},
    }


GEOJSON_FALSO = {
    "type": "FeatureCollection",
    "features": [
        _feature("SP", [[0, 0], [1, 0], [1, 1], [0, 0]]),
        _feature("RJ", [[1, 1], [2, 1], [2, 2], [1, 1]]),
    ],
}


# -- tema escuro e contraste --------------------------------------------------


def test_tema_escuro_registrado():
    assert TEMA_ESCURO in pio.templates
    assert pio.templates[TEMA_ESCURO].layout.paper_bgcolor == "#16181d"


def test_tema_escuro_aplicavel_em_qualquer_plot(obt):
    fig = viz.classificacao(analytics.classificacao(obt, 2023), template=TEMA_ESCURO)
    assert fig.layout.template.layout.paper_bgcolor == "#16181d"


def test_cor_texto_para_luminancia():
    assert cor_texto_para("#1b1b1b") == "#f2f1ec"  # barra preta -> texto claro
    assert cor_texto_para("#eda100") == "#0b0b0b"  # amarelo -> texto escuro
    assert cor_texto_para("#fff") == "#0b0b0b"  # hex curto aceito


def test_rotulo_interno_recebe_cor_por_luminancia(obt):
    resumo = analytics.confronto(obt, "Palmeiras", "Santos")
    fig = viz.confronto(resumo, usar_cores_times=True)
    cores_inside = fig.data[0].insidetextfont.color
    assert len(cores_inside) == 3
    assert all(c in ("#0b0b0b", "#f2f1ec") for c in cores_inside)


# -- mostrar_valores / mostrar_legenda ---------------------------------------


def test_mostrar_valores_desliga_rotulos(obt):
    tabela = analytics.classificacao(obt, 2023)
    assert viz.classificacao(tabela).data[0].text is not None
    assert viz.classificacao(tabela, mostrar_valores=False).data[0].text is None


def test_mostrar_legenda_forca_estado(obt):
    evolucoes = analytics.corrida_titulo(obt, 2023, n=2)
    assert viz.evolucao(evolucoes).layout.showlegend is True
    assert viz.evolucao(evolucoes, mostrar_legenda=False).layout.showlegend is False
    resumo = analytics.casa_fora(obt, "Palmeiras")
    assert viz.casa_fora(resumo, mostrar_legenda=False).layout.showlegend is False


# -- novas análises -----------------------------------------------------------


def test_evolucao_confronto_saldo_acumulado(obt):
    linha = analytics.evolucao_confronto(obt, "palmeiras", "Santos")
    assert linha.attrs["time_a"] == "Palmeiras"
    # jogos Palmeiras x Santos (com placar): 1971 V, 1971 D, 2023 V, 2023 V (final)
    assert list(linha["saldo_jogo"]) == [1, -1, 1, 1]
    assert list(linha["saldo_acumulado"]) == [1, 0, 1, 2]
    fig = viz.evolucao_confronto(linha, usar_cores_times=True)
    assert fig.data[0].line.color == cor_time("Palmeiras")


def test_fator_viagem_grupos(obt):
    stats = analytics.fator_viagem(obt)
    assert set(stats["grupo"]) == {
        "Visitante do mesmo estado",
        "Visitante de outro estado",
    }
    assert int(stats["jogos"].sum()) == 11  # todos os jogos têm UF na fixture


def test_media_gols_por_decada(obt):
    stats = analytics.media_gols_por_decada(obt)
    decada_70 = stats[stats["decada"] == "1970"].iloc[0]
    assert decada_70["era_pontuacao"] == "2 pontos por vitória"
    assert decada_70["jogos"] == 6
    decada_20 = stats[stats["decada"] == "2020"].iloc[0]
    assert decada_20["era_pontuacao"] == "3 pontos por vitória"


def test_distribuicao_saldos(obt):
    contagem = analytics.distribuicao_saldos(obt, max_saldo=3)
    assert list(contagem["saldo"]) == [-3, -2, -1, 0, 1, 2, 3]
    assert int(contagem["jogos"].sum()) == 11
    # goleada 5x0 agregada na cauda +3
    assert contagem.loc[contagem["saldo"] == 3, "jogos"].iloc[0] >= 1
    fig = viz.distribuicao_saldos(contagem)
    assert fig.data[0].y.sum() == 11


def test_distribuicao_saldos_ano_invalido(obt):
    with pytest.raises(ValueError, match="1999"):
        analytics.distribuicao_saldos(obt, ano=1999)


# -- validação de consistência -------------------------------------------------


def test_relatorio_consistencia_base_limpa(obt):
    relatorio = schema.relatorio_consistencia(obt)
    assert set(relatorio.columns) == {"checagem", "problemas", "exemplos"}
    assert int(relatorio["problemas"].sum()) == 0


def test_relatorio_consistencia_detecta_problemas(obt):
    sujo = obt.copy()
    sujo.loc[0, "resultado_mandante"] = "D"  # incoerente: mandante venceu 2x0
    sujo.loc[1, "total_gols"] = 99
    relatorio = schema.relatorio_consistencia(sujo).set_index("checagem")
    assert relatorio.loc["resultado do mandante incoerente com o placar", "problemas"] >= 1
    assert relatorio.loc["total_gols diferente da soma do placar", "problemas"] == 1
    assert "1" in relatorio.loc["resultado do mandante incoerente com o placar", "exemplos"]


def test_validar_na_fachada(caminho_csv):
    br = Brasileirao(fonte=caminho_csv)
    assert int(br.validar()["problemas"].sum()) == 0


# -- mapa coroplético ----------------------------------------------------------


def test_mapa_estados_com_geojson(obt):
    stats = analytics.estatisticas_estados(obt)
    fig = viz.mapa_estados(stats, GEOJSON_FALSO)
    assert fig.data[0].type == "choropleth"
    assert fig.data[0].featureidkey == "properties.sigla"
    assert set(fig.data[0].locations) == {"SP", "RJ"}


def test_mapa_estados_metrica_invalida(obt):
    stats = analytics.estatisticas_estados(obt)
    with pytest.raises(ValueError, match="nao_existe"):
        viz.mapa_estados(stats, GEOJSON_FALSO, metrica="nao_existe")


def test_carregar_geojson_estados_mockado(monkeypatch, tmp_path):
    monkeypatch.setattr(data, "DIR_CACHE", tmp_path)
    monkeypatch.setattr(
        data, "_baixar", lambda url: json.dumps(GEOJSON_FALSO).encode("utf-8")
    )
    data._CACHE_GEOJSON.clear()
    geojson = data.carregar_geojson_estados(url="https://exemplo/uf.geojson")
    assert len(geojson["features"]) == 2
    assert list(tmp_path.glob("*.json"))  # cacheado em disco
    # segunda chamada vem da memória, mesmo sem rede
    monkeypatch.setattr(data, "_baixar", lambda url: (_ for _ in ()).throw(OSError))
    assert data.carregar_geojson_estados(url="https://exemplo/uf.geojson") == geojson
    data._CACHE_GEOJSON.clear()


def test_carregar_geojson_conteudo_invalido(monkeypatch, tmp_path):
    monkeypatch.setattr(data, "DIR_CACHE", tmp_path)
    monkeypatch.setattr(data, "_baixar", lambda url: b'{"sem": "features"}')
    data._CACHE_GEOJSON.clear()
    with pytest.raises(ValueError, match="GeoJSON"):
        data.carregar_geojson_estados(url="https://exemplo/ruim.json", cache_disco=False)


# -- fachada e CLI --------------------------------------------------------------


def test_partidas_resolve_nome_tolerante(caminho_csv):
    br = Brasileirao(fonte=caminho_csv)
    assert len(br.partidas(time="PALMEIRAS")) == len(br.partidas(time="Palmeiras")) > 0
    with pytest.raises(ValueError, match="não encontrado"):
        br.partidas(time="Time Fantasma")


def test_fachada_novos_metodos(caminho_csv):
    br = Brasileirao(fonte=caminho_csv)
    assert br.plot_confronto_evolucao("Palmeiras", "Santos").data
    assert br.plot_saldos(ano=2023).data
    assert not br.gols_por_decada().empty
    assert not br.viagem().empty
    fig = br.plot_mapa_estados(geojson=GEOJSON_FALSO)
    assert fig.data[0].type == "choropleth"


def test_cli_tabela_e_validar(caminho_csv, capsys):
    assert cli_main(["--fonte", caminho_csv, "tabela", "2023"]) == 0
    saida = capsys.readouterr().out
    assert "Palmeiras" in saida
    assert cli_main(["--fonte", caminho_csv, "validar"]) == 0
    assert "checagem" in capsys.readouterr().out


def test_cli_salva_html(caminho_csv, tmp_path, capsys):
    destino = tmp_path / "tabela.html"
    assert cli_main(["--fonte", caminho_csv, "tabela", "2023", "--html", str(destino)]) == 0
    assert destino.exists()


# -- cores da cauda longa --------------------------------------------------------


def test_cores_cauda_longa():
    assert cor_time("Treze") == "#1b1b1b"
    assert cor_time("Ferroviária") == "#7a1f2b"
    assert cor_time("XV de Piracicaba") == cor_time("xv de piracicaba")
    assert cor_time("Volta Redonda") is not None

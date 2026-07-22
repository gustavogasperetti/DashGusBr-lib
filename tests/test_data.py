import pytest

from dashgusbr import config, data


def test_sheets_export_url_converte_link_de_edicao():
    url = "https://docs.google.com/spreadsheets/d/ABC-123_xyz/edit?usp=sharing"
    assert (
        config.sheets_export_url(url)
        == "https://docs.google.com/spreadsheets/d/ABC-123_xyz/export?format=csv"
    )


def test_sheets_export_url_com_gid():
    url = "https://docs.google.com/spreadsheets/d/ABC/edit"
    assert config.sheets_export_url(url, gid=42).endswith("format=csv&gid=42")


def test_sheets_export_url_passa_export_adiante():
    url = "https://docs.google.com/spreadsheets/d/ABC/export?format=csv"
    assert config.sheets_export_url(url) == url


def test_sheets_export_url_rejeita_url_invalida():
    with pytest.raises(ValueError):
        config.sheets_export_url("https://example.com/planilha.csv")


def test_carregar_de_caminho_local(caminho_csv):
    df = data.carregar_dados(caminho_csv, cache=False)
    assert len(df) == 11
    assert "mandante" in df.columns


def test_cache_devolve_copia_independente(caminho_csv):
    data.limpar_cache()
    primeiro = data.carregar_dados(caminho_csv)
    primeiro.loc[:, "mandante"] = "ALTERADO"
    segundo = data.carregar_dados(caminho_csv)
    assert (segundo["mandante"] != "ALTERADO").all()
    data.limpar_cache()


def test_todas_as_fontes_indisponiveis(tmp_path):
    inexistente = str(tmp_path / "nao_existe.csv")
    with pytest.raises(data.DadosIndisponiveisError, match="nao_existe"):
        data.carregar_dados(inexistente, cache=False)


@pytest.mark.rede
def test_smoke_fonte_real_github():
    """Baixa a OBT real do GitHub e valida o shape básico (requer internet)."""
    df = data.carregar_dados(fonte="github", cache=False)
    assert len(df) > 20_000
    assert set(["mandante", "visitante", "pontos_mandante"]) <= set(df.columns)

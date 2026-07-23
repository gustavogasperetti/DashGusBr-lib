"""Exportação de figuras e cache em disco da carga de dados."""

import importlib.util

import plotly.graph_objects as go
import pytest

from dashgusbr import data, export

TEM_KALEIDO = importlib.util.find_spec("kaleido") is not None


@pytest.fixture()
def figura() -> go.Figure:
    return go.Figure(go.Bar(x=["a", "b"], y=[1, 2]))


# -- exportação ---------------------------------------------------------------


def test_salvar_html(figura, tmp_path):
    destino = export.salvar_html(figura, tmp_path / "grafico.html")
    assert destino.exists()
    assert destino.stat().st_size > 0


def test_salvar_html_completa_extensao(figura, tmp_path):
    destino = export.salvar_html(figura, tmp_path / "grafico")
    assert destino.suffix == ".html"


@pytest.mark.skipif(TEM_KALEIDO, reason="kaleido instalado: o erro não se aplica")
def test_salvar_imagem_sem_kaleido_da_erro_amigavel(figura, tmp_path):
    with pytest.raises(ImportError, match=r"dashgusbr\[imagem\]"):
        export.salvar_imagem(figura, tmp_path / "grafico.png")


@pytest.mark.skipif(not TEM_KALEIDO, reason="requer kaleido")
def test_salvar_imagem_com_kaleido(figura, tmp_path):
    destino = export.salvar_imagem(figura, tmp_path / "grafico.png")
    assert destino.exists()


# -- cache em disco -------------------------------------------------------------


@pytest.fixture()
def fonte_falsa(monkeypatch, tmp_path, csv_texto):
    """Redireciona o cache em disco para tmp_path e simula o download."""
    monkeypatch.setattr(data, "DIR_CACHE", tmp_path / "cache")
    chamadas = {"n": 0}

    def baixar_falso(url, timeout=30, tentativas=3):
        chamadas["n"] += 1
        return csv_texto.encode("utf-8")

    monkeypatch.setattr(data, "_baixar", baixar_falso)
    data.limpar_cache()
    yield chamadas
    data.limpar_cache()


URL = "https://example.com/obt.csv"


def test_cache_disco_evita_segundo_download(fonte_falsa):
    df1 = data.carregar_dados(fonte="github", github_url=URL, cache=False)
    df2 = data.carregar_dados(fonte="github", github_url=URL, cache=False)
    assert fonte_falsa["n"] == 1  # segunda carga veio do disco
    assert len(df1) == len(df2) == 11


def test_forcar_download_ignora_cache_disco(fonte_falsa):
    data.carregar_dados(fonte="github", github_url=URL, cache=False)
    data.carregar_dados(
        fonte="github", github_url=URL, cache=False, forcar_download=True
    )
    assert fonte_falsa["n"] == 2


def test_cache_vencido_baixa_de_novo(fonte_falsa):
    data.carregar_dados(fonte="github", github_url=URL, cache=False)
    data.carregar_dados(
        fonte="github", github_url=URL, cache=False, validade_horas=0
    )
    assert fonte_falsa["n"] == 2


def test_rede_fora_usa_cache_desatualizado(fonte_falsa, monkeypatch):
    data.carregar_dados(fonte="github", github_url=URL, cache=False)

    def baixar_quebrado(url, timeout=30, tentativas=3):
        raise OSError("rede fora")

    monkeypatch.setattr(data, "_baixar", baixar_quebrado)
    df = data.carregar_dados(
        fonte="github", github_url=URL, cache=False, validade_horas=0
    )
    assert len(df) == 11  # melhor dado velho que erro


def test_cache_disco_desligado_sempre_baixa(fonte_falsa):
    data.carregar_dados(
        fonte="github", github_url=URL, cache=False, cache_disco=False
    )
    data.carregar_dados(
        fonte="github", github_url=URL, cache=False, cache_disco=False
    )
    assert fonte_falsa["n"] == 2


def test_limpar_cache_disco(fonte_falsa):
    data.carregar_dados(fonte="github", github_url=URL, cache=False)
    assert any(data.DIR_CACHE.glob("*.csv"))
    data.limpar_cache(disco=True)
    assert not any(data.DIR_CACHE.glob("*.csv"))

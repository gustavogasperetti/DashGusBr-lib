"""Carga da OBT do Brasileirão: GitHub (primário) com fallback para Google Sheets.

Camada pura de acesso a dados: baixa o CSV, normaliza para o schema canônico
(:mod:`dashgusbr.schema`) e valida. Dois níveis de cache evitam downloads
repetidos: em memória (por sessão) e em disco (entre sessões, com validade).

O progresso da carga é reportado via ``logging`` (logger ``dashgusbr``)::

    import logging
    logging.basicConfig(level=logging.INFO)  # mostra download/cache/fallback
"""

from __future__ import annotations

import hashlib
import io
import logging
import time as _time
import urllib.request
from pathlib import Path
from typing import Optional

import pandas as pd

from . import config, schema

logger = logging.getLogger("dashgusbr")

_CACHE: "dict[str, pd.DataFrame]" = {}

FONTES = ("auto", "github", "sheets")

# Cache em disco: ~/.dashgusbr/cache/<sha1-da-url>.csv
DIR_CACHE = Path.home() / ".dashgusbr" / "cache"


class DadosIndisponiveisError(RuntimeError):
    """Levantado quando nenhuma fonte de dados pôde ser carregada."""


def limpar_cache(disco: bool = False) -> None:
    """Descarta os DataFrames em memória; ``disco=True`` também apaga os CSVs locais."""
    _CACHE.clear()
    if disco and DIR_CACHE.exists():
        for arquivo in DIR_CACHE.glob("*.csv"):
            arquivo.unlink(missing_ok=True)


def _arquivo_cache(url: str) -> Path:
    chave = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return DIR_CACHE / f"{chave}.csv"


def _baixar(url: str, timeout: float = 30, tentativas: int = 3) -> bytes:
    """Baixa a URL com timeout e novas tentativas (backoff simples)."""
    ultimo_erro: Optional[Exception] = None
    for tentativa in range(1, tentativas + 1):
        try:
            logger.info("Baixando %s (tentativa %d/%d)...", url, tentativa, tentativas)
            with urllib.request.urlopen(url, timeout=timeout) as resposta:
                dados = resposta.read()
            logger.info("Download concluído: %.1f KB.", len(dados) / 1024)
            return dados
        except Exception as exc:  # rede, HTTP, timeout
            ultimo_erro = exc
            if tentativa < tentativas:
                espera = 2 ** (tentativa - 1)
                logger.warning(
                    "Falha no download (%s); nova tentativa em %ds.", exc, espera
                )
                _time.sleep(espera)
    raise ultimo_erro  # type: ignore[misc]


def _parse_csv(conteudo: bytes) -> pd.DataFrame:
    # utf-8-sig absorve o BOM que o pipeline grava no início do arquivo
    bruto = pd.read_csv(io.BytesIO(conteudo), encoding="utf-8-sig")
    return schema.validar(schema.normalizar(bruto))


def _ler_url(
    url: str,
    cache_disco: bool,
    validade_horas: float,
    forcar_download: bool,
) -> pd.DataFrame:
    """Lê um CSV remoto, passando pelo cache em disco quando habilitado."""
    arquivo = _arquivo_cache(url)

    if cache_disco and not forcar_download and arquivo.exists():
        idade_horas = (_time.time() - arquivo.stat().st_mtime) / 3600
        # < estrito: validade_horas=0 significa "nunca aceitar cache do disco"
        if idade_horas < validade_horas:
            logger.info(
                "Usando cache em disco (%.1fh de idade): %s", idade_horas, arquivo
            )
            return _parse_csv(arquivo.read_bytes())

    try:
        conteudo = _baixar(url)
    except Exception:
        # rede caiu, mas há uma cópia velha em disco: melhor dado velho que erro
        if cache_disco and arquivo.exists():
            logger.warning(
                "Download falhou; usando cache em disco DESATUALIZADO: %s", arquivo
            )
            return _parse_csv(arquivo.read_bytes())
        raise

    df = _parse_csv(conteudo)  # valida ANTES de gravar: nunca cachear lixo
    if cache_disco:
        DIR_CACHE.mkdir(parents=True, exist_ok=True)
        arquivo.write_bytes(conteudo)
        logger.info("Cache em disco atualizado: %s", arquivo)
    return df


def _ler_caminho(caminho: str) -> pd.DataFrame:
    """Lê um CSV local (ou URL direta via pandas) sem cache em disco."""
    bruto = pd.read_csv(caminho, encoding="utf-8-sig")
    return schema.validar(schema.normalizar(bruto))


def carregar_dados(
    fonte: str = "auto",
    github_url: Optional[str] = None,
    sheets_url: Optional[str] = None,
    cache: bool = True,
    forcar_download: bool = False,
    cache_disco: bool = True,
    validade_horas: float = 24,
) -> pd.DataFrame:
    """Carrega a OBT completa como DataFrame no schema canônico.

    Parameters
    ----------
    fonte:
        ``"auto"`` (padrão) tenta o CSV do GitHub e, em caso de falha, o
        Google Sheets. ``"github"`` e ``"sheets"`` forçam uma fonte única.
        Qualquer outro valor é tratado como caminho local ou URL direta de
        um CSV no mesmo schema.
    github_url, sheets_url:
        Sobrescrevem as URLs padrão de :mod:`dashgusbr.config`.
    cache:
        Reutiliza o resultado de cargas anteriores da mesma fonte na sessão.
    forcar_download:
        Ignora (e substitui) os caches desta fonte.
    cache_disco:
        Guarda o CSV baixado em ``~/.dashgusbr/cache`` e o reutiliza entre
        sessões enquanto for válido (só para fontes remotas github/sheets).
    validade_horas:
        Idade máxima do cache em disco antes de baixar de novo (padrão 24h).
    """
    github_url = github_url or config.GITHUB_CSV_URL
    sheets_url = sheets_url or config.SHEETS_URL

    if fonte == "github":
        candidatas = [("github", github_url, True)]
    elif fonte == "sheets":
        candidatas = [("sheets", config.sheets_export_url(sheets_url), True)]
    elif fonte == "auto":
        candidatas = [
            ("github", github_url, True),
            ("sheets", config.sheets_export_url(sheets_url), True),
        ]
    else:
        # caminho local ou URL direta de CSV: sem cache em disco
        candidatas = [("caminho", fonte, False)]

    erros = []
    for nome, url, remota in candidatas:
        if cache and not forcar_download and url in _CACHE:
            logger.info("Usando cache em memória da fonte %s.", nome)
            return _CACHE[url].copy()
        try:
            if remota:
                df = _ler_url(url, cache_disco, validade_horas, forcar_download)
            else:
                df = _ler_caminho(url)
        except schema.SchemaInvalidoError:
            raise
        except Exception as exc:  # rede, HTTP, parsing
            logger.warning("Fonte %s indisponível: %s", nome, exc)
            erros.append(f"{nome} ({url}): {exc}")
            continue
        if cache:
            _CACHE[url] = df
        return df.copy()

    detalhes = "\n  - ".join(erros)
    raise DadosIndisponiveisError(
        f"Nenhuma fonte de dados pôde ser carregada:\n  - {detalhes}"
    )

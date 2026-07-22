"""Carga da OBT do Brasileirão: GitHub (primário) com fallback para Google Sheets.

Camada pura de acesso a dados: baixa o CSV, normaliza para o schema canônico
(:mod:`dashgusbr.schema`) e valida. Um cache em módulo evita downloads
repetidos na mesma sessão.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from . import config, schema

_CACHE: "dict[str, pd.DataFrame]" = {}

FONTES = ("auto", "github", "sheets")


class DadosIndisponiveisError(RuntimeError):
    """Levantado quando nenhuma fonte de dados pôde ser carregada."""


def limpar_cache() -> None:
    """Descarta todos os DataFrames em cache; a próxima carga baixa de novo."""
    _CACHE.clear()


def _ler_csv(url: str) -> pd.DataFrame:
    # utf-8-sig absorve o BOM que o pipeline grava no início do arquivo
    bruto = pd.read_csv(url, encoding="utf-8-sig")
    return schema.validar(schema.normalizar(bruto))


def carregar_dados(
    fonte: str = "auto",
    github_url: Optional[str] = None,
    sheets_url: Optional[str] = None,
    cache: bool = True,
    forcar_download: bool = False,
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
        Ignora (e substitui) o cache desta fonte.
    """
    github_url = github_url or config.GITHUB_CSV_URL
    sheets_url = sheets_url or config.SHEETS_URL

    if fonte == "github":
        candidatas = [("github", github_url)]
    elif fonte == "sheets":
        candidatas = [("sheets", config.sheets_export_url(sheets_url))]
    elif fonte == "auto":
        candidatas = [
            ("github", github_url),
            ("sheets", config.sheets_export_url(sheets_url)),
        ]
    else:
        # caminho local ou URL direta de CSV
        candidatas = [("caminho", fonte)]

    erros = []
    for nome, url in candidatas:
        if cache and not forcar_download and url in _CACHE:
            return _CACHE[url].copy()
        try:
            df = _ler_csv(url)
        except schema.SchemaInvalidoError:
            raise
        except Exception as exc:  # rede, HTTP, parsing
            erros.append(f"{nome} ({url}): {exc}")
            continue
        if cache:
            _CACHE[url] = df
        return df.copy()

    detalhes = "\n  - ".join(erros)
    raise DadosIndisponiveisError(
        f"Nenhuma fonte de dados pôde ser carregada:\n  - {detalhes}"
    )

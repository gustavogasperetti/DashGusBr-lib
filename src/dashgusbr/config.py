"""Configuração das fontes de dados da dashgusbr.

A biblioteca consome a OBT (One Big Table) gerada pelo pipeline ETL do
projeto Infra-Brasileirao. A fonte primária é o CSV publicado no GitHub
(camada gold); o Google Sheets é o fallback.
"""

from __future__ import annotations

import re

GITHUB_CSV_URL = (
    "https://raw.githubusercontent.com/gustavogasperetti/Infra-Brasileirao/"
    "refs/heads/main/data/gold/brasileirao_obt.csv"
)

SHEETS_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1s_Pk7wYAZ4DjVRhamLJVZI26sIMdNvF-eFMkMGxWeIA/edit"
)

_SHEETS_ID_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9_-]+)")


def sheets_export_url(url: str, gid: "int | None" = None) -> str:
    """Converte um link de compartilhamento do Google Sheets em URL de export CSV.

    Aceita tanto o link de edição (``.../d/<id>/edit...``) quanto uma URL de
    export já pronta (retornada como está). ``gid`` seleciona a aba; sem ele,
    o Google exporta a primeira aba da planilha.
    """
    if "/export" in url:
        return url
    match = _SHEETS_ID_RE.search(url)
    if not match:
        raise ValueError(f"URL de Google Sheets não reconhecida: {url!r}")
    base = f"https://docs.google.com/spreadsheets/d/{match.group(1)}/export?format=csv"
    if gid is not None:
        base += f"&gid={gid}"
    return base

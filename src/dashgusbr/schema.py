"""Schema canônico da OBT do Brasileirão.

O ETL publica a tabela com alguns nomes capitalizados (``Data``, ``Mandante``,
``Visitante``, ``Fase``). Internamente a dashgusbr trabalha sempre com o
schema canônico em snake_case minúsculo definido aqui; :func:`normalizar`
faz a conversão na carga e :func:`validar` garante que nada essencial falta.
"""

from __future__ import annotations

import pandas as pd

# Renomeações aplicadas na carga (nome na fonte -> nome canônico)
RENOMEACOES = {
    "Data": "data",
    "Mandante": "mandante",
    "Visitante": "visitante",
    "Fase": "fase",
}

# Colunas do schema canônico, na ordem publicada pela OBT
COLUNAS = [
    "id_partida",
    "ano_campeonato",
    "data",
    "mandante",
    "visitante",
    "estado_mandante",
    "estado_visitante",
    "gols_mandante",
    "gols_visitante",
    "resultado_mandante",
    "resultado_visitante",
    "placar_status",
    "fase",
    "tipo_fase",
    "is_mata_mata",
    "is_classico_estadual",
    "total_gols",
    "saldo_gols_mandante",
    "saldo_gols_visitante",
    "pontos_mandante",
    "pontos_visitante",
]

# Colunas sem as quais as análises do MVP não funcionam
COLUNAS_OBRIGATORIAS = [
    "ano_campeonato",
    "data",
    "mandante",
    "visitante",
    "gols_mandante",
    "gols_visitante",
    "resultado_mandante",
    "resultado_visitante",
    "tipo_fase",
    "pontos_mandante",
    "pontos_visitante",
]

_COLUNAS_INTEIRAS = [
    "id_partida",
    "ano_campeonato",
    "gols_mandante",
    "gols_visitante",
    "total_gols",
    "saldo_gols_mandante",
    "saldo_gols_visitante",
    "pontos_mandante",
    "pontos_visitante",
]

_COLUNAS_BOOLEANAS = ["is_mata_mata", "is_classico_estadual"]

# Valor usado pelo ETL na coluna tipo_fase para jogos de pontos corridos
TIPO_FASE_PONTOS_CORRIDOS = "Pontos Corridos"


class SchemaInvalidoError(ValueError):
    """Levantado quando a fonte de dados não contém o schema canônico da OBT."""


def normalizar(df: pd.DataFrame) -> pd.DataFrame:
    """Converte um DataFrame recém-carregado para o schema canônico.

    - remove BOM/espaços dos nomes de coluna e aplica :data:`RENOMEACOES`;
    - ``data`` vira ``datetime64``;
    - contagens (gols, pontos, saldos) viram inteiros anuláveis (``Int64``),
      já que a fonte publica gols como float (``1.0``);
    - flags ``is_*`` viram ``bool`` (a fonte publica como texto ``True``/``False``).
    """
    df = df.copy()
    df.columns = [str(c).replace("﻿", "").strip() for c in df.columns]
    df = df.rename(columns=RENOMEACOES)

    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")

    for col in _COLUNAS_INTEIRAS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round().astype("Int64")

    for col in _COLUNAS_BOOLEANAS:
        if col in df.columns:
            if df[col].dtype != bool:
                df[col] = (
                    df[col].astype(str).str.strip().str.lower().eq("true")
                )

    return df


def validar(df: pd.DataFrame) -> pd.DataFrame:
    """Valida a presença das colunas obrigatórias; retorna o próprio DataFrame.

    Levanta :class:`SchemaInvalidoError` com a lista do que falta, para que o
    erro aponte direto para a divergência entre a fonte e o schema esperado.
    """
    faltantes = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if faltantes:
        raise SchemaInvalidoError(
            "A fonte de dados não segue o schema canônico da OBT. "
            f"Colunas faltantes: {faltantes}. Colunas presentes: {list(df.columns)}"
        )
    return df


def relatorio_consistencia(df: pd.DataFrame) -> pd.DataFrame:
    """Checagens de consistência dos DADOS (além da presença de colunas).

    Não levanta erro: devolve um relatório com uma linha por checagem —
    ``checagem``, ``problemas`` (nº de partidas afetadas) e ``exemplos``
    (até 5 ``id_partida``) — para inspecionar a qualidade da OBT ou de um
    CSV próprio antes de confiar nas análises.

    Checagens: gols negativos, resultado incoerente com o placar, resultados
    dos dois lados não espelhados, pontos incoerentes com o resultado,
    ``total_gols`` divergente da soma, datas ausentes/implausíveis (fora de
    1971..ano atual + 1) e ``id_partida`` duplicado.
    """
    jogos = df.dropna(subset=["gols_mandante", "gols_visitante"])
    gm, gv = jogos["gols_mandante"], jogos["gols_visitante"]

    resultado_esperado = (
        pd.Series("E", index=jogos.index)
        .mask(gm > gv, "V")
        .mask(gm < gv, "D")
    )
    espelho = {"V": "D", "E": "E", "D": "V"}

    pontos_ok = pd.Series(True, index=jogos.index)
    if "pontos_mandante" in jogos.columns:
        pm = jogos["pontos_mandante"]
        pontos_ok &= (
            ((jogos["resultado_mandante"] == "V") & pm.isin([2, 3]))
            | ((jogos["resultado_mandante"] == "E") & (pm == 1))
            | ((jogos["resultado_mandante"] == "D") & (pm == 0))
        )

    limite_ano = pd.Timestamp.now().year + 1
    datas_ruins = df["data"].isna() | (df["data"].dt.year < 1971) | (
        df["data"].dt.year > limite_ano
    )

    checagens = [
        ("gols negativos", jogos[(gm < 0) | (gv < 0)]),
        (
            "resultado do mandante incoerente com o placar",
            jogos[jogos["resultado_mandante"] != resultado_esperado],
        ),
        (
            "resultados dos dois lados não espelhados",
            jogos[
                jogos["resultado_visitante"]
                != jogos["resultado_mandante"].map(espelho)
            ],
        ),
        ("pontos incoerentes com o resultado", jogos[~pontos_ok]),
        (
            "total_gols diferente da soma do placar",
            jogos[jogos["total_gols"] != gm + gv]
            if "total_gols" in jogos.columns
            else jogos.iloc[0:0],
        ),
        ("data ausente ou fora de 1971..hoje", df[datas_ruins]),
        (
            "id_partida duplicado",
            df[df["id_partida"].duplicated(keep=False)]
            if "id_partida" in df.columns
            else df.iloc[0:0],
        ),
    ]

    linhas = []
    for nome, problematicos in checagens:
        ids = (
            problematicos["id_partida"].dropna().astype(int).head(5).tolist()
            if "id_partida" in problematicos.columns
            else []
        )
        linhas.append(
            {
                "checagem": nome,
                "problemas": int(len(problematicos)),
                "exemplos": ", ".join(str(i) for i in ids),
            }
        )
    return pd.DataFrame(linhas)

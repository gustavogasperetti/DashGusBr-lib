"""Agregações analíticas sobre a OBT do Brasileirão.

Funções puras: recebem o DataFrame no schema canônico e devolvem DataFrames
(ou dicts) prontos para consumo ou visualização. Nenhuma função acessa rede
ou estado global — a carga é responsabilidade de :mod:`dashgusbr.data`.

Nota sobre pontuação: as colunas ``pontos_mandante``/``pontos_visitante`` já
vêm calculadas pelo ETL respeitando a regra da época (vitória valia 2 pontos
até 1994 e 3 pontos a partir de 1995). Por isso as agregações SOMAM esses
pontos em vez de recalcular 3-1-0, e o aproveitamento é normalizado pelo
valor da vitória vigente em cada temporada.
"""

from __future__ import annotations

import difflib
from typing import Optional

import pandas as pd

from .schema import TIPO_FASE_PONTOS_CORRIDOS

# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _validar_ano(df: pd.DataFrame, ano: int) -> None:
    anos = df["ano_campeonato"].dropna().unique()
    if ano not in anos:
        raise ValueError(
            f"Temporada {ano} não encontrada. Dados disponíveis de "
            f"{int(anos.min())} a {int(anos.max())}."
        )


def _validar_time(df: pd.DataFrame, time: str) -> None:
    times = pd.unique(pd.concat([df["mandante"], df["visitante"]]).dropna())
    if time not in times:
        sugestoes = difflib.get_close_matches(time, list(times), n=3)
        dica = f" Você quis dizer: {', '.join(sugestoes)}?" if sugestoes else ""
        raise ValueError(f"Time {time!r} não encontrado na base.{dica}")


def _pontos_corridos(df: pd.DataFrame) -> pd.DataFrame:
    """Mantém apenas jogos que contam para a tabela (fase de pontos corridos)."""
    return df[df["tipo_fase"] == TIPO_FASE_PONTOS_CORRIDOS]


def _com_placar(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(subset=["gols_mandante", "gols_visitante"])


def _formato_longo(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por (partida, time): a partida vista da perspectiva de cada lado."""
    mandante = pd.DataFrame(
        {
            "id_partida": df["id_partida"],
            "ano_campeonato": df["ano_campeonato"],
            "data": df["data"],
            "time": df["mandante"],
            "adversario": df["visitante"],
            "local": "mandante",
            "gols_pro": df["gols_mandante"],
            "gols_contra": df["gols_visitante"],
            "resultado": df["resultado_mandante"],
            "pontos": df["pontos_mandante"],
        }
    )
    visitante = pd.DataFrame(
        {
            "id_partida": df["id_partida"],
            "ano_campeonato": df["ano_campeonato"],
            "data": df["data"],
            "time": df["visitante"],
            "adversario": df["mandante"],
            "local": "visitante",
            "gols_pro": df["gols_visitante"],
            "gols_contra": df["gols_mandante"],
            "resultado": df["resultado_visitante"],
            "pontos": df["pontos_visitante"],
        }
    )
    return pd.concat([mandante, visitante], ignore_index=True)


def _valor_vitoria(df_temporada: pd.DataFrame) -> int:
    """Quantos pontos valia a vitória na temporada (2 até 1994, 3 depois)."""
    pontos = pd.concat(
        [df_temporada["pontos_mandante"], df_temporada["pontos_visitante"]]
    ).dropna()
    if pontos.empty:
        return 3
    return int(pontos.max())


# ---------------------------------------------------------------------------
# Classificação
# ---------------------------------------------------------------------------


def classificacao(df: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Tabela de classificação da fase de pontos corridos de uma temporada.

    Colunas: posicao, time, pontos, jogos, vitorias, empates, derrotas,
    gols_pro, gols_contra, saldo, aproveitamento (%). Desempate no critério
    CBF: pontos, vitórias, saldo de gols, gols pró.
    """
    _validar_ano(df, ano)
    temporada = _com_placar(_pontos_corridos(df[df["ano_campeonato"] == ano]))
    longo = _formato_longo(temporada)

    tabela = (
        longo.groupby("time")
        .agg(
            pontos=("pontos", "sum"),
            jogos=("id_partida", "count"),
            vitorias=("resultado", lambda r: int((r == "V").sum())),
            empates=("resultado", lambda r: int((r == "E").sum())),
            derrotas=("resultado", lambda r: int((r == "D").sum())),
            gols_pro=("gols_pro", "sum"),
            gols_contra=("gols_contra", "sum"),
        )
        .reset_index()
    )
    tabela["saldo"] = tabela["gols_pro"] - tabela["gols_contra"]

    valor_vitoria = _valor_vitoria(temporada)
    tabela["aproveitamento"] = (
        100 * tabela["pontos"] / (tabela["jogos"] * valor_vitoria)
    ).astype(float).round(1)

    tabela = tabela.sort_values(
        by=["pontos", "vitorias", "saldo", "gols_pro", "time"],
        ascending=[False, False, False, False, True],
        ignore_index=True,
    )
    tabela.insert(0, "posicao", tabela.index + 1)
    return tabela


# ---------------------------------------------------------------------------
# Evolução e histórico de um time
# ---------------------------------------------------------------------------


def evolucao_pontos(df: pd.DataFrame, time: str, ano: int) -> pd.DataFrame:
    """Pontuação acumulada de um time, jogo a jogo, dentro de uma temporada.

    A OBT não publica número de rodada, então a linha do tempo é ordenada
    pela data da partida (coluna ``jogo`` = 1º, 2º, 3º... jogo do time).
    """
    _validar_ano(df, ano)
    _validar_time(df, time)
    temporada = _com_placar(_pontos_corridos(df[df["ano_campeonato"] == ano]))
    longo = _formato_longo(temporada)
    jogos = (
        longo[longo["time"] == time]
        .sort_values(["data", "id_partida"])
        .reset_index(drop=True)
    )
    if jogos.empty:
        raise ValueError(f"{time!r} não disputou pontos corridos em {ano}.")
    jogos.insert(0, "jogo", jogos.index + 1)
    jogos["pontos_acumulados"] = jogos["pontos"].cumsum().astype("Int64")
    return jogos[
        [
            "jogo",
            "data",
            "time",
            "adversario",
            "local",
            "gols_pro",
            "gols_contra",
            "resultado",
            "pontos",
            "pontos_acumulados",
        ]
    ]


def historico_time(df: pd.DataFrame, time: str) -> pd.DataFrame:
    """Desempenho de um time temporada a temporada (posição, pontos, aproveitamento).

    O aproveitamento é comparável entre eras (normalizado pelo valor da
    vitória de cada temporada); a posição vem da classificação completa
    da fase de pontos corridos de cada ano.
    """
    _validar_time(df, time)
    pontos_corridos = _pontos_corridos(df)
    anos = sorted(
        pontos_corridos[
            (pontos_corridos["mandante"] == time)
            | (pontos_corridos["visitante"] == time)
        ]["ano_campeonato"].dropna().unique()
    )
    linhas = []
    for ano in anos:
        tabela = classificacao(df, int(ano))
        linha = tabela[tabela["time"] == time]
        if linha.empty:
            continue
        registro = linha.iloc[0].to_dict()
        registro["ano_campeonato"] = int(ano)
        linhas.append(registro)
    if not linhas:
        raise ValueError(f"{time!r} nunca disputou fases de pontos corridos na base.")
    historico = pd.DataFrame(linhas)
    colunas = ["ano_campeonato"] + [c for c in historico.columns if c != "ano_campeonato"]
    return historico[colunas].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Confronto direto
# ---------------------------------------------------------------------------


def confronto(df: pd.DataFrame, time_a: str, time_b: str) -> dict:
    """Histórico do confronto direto entre dois times (todas as fases).

    Retorna um dict com o resumo (jogos, vitórias de cada lado, empates,
    gols) e o DataFrame ``partidas`` com todos os jogos, do mais antigo ao
    mais recente.
    """
    _validar_time(df, time_a)
    _validar_time(df, time_b)
    if time_a == time_b:
        raise ValueError("Informe dois times diferentes para o confronto.")

    partidas = _com_placar(
        df[
            ((df["mandante"] == time_a) & (df["visitante"] == time_b))
            | ((df["mandante"] == time_b) & (df["visitante"] == time_a))
        ]
    ).sort_values(["data", "id_partida"]).reset_index(drop=True)

    a_mandante = partidas["mandante"] == time_a
    vitorias_a = (
        (a_mandante & (partidas["resultado_mandante"] == "V"))
        | (~a_mandante & (partidas["resultado_visitante"] == "V"))
    ).sum()
    vitorias_b = (
        (~a_mandante & (partidas["resultado_mandante"] == "V"))
        | (a_mandante & (partidas["resultado_visitante"] == "V"))
    ).sum()
    empates = (partidas["resultado_mandante"] == "E").sum()
    gols_a = (
        partidas.loc[a_mandante, "gols_mandante"].sum()
        + partidas.loc[~a_mandante, "gols_visitante"].sum()
    )
    gols_b = (
        partidas.loc[~a_mandante, "gols_mandante"].sum()
        + partidas.loc[a_mandante, "gols_visitante"].sum()
    )

    return {
        "time_a": time_a,
        "time_b": time_b,
        "jogos": int(len(partidas)),
        "vitorias_a": int(vitorias_a),
        "empates": int(empates),
        "vitorias_b": int(vitorias_b),
        "gols_a": int(gols_a),
        "gols_b": int(gols_b),
        "partidas": partidas,
    }


# ---------------------------------------------------------------------------
# Estatísticas agregadas do campeonato
# ---------------------------------------------------------------------------


def estatisticas_temporada(df: pd.DataFrame) -> pd.DataFrame:
    """Indicadores por temporada: jogos, gols, média de gols e mando de campo.

    ``pct_vitorias_mandante``/``pct_empates``/``pct_vitorias_visitante`` medem
    o peso do fator casa ao longo da história (somam 100% por temporada).
    """
    jogos = _com_placar(_pontos_corridos(df)).copy()
    jogos["_gols_partida"] = jogos["gols_mandante"] + jogos["gols_visitante"]
    stats = (
        jogos.groupby("ano_campeonato")
        .agg(
            jogos=("id_partida", "count"),
            gols=("_gols_partida", "sum"),
            pct_vitorias_mandante=(
                "resultado_mandante",
                lambda r: round(100 * (r == "V").mean(), 1),
            ),
            pct_empates=(
                "resultado_mandante",
                lambda r: round(100 * (r == "E").mean(), 1),
            ),
            pct_vitorias_visitante=(
                "resultado_mandante",
                lambda r: round(100 * (r == "D").mean(), 1),
            ),
        )
        .reset_index()
    )
    stats["media_gols"] = (stats["gols"] / stats["jogos"]).astype(float).round(2)
    return stats[
        [
            "ano_campeonato",
            "jogos",
            "gols",
            "media_gols",
            "pct_vitorias_mandante",
            "pct_empates",
            "pct_vitorias_visitante",
        ]
    ]


def distribuicao_placares(
    df: pd.DataFrame, ano: Optional[int] = None, max_gols: int = 6
) -> pd.DataFrame:
    """Matriz de frequência de placares (gols do mandante × gols do visitante).

    Placares com mais de ``max_gols`` de um dos lados são agrupados no último
    bin para a matriz não explodir por causa de goleadas raras. Índice =
    gols do mandante, colunas = gols do visitante, valores = nº de jogos.
    """
    jogos = _com_placar(df if ano is None else df[df["ano_campeonato"] == ano])
    if ano is not None:
        _validar_ano(df, ano)
    gm = jogos["gols_mandante"].clip(upper=max_gols).astype(int)
    gv = jogos["gols_visitante"].clip(upper=max_gols).astype(int)
    matriz = pd.crosstab(gm, gv)
    eixo = range(0, max_gols + 1)
    matriz = matriz.reindex(index=eixo, columns=eixo, fill_value=0)
    matriz.index.name = "gols_mandante"
    matriz.columns.name = "gols_visitante"
    return matriz


def maiores_goleadas(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """As ``n`` maiores goleadas da história (maior diferença de gols)."""
    jogos = _com_placar(df).copy()
    jogos["diferenca"] = (jogos["gols_mandante"] - jogos["gols_visitante"]).abs()
    jogos["_gols_partida"] = jogos["gols_mandante"] + jogos["gols_visitante"]
    jogos["placar"] = (
        jogos["gols_mandante"].astype(int).astype(str)
        + " x "
        + jogos["gols_visitante"].astype(int).astype(str)
    )
    return (
        jogos.sort_values(
            ["diferenca", "_gols_partida", "data"], ascending=[False, False, True]
        )
        .head(n)[
            [
                "ano_campeonato",
                "data",
                "mandante",
                "placar",
                "visitante",
                "diferenca",
            ]
        ]
        .reset_index(drop=True)
    )

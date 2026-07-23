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

from ._cores_times import _normalizar
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


def _resolver_time(df: pd.DataFrame, time: str) -> str:
    """Resolve o nome do time com tolerância a caixa, acento e hífen.

    Ordem: nome exato → equivalência normalizada única ("gremio" → "Grêmio")
    → erro com sugestões (``difflib``). Nunca resolve por aproximação vaga:
    empate ou baixa similaridade viram erro, não um palpite silencioso.
    """
    times = list(pd.unique(pd.concat([df["mandante"], df["visitante"]]).dropna()))
    if time in times:
        return time

    chave = _normalizar(time)
    equivalentes = [t for t in times if _normalizar(t) == chave]
    if len(equivalentes) == 1:
        return equivalentes[0]

    sugestoes = difflib.get_close_matches(time, times, n=3)
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


def _valores_vitoria_por_ano(df: pd.DataFrame) -> pd.Series:
    """Valor da vitória em cada temporada da base (índice = ano)."""
    longo = pd.concat(
        [
            df[["ano_campeonato", "pontos_mandante"]].rename(
                columns={"pontos_mandante": "p"}
            ),
            df[["ano_campeonato", "pontos_visitante"]].rename(
                columns={"pontos_visitante": "p"}
            ),
        ]
    ).dropna()
    return longo.groupby("ano_campeonato")["p"].max().astype(int)


def _aproveitamento(jogos_longo: pd.DataFrame, valores_ano: pd.Series) -> float:
    """Aproveitamento (%) de um conjunto de jogos em formato longo.

    Normalizado pelo valor da vitória vigente em cada temporada, para ser
    comparável entre a era de 2 e a de 3 pontos.
    """
    if jogos_longo.empty:
        return 0.0
    maximo = jogos_longo["ano_campeonato"].map(valores_ano).fillna(3).sum()
    if maximo == 0:
        return 0.0
    return round(float(100 * jogos_longo["pontos"].sum() / maximo), 1)


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
    time = _resolver_time(df, time)
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
    time = _resolver_time(df, time)
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
    time_a = _resolver_time(df, time_a)
    time_b = _resolver_time(df, time_b)
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


# ---------------------------------------------------------------------------
# Casa × fora, sequências e forma
# ---------------------------------------------------------------------------


def casa_fora(
    df: pd.DataFrame, time: str, ano: Optional[int] = None
) -> pd.DataFrame:
    """Desempenho de um time como mandante × como visitante (pontos corridos).

    Uma linha por ``local`` (mandante/visitante): jogos, V/E/D, gols, saldo,
    pontos e aproveitamento (normalizado pelo valor da vitória de cada
    temporada). ``ano`` restringe a uma temporada; sem ele, considera toda a
    história do time. O nome resolvido fica em ``resultado.attrs['time']``.
    """
    time = _resolver_time(df, time)
    base = _com_placar(_pontos_corridos(df))
    if ano is not None:
        _validar_ano(df, ano)
        base = base[base["ano_campeonato"] == ano]
    longo = _formato_longo(base)
    jogos = longo[longo["time"] == time]
    if jogos.empty:
        raise ValueError(f"{time!r} não tem jogos de pontos corridos no recorte.")

    valores_ano = _valores_vitoria_por_ano(base)
    linhas = []
    for local in ("mandante", "visitante"):
        parte = jogos[jogos["local"] == local]
        linhas.append(
            {
                "local": local,
                "jogos": int(len(parte)),
                "vitorias": int((parte["resultado"] == "V").sum()),
                "empates": int((parte["resultado"] == "E").sum()),
                "derrotas": int((parte["resultado"] == "D").sum()),
                "gols_pro": int(parte["gols_pro"].sum()),
                "gols_contra": int(parte["gols_contra"].sum()),
                "saldo": int(parte["gols_pro"].sum() - parte["gols_contra"].sum()),
                "pontos": int(parte["pontos"].sum()),
                "aproveitamento": _aproveitamento(parte, valores_ano),
            }
        )
    resultado = pd.DataFrame(linhas)
    resultado.attrs["time"] = time
    return resultado


def sequencias(
    df: pd.DataFrame, time: str, ano: Optional[int] = None
) -> pd.DataFrame:
    """Maiores sequências do time: vitórias, invencibilidade, derrotas, sem vencer.

    Uma linha por tipo, com o tamanho da maior sequência e o período
    (``inicio``/``fim``). Considera todos os jogos com placar do recorte,
    ordenados por data.
    """
    time = _resolver_time(df, time)
    base = _com_placar(df)
    if ano is not None:
        _validar_ano(df, ano)
        base = base[base["ano_campeonato"] == ano]
    longo = _formato_longo(base)
    jogos = (
        longo[longo["time"] == time]
        .sort_values(["data", "id_partida"])
        .reset_index(drop=True)
    )
    if jogos.empty:
        raise ValueError(f"{time!r} não tem jogos com placar no recorte.")

    tipos = {
        "vitorias": jogos["resultado"] == "V",
        "invencibilidade": jogos["resultado"] != "D",
        "derrotas": jogos["resultado"] == "D",
        "sem_vencer": jogos["resultado"] != "V",
    }
    linhas = []
    for tipo, condicao in tipos.items():
        blocos = (~condicao).cumsum()[condicao]
        if blocos.empty:
            linhas.append({"tipo": tipo, "tamanho": 0, "inicio": pd.NaT, "fim": pd.NaT})
            continue
        tamanhos = blocos.groupby(blocos).size()
        maior = tamanhos.idxmax()  # primeiro bloco em caso de empate
        indices = blocos[blocos == maior].index
        linhas.append(
            {
                "tipo": tipo,
                "tamanho": int(tamanhos.max()),
                "inicio": jogos.loc[indices[0], "data"],
                "fim": jogos.loc[indices[-1], "data"],
            }
        )
    resultado = pd.DataFrame(linhas)
    resultado.attrs["time"] = time
    return resultado


def forma_recente(df: pd.DataFrame, time: str, n: int = 5) -> pd.DataFrame:
    """Os últimos ``n`` jogos com placar do time, do mais antigo ao mais recente.

    O aproveitamento do período fica em ``resultado.attrs['aproveitamento']``
    (e o nome resolvido em ``attrs['time']``).
    """
    time = _resolver_time(df, time)
    longo = _formato_longo(_com_placar(df))
    jogos = (
        longo[longo["time"] == time]
        .sort_values(["data", "id_partida"])
        .tail(n)
        .reset_index(drop=True)
    )
    if jogos.empty:
        raise ValueError(f"{time!r} não tem jogos com placar na base.")
    resultado = jogos[
        [
            "data",
            "ano_campeonato",
            "adversario",
            "local",
            "gols_pro",
            "gols_contra",
            "resultado",
            "pontos",
        ]
    ].copy()
    resultado.attrs["time"] = time
    resultado.attrs["aproveitamento"] = _aproveitamento(
        jogos, _valores_vitoria_por_ano(df)
    )
    return resultado


# ---------------------------------------------------------------------------
# Contra todos os adversários
# ---------------------------------------------------------------------------


def desempenho_contra(
    df: pd.DataFrame, time: str, min_jogos: int = 1
) -> pd.DataFrame:
    """Retrospecto de um time contra cada adversário (todas as fases).

    Uma linha por adversário: jogos, V/E/D, gols, saldo e aproveitamento,
    ordenado do adversário mais enfrentado para o menos. ``min_jogos``
    descarta confrontos raros. O nome resolvido fica em ``attrs['time']``.
    """
    time = _resolver_time(df, time)
    longo = _formato_longo(_com_placar(df))
    jogos = longo[longo["time"] == time]
    if jogos.empty:
        raise ValueError(f"{time!r} não tem jogos com placar na base.")

    valores_ano = _valores_vitoria_por_ano(df)
    tabela = (
        jogos.groupby("adversario")
        .agg(
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
    aproveitamentos = (
        jogos.groupby("adversario")
        .apply(lambda parte: _aproveitamento(parte, valores_ano))
        .rename("aproveitamento")
        .reset_index()
    )
    tabela = tabela.merge(aproveitamentos, on="adversario")
    tabela = tabela[tabela["jogos"] >= min_jogos].sort_values(
        ["jogos", "aproveitamento"], ascending=[False, False], ignore_index=True
    )
    tabela.attrs["time"] = time
    return tabela


# ---------------------------------------------------------------------------
# Corrida pelo título e líderes
# ---------------------------------------------------------------------------


def corrida_titulo(df: pd.DataFrame, ano: int, n: int = 4) -> pd.DataFrame:
    """Evolução de pontos dos ``n`` primeiros colocados da temporada.

    Concatena :func:`evolucao_pontos` dos times que terminaram no topo da
    classificação — pronto para :func:`dashgusbr.viz.evolucao`.
    """
    tabela = classificacao(df, ano)
    lideres = tabela.head(n)["time"].tolist()
    return pd.concat(
        [evolucao_pontos(df, time, ano) for time in lideres], ignore_index=True
    )


def lideres_temporada(df: pd.DataFrame) -> pd.DataFrame:
    """O 1º colocado da fase de pontos corridos de cada temporada.

    Atenção: nas eras com mata-mata (até 2002), o líder dos pontos corridos
    NÃO é necessariamente o campeão — a base não registra a fase final de
    forma decidível (finais em dois jogos, agregados). A partir de 2003
    (pontos corridos puros), líder = campeão.
    """
    anos = sorted(
        int(a)
        for a in _com_placar(_pontos_corridos(df))["ano_campeonato"]
        .dropna()
        .unique()
    )
    linhas = []
    for ano in anos:
        lider = classificacao(df, ano).iloc[0]
        linhas.append(
            {
                "ano_campeonato": ano,
                "time": lider["time"],
                "pontos": int(lider["pontos"]),
                "aproveitamento": float(lider["aproveitamento"]),
            }
        )
    return pd.DataFrame(linhas)


def contagem_lideres(df: pd.DataFrame) -> pd.DataFrame:
    """Quantas vezes cada clube terminou líder dos pontos corridos.

    Colunas: time, lideracas, anos (string "1971, 2023..."). Mesma ressalva
    de :func:`lideres_temporada`: líder ≠ campeão nas eras de mata-mata.
    """
    lideres = lideres_temporada(df)
    contagem = (
        lideres.groupby("time")
        .agg(
            lideracas=("ano_campeonato", "count"),
            anos=("ano_campeonato", lambda a: ", ".join(str(x) for x in sorted(a))),
        )
        .reset_index()
        .sort_values(["lideracas", "time"], ascending=[False, True], ignore_index=True)
    )
    return contagem


def ranking_historico(df: pd.DataFrame, min_temporadas: int = 1) -> pd.DataFrame:
    """Tabela histórica geral (todas as temporadas de pontos corridos somadas).

    Pontos somados entre eras não são diretamente comparáveis (vitória valia
    2 até 1994); o aproveitamento é normalizado por temporada e é a métrica
    justa para ordenar entre eras. A ordenação padrão é por pontos (leitura
    clássica de "tabela all-time").
    """
    base = _com_placar(_pontos_corridos(df))
    longo = _formato_longo(base)
    valores_ano = _valores_vitoria_por_ano(base)

    tabela = (
        longo.groupby("time")
        .agg(
            temporadas=("ano_campeonato", "nunique"),
            jogos=("id_partida", "count"),
            pontos=("pontos", "sum"),
            vitorias=("resultado", lambda r: int((r == "V").sum())),
            empates=("resultado", lambda r: int((r == "E").sum())),
            derrotas=("resultado", lambda r: int((r == "D").sum())),
            gols_pro=("gols_pro", "sum"),
            gols_contra=("gols_contra", "sum"),
        )
        .reset_index()
    )
    tabela["saldo"] = tabela["gols_pro"] - tabela["gols_contra"]
    aproveitamentos = (
        longo.groupby("time")
        .apply(lambda parte: _aproveitamento(parte, valores_ano))
        .rename("aproveitamento")
        .reset_index()
    )
    tabela = tabela.merge(aproveitamentos, on="time")
    tabela = tabela[tabela["temporadas"] >= min_temporadas].sort_values(
        ["pontos", "vitorias", "saldo", "time"],
        ascending=[False, False, False, True],
        ignore_index=True,
    )
    tabela.insert(0, "posicao", tabela.index + 1)
    return tabela


def resumo_time(df: pd.DataFrame, time: str) -> dict:
    """Cartão-resumo de um clube: totais, campanhas e recordes.

    Retorna um dict com temporadas disputadas, totais de jogos/V/E/D/gols,
    aproveitamento histórico, melhor e pior campanha (ano/posição) e as
    maiores vitória e derrota (com placar, adversário e data).
    """
    time = _resolver_time(df, time)
    longo = _formato_longo(_com_placar(df))
    jogos = longo[longo["time"] == time]
    if jogos.empty:
        raise ValueError(f"{time!r} não tem jogos com placar na base.")

    campanhas = historico_time(df, time)
    melhor = campanhas.loc[campanhas["posicao"].idxmin()]
    pior = campanhas.loc[campanhas["posicao"].idxmax()]

    saldo_jogo = jogos["gols_pro"] - jogos["gols_contra"]

    def _partida(indice) -> dict:
        jogo = jogos.loc[indice]
        return {
            "data": jogo["data"],
            "adversario": jogo["adversario"],
            "placar": f"{int(jogo['gols_pro'])} x {int(jogo['gols_contra'])}",
            "local": jogo["local"],
        }

    return {
        "time": time,
        "temporadas": int(campanhas["ano_campeonato"].nunique()),
        "primeira_temporada": int(campanhas["ano_campeonato"].min()),
        "ultima_temporada": int(campanhas["ano_campeonato"].max()),
        "jogos": int(len(jogos)),
        "vitorias": int((jogos["resultado"] == "V").sum()),
        "empates": int((jogos["resultado"] == "E").sum()),
        "derrotas": int((jogos["resultado"] == "D").sum()),
        "gols_pro": int(jogos["gols_pro"].sum()),
        "gols_contra": int(jogos["gols_contra"].sum()),
        "aproveitamento": _aproveitamento(jogos, _valores_vitoria_por_ano(df)),
        "melhor_campanha": {
            "ano": int(melhor["ano_campeonato"]),
            "posicao": int(melhor["posicao"]),
        },
        "pior_campanha": {
            "ano": int(pior["ano_campeonato"]),
            "posicao": int(pior["posicao"]),
        },
        "maior_vitoria": _partida(saldo_jogo.idxmax()),
        "maior_derrota": _partida(saldo_jogo.idxmin()),
    }


# ---------------------------------------------------------------------------
# Geografia e recortes do campeonato
# ---------------------------------------------------------------------------


def estatisticas_estados(df: pd.DataFrame) -> pd.DataFrame:
    """Indicadores por estado (UF) do mandante: jogos, gols, clubes, fator casa.

    ``pct_vitorias_mandante`` mede o fator casa visto por estado. Considera
    todos os jogos com placar cujo ``estado_mandante`` está preenchido.
    """
    jogos = _com_placar(df).dropna(subset=["estado_mandante"]).copy()
    jogos["_gols_partida"] = jogos["gols_mandante"] + jogos["gols_visitante"]
    stats = (
        jogos.groupby("estado_mandante")
        .agg(
            jogos=("id_partida", "count"),
            gols=("_gols_partida", "sum"),
            times=("mandante", "nunique"),
            pct_vitorias_mandante=(
                "resultado_mandante",
                lambda r: round(100 * (r == "V").mean(), 1),
            ),
        )
        .reset_index()
        .rename(columns={"estado_mandante": "estado"})
    )
    stats["media_gols"] = (stats["gols"] / stats["jogos"]).astype(float).round(2)
    return stats.sort_values("jogos", ascending=False, ignore_index=True)[
        ["estado", "jogos", "gols", "media_gols", "times", "pct_vitorias_mandante"]
    ]


def _comparar_grupos(df: pd.DataFrame, coluna: str, nomes: "dict[bool, str]"):
    jogos = _com_placar(df).copy()
    jogos["_gols_partida"] = jogos["gols_mandante"] + jogos["gols_visitante"]
    stats = (
        jogos.groupby(coluna)
        .agg(
            jogos=("id_partida", "count"),
            media_gols=("_gols_partida", lambda g: round(float(g.mean()), 2)),
            pct_empates=(
                "resultado_mandante",
                lambda r: round(100 * (r == "E").mean(), 1),
            ),
            pct_vitorias_mandante=(
                "resultado_mandante",
                lambda r: round(100 * (r == "V").mean(), 1),
            ),
        )
        .reset_index()
    )
    stats.insert(0, "grupo", stats[coluna].map(nomes))
    return stats.drop(columns=[coluna])


def comparar_classicos(df: pd.DataFrame) -> pd.DataFrame:
    """Clássicos estaduais × demais jogos: volume, gols, empates e fator casa.

    Usa a flag ``is_classico_estadual`` da OBT. Uma linha por grupo.
    """
    return _comparar_grupos(
        df,
        "is_classico_estadual",
        {True: "Clássico estadual", False: "Demais jogos"},
    )


def comparar_fases(df: pd.DataFrame) -> pd.DataFrame:
    """Mata-mata × fase de pontos: volume, gols, empates e fator casa.

    Usa a flag ``is_mata_mata`` da OBT. Uma linha por grupo.
    """
    return _comparar_grupos(
        df,
        "is_mata_mata",
        {True: "Mata-mata", False: "Fase de pontos"},
    )


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

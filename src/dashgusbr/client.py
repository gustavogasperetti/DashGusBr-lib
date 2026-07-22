"""Fachada pública da dashgusbr: a classe :class:`Brasileirao`.

Orquestra as camadas puras (``data`` → ``analytics`` → ``viz``) com um
DataFrame cacheado por instância. Usuários avançados podem importar as
camadas diretamente (``from dashgusbr import analytics, viz``).
"""

from __future__ import annotations

from typing import Iterable, Optional, Union

import pandas as pd
import plotly.graph_objects as go

from . import analytics, data, viz


class Brasileirao:
    """Ponto de entrada da biblioteca.

    Carrega a OBT sob demanda (no primeiro uso, não no construtor) e a mantém
    em memória; todos os métodos de análise e plot operam sobre essa cópia.

    Examples
    --------
    >>> from dashgusbr import Brasileirao
    >>> br = Brasileirao()
    >>> br.tabela(2023).head()
    >>> br.plot_confronto("Flamengo", "Palmeiras").show()
    """

    def __init__(
        self,
        fonte: str = "auto",
        github_url: Optional[str] = None,
        sheets_url: Optional[str] = None,
        cache: bool = True,
    ) -> None:
        self._fonte = fonte
        self._github_url = github_url
        self._sheets_url = sheets_url
        self._cache = cache
        self._df: Optional[pd.DataFrame] = None

    # -- dados -------------------------------------------------------------

    @property
    def df(self) -> pd.DataFrame:
        """A OBT completa (carga preguiçosa; não modifique in-place)."""
        if self._df is None:
            self._df = data.carregar_dados(
                fonte=self._fonte,
                github_url=self._github_url,
                sheets_url=self._sheets_url,
                cache=self._cache,
            )
        return self._df

    def recarregar(self) -> "Brasileirao":
        """Força novo download da fonte, ignorando os caches."""
        self._df = data.carregar_dados(
            fonte=self._fonte,
            github_url=self._github_url,
            sheets_url=self._sheets_url,
            cache=self._cache,
            forcar_download=True,
        )
        return self

    def partidas(
        self, ano: Optional[int] = None, time: Optional[str] = None
    ) -> pd.DataFrame:
        """Partidas da base, opcionalmente filtradas por temporada e/ou time."""
        partidas = self.df
        if ano is not None:
            partidas = partidas[partidas["ano_campeonato"] == ano]
        if time is not None:
            partidas = partidas[
                (partidas["mandante"] == time) | (partidas["visitante"] == time)
            ]
        return partidas.reset_index(drop=True).copy()

    def anos(self) -> "list[int]":
        """Temporadas disponíveis na base, em ordem crescente."""
        return sorted(int(a) for a in self.df["ano_campeonato"].dropna().unique())

    def times(self, ano: Optional[int] = None) -> "list[str]":
        """Times presentes na base (ou apenas em uma temporada), em ordem alfabética."""
        partidas = self.partidas(ano=ano)
        return sorted(
            pd.unique(pd.concat([partidas["mandante"], partidas["visitante"]]).dropna())
        )

    # -- classificação -----------------------------------------------------

    def tabela(self, ano: int) -> pd.DataFrame:
        """Classificação da fase de pontos corridos da temporada."""
        return analytics.classificacao(self.df, ano)

    def plot_tabela(self, ano: int) -> go.Figure:
        """Gráfico de barras da classificação da temporada."""
        return viz.classificacao(
            self.tabela(ano), titulo=f"Brasileirão {ano} — Classificação"
        )

    # -- evolução e histórico ----------------------------------------------

    def evolucao(self, time: str, ano: int) -> pd.DataFrame:
        """Pontos acumulados do time, jogo a jogo, na temporada."""
        return analytics.evolucao_pontos(self.df, time, ano)

    def plot_evolucao(
        self, times: Union[str, Iterable[str]], ano: int
    ) -> go.Figure:
        """Linha(s) de pontos acumulados de um ou mais times na temporada."""
        if isinstance(times, str):
            times = [times]
        evolucoes = pd.concat(
            [analytics.evolucao_pontos(self.df, t, ano) for t in times],
            ignore_index=True,
        )
        return viz.evolucao(
            evolucoes, titulo=f"Brasileirão {ano} — Evolução de pontos"
        )

    def historico(self, time: str) -> pd.DataFrame:
        """Desempenho do time temporada a temporada (posição, pontos, aproveitamento)."""
        return analytics.historico_time(self.df, time)

    def plot_historico(
        self, time: str, metrica: str = "aproveitamento"
    ) -> go.Figure:
        """Linha do desempenho histórico do time (aproveitamento por padrão)."""
        return viz.historico(self.historico(time), metrica=metrica)

    # -- confronto direto ----------------------------------------------------

    def confronto(self, time_a: str, time_b: str) -> dict:
        """Resumo do confronto direto (inclui o DataFrame ``partidas``)."""
        return analytics.confronto(self.df, time_a, time_b)

    def plot_confronto(self, time_a: str, time_b: str) -> go.Figure:
        """Barras de vitórias/empates do confronto direto."""
        return viz.confronto(self.confronto(time_a, time_b))

    # -- estatísticas do campeonato ------------------------------------------

    def estatisticas(self) -> pd.DataFrame:
        """Indicadores por temporada: jogos, gols, média de gols, fator casa."""
        return analytics.estatisticas_temporada(self.df)

    def plot_gols_por_temporada(self) -> go.Figure:
        """Linha da média de gols por jogo em cada temporada."""
        return viz.gols_por_temporada(self.estatisticas())

    def plot_mandante_visitante(self) -> go.Figure:
        """Linhas do fator casa (% vitórias mandante/empates/visitante)."""
        return viz.mandante_visitante(self.estatisticas())

    def placares(self, ano: Optional[int] = None, max_gols: int = 6) -> pd.DataFrame:
        """Matriz de frequência de placares (mandante × visitante)."""
        return analytics.distribuicao_placares(self.df, ano=ano, max_gols=max_gols)

    def plot_placares(
        self, ano: Optional[int] = None, max_gols: int = 6
    ) -> go.Figure:
        """Heatmap da distribuição de placares."""
        titulo = (
            f"Brasileirão {ano} — Distribuição de placares"
            if ano is not None
            else "Distribuição de placares (1971–hoje)"
        )
        return viz.distribuicao_placares(
            self.placares(ano=ano, max_gols=max_gols), titulo=titulo
        )

    def goleadas(self, n: int = 10) -> pd.DataFrame:
        """As ``n`` maiores goleadas da história do campeonato."""
        return analytics.maiores_goleadas(self.df, n=n)

    def __repr__(self) -> str:
        estado = "não carregado" if self._df is None else f"{len(self._df)} partidas"
        return f"Brasileirao(fonte={self._fonte!r}, dados: {estado})"

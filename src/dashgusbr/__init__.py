"""dashgusbr — consumo e visualização do histórico do Campeonato Brasileiro.

Camada de consumo da arquitetura serverless do projeto Infra-Brasileirao:
lê a OBT (One Big Table) publicada pelo pipeline ETL (CSV no GitHub, com
fallback para Google Sheets) e oferece análises em Pandas e gráficos Plotly.

Uso rápido::

    from dashgusbr import Brasileirao

    br = Brasileirao()
    br.tabela(2023)                      # DataFrame da classificação
    br.plot_confronto("Flamengo", "Palmeiras").show()

Uso avançado (camadas puras)::

    from dashgusbr import analytics, data, viz

    df = data.carregar_dados()
    tab = analytics.classificacao(df, ano=2023)
    fig = viz.classificacao(tab)
"""

from . import analytics, config, data, schema, viz
from .client import Brasileirao
from .data import carregar_dados

__version__ = "0.1.1"

__all__ = [
    "Brasileirao",
    "carregar_dados",
    "analytics",
    "config",
    "data",
    "schema",
    "viz",
    "__version__",
]

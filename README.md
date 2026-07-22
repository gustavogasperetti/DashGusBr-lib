# dashgusbr

**Análise e visualização do histórico completo do Campeonato Brasileiro (1971–hoje), em uma linha de Python.**

`dashgusbr` é a camada de consumo e visualização de uma arquitetura serverless desacoplada em dois
repositórios: o [Infra-Brasileirao](https://github.com/gustavogasperetti/Infra-Brasileirao) roda o
pipeline ETL agendado (cron) que limpa e consolida todas as partidas do Brasileirão em uma
**OBT (One Big Table)** publicada na camada gold; este repositório contém apenas a biblioteca, que
lê essa tabela (CSV no GitHub, com fallback para Google Sheets) e oferece análises prontas em
**Pandas** e gráficos interativos em **Plotly**. O único acoplamento entre os dois é o contrato de
dados: a URL da OBT e o schema documentado abaixo.

```
┌─────────────┐      ┌──────────────┐      ┌──────────────────┐      ┌────────────┐
│ Fontes brutas │ ──▶ │ Pipeline ETL │ ──▶ │ OBT (camada gold) │ ──▶ │ dashgusbr  │
└─────────────┘      └──────────────┘      │ GitHub / Sheets   │      │ análise+viz│
                                           └──────────────────┘      └────────────┘
```

## Instalação

```bash
pip install dashgusbr
```

Requer Python ≥ 3.9. Dependências: `pandas` e `plotly`.

## Uso rápido

```python
from dashgusbr import Brasileirao

br = Brasileirao()                     # baixa a OBT na primeira consulta e cacheia

br.tabela(2023)                        # DataFrame: classificação de 2023
br.plot_tabela(2023).show()            # gráfico de barras da classificação

br.plot_evolucao(["Palmeiras", "Botafogo"], 2023).show()   # corrida do título
br.plot_confronto("Flamengo", "Palmeiras").show()          # histórico do confronto
br.plot_historico("Santos").show()     # aproveitamento temporada a temporada
br.plot_gols_por_temporada().show()    # média de gols/jogo desde 1971
br.plot_mandante_visitante().show()    # o fator casa ao longo da história
br.plot_placares().show()              # heatmap: frequência de cada placar
br.goleadas(10)                        # DataFrame: as 10 maiores goleadas
```

Métodos utilitários: `br.anos()`, `br.times(ano=2023)`, `br.partidas(ano=2023, time="Grêmio")`,
`br.recarregar()` (força novo download).

## Uso avançado — camadas puras

A classe `Brasileirao` é uma fachada. Por baixo, a biblioteca é organizada em três camadas de
funções puras que você pode importar diretamente (por exemplo, para montar seu próprio dashboard
em Streamlit):

```python
from dashgusbr import data, analytics, viz

df  = data.carregar_dados()                       # OBT completa, schema canônico
tab = analytics.classificacao(df, ano=2023)       # DataFrame → DataFrame
fig = viz.classificacao(tab)                      # DataFrame → plotly Figure
```

| Camada | Responsabilidade | Principais funções |
|---|---|---|
| `dashgusbr.data` | carga, fallback e cache | `carregar_dados`, `limpar_cache` |
| `dashgusbr.analytics` | agregações Pandas | `classificacao`, `evolucao_pontos`, `historico_time`, `confronto`, `estatisticas_temporada`, `distribuicao_placares`, `maiores_goleadas` |
| `dashgusbr.viz` | figuras Plotly | `classificacao`, `evolucao`, `historico`, `confronto`, `gols_por_temporada`, `mandante_visitante`, `distribuicao_placares` |

## Fontes de dados

Por padrão, `dashgusbr` tenta o CSV publicado no GitHub e, se indisponível, cai para o Google
Sheets. Também é possível apontar para um arquivo local ou URL própria:

```python
br = Brasileirao()                       # auto: GitHub → Sheets
br = Brasileirao(fonte="sheets")         # força o Google Sheets
br = Brasileirao(fonte="dados/obt.csv")  # arquivo local no mesmo schema
br = Brasileirao(github_url="https://raw.githubusercontent.com/.../obt.csv")
```

## Schema da OBT

A biblioteca normaliza os nomes na carga (`Data` → `data`, `Mandante` → `mandante`, ...) e valida
as colunas obrigatórias. Schema canônico:

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_partida` | int | identificador da partida |
| `ano_campeonato` | int | temporada |
| `data` | date | data da partida |
| `mandante` / `visitante` | str | times |
| `estado_mandante` / `estado_visitante` | str | UF de cada time |
| `gols_mandante` / `gols_visitante` | int | placar |
| `resultado_mandante` / `resultado_visitante` | str | `V`/`E`/`D` |
| `placar_status` | str | status do placar |
| `fase` / `tipo_fase` | str | fase do campeonato (`Pontos Corridos`, mata-mata...) |
| `is_mata_mata` / `is_classico_estadual` | bool | flags |
| `total_gols`, `saldo_gols_*` | int | derivadas do placar |
| `pontos_mandante` / `pontos_visitante` | int | pontos da partida, **já na regra da época** |

> **Nota histórica:** a vitória valia **2 pontos até 1994** e **3 pontos a partir de 1995**. As
> colunas de pontos já vêm calculadas pelo ETL com a regra correta de cada era; por isso as tabelas
> de classificação somam esses pontos (em vez de recalcular 3-1-0) e o **aproveitamento** é
> normalizado pelo valor da vitória da temporada — a única métrica comparável entre eras.

Apenas jogos com `tipo_fase == "Pontos Corridos"` entram na classificação e nas estatísticas de
temporada; o confronto direto considera todas as fases.

## Desenvolvimento

```bash
git clone https://github.com/gustavogasperetti/DashGusBr-lib.git
cd DashGusBr-lib
pip install -e ".[dev]"
pytest                          # suíte offline (fixture com mini-OBT)
pytest -m rede -o addopts=""    # smoke tests que baixam a OBT real (requer internet)
```

Antes da publicação no PyPI, é possível instalar direto do GitHub:

```bash
pip install git+https://github.com/gustavogasperetti/DashGusBr-lib.git
```

## Licença

[MIT](LICENSE)

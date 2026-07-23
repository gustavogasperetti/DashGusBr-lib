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

Mais análises prontas:

```python
br.plot_corrida_titulo(2023, n=4).show()   # evolução dos 4 primeiros colocados
br.plot_casa_fora("Grêmio").show()         # V/E/D como mandante × visitante
br.plot_contra("Palmeiras").show()         # aproveitamento contra cada adversário
br.plot_estados().show()                   # jogos por estado (UF)
br.plot_lideres().show()                   # vezes que cada clube liderou os pontos corridos
br.sequencias("Flamengo")                  # DataFrame: maiores sequências (vitórias, invencibilidade...)
br.forma("Botafogo", n=5)                  # DataFrame: os últimos 5 jogos
br.resumo("Cruzeiro")                      # dict: cartão-resumo do clube (campanhas, recordes)
br.ranking()                               # DataFrame: tabela histórica geral
br.classicos(); br.fases()                 # clássicos × demais jogos; mata-mata × pontos corridos
```

Métodos utilitários: `br.anos()`, `br.times(ano=2023)`, `br.partidas(ano=2023, time="Grêmio")`,
`br.recarregar()` (força novo download). Nomes de time aceitam variações de caixa e acento
(`"gremio"` resolve para `"Grêmio"`).

## Como personalizar os gráficos

Todo método `plot_*` aceita `titulo=` e argumentos de layout do Plotly, repassados a
`fig.update_layout` — e a figura retornada é um `plotly.graph_objects.Figure` normal, então
qualquer ajuste do Plotly funciona depois:

```python
fig = br.plot_tabela(2023, titulo="Meu título", width=1000, height=700)
fig = br.plot_gols_por_temporada(template="plotly_dark")   # troca o tema

fig.update_traces(marker_color="#ff5722")                  # pós-processamento livre
fig.add_annotation(text="Fonte: OBT Infra-Brasileirao", xref="paper", x=1, y=-0.12)
```

Nas funções de `dashgusbr.viz`, o parâmetro `cores=` substitui a paleta padrão
(`viz.classificacao(tab, cores="#ff5722")`).

### Cores oficiais dos clubes

Os gráficos por time aceitam `cores_times=True` para pintar cada clube com sua cor de
identidade (Palmeiras → verde, Flamengo → vermelho, Grêmio → azul...):

```python
br.plot_corrida_titulo(2023, n=4, cores_times=True).show()
br.plot_confronto("Flamengo", "Palmeiras", cores_times=True).show()

from dashgusbr import cor_time
cor_time("Palmeiras")   # '#006437' — para usar em gráficos próprios
```

Clubes fora do mapa (e dois clubes de mesma cor no mesmo gráfico — ex.: dois alvinegros)
caem automaticamente na paleta categórica padrão. O recurso é **opt-in**: cores de clube
não são seguras para daltonismo; a paleta padrão da biblioteca é validada.

### Exportação

```python
from dashgusbr import salvar_html, salvar_imagem

salvar_html(fig, "grafico.html")            # página interativa
salvar_imagem(fig, "grafico.png", escala=2) # PNG/SVG/PDF — requer: pip install dashgusbr[imagem]
```

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
| `dashgusbr.data` | carga, fallback e caches (memória + disco) | `carregar_dados`, `limpar_cache` |
| `dashgusbr.analytics` | agregações Pandas | `classificacao`, `evolucao_pontos`, `historico_time`, `confronto`, `casa_fora`, `sequencias`, `forma_recente`, `desempenho_contra`, `corrida_titulo`, `lideres_temporada`, `ranking_historico`, `resumo_time`, `estatisticas_temporada`, `estatisticas_estados`, `comparar_classicos`, `comparar_fases`, `distribuicao_placares`, `maiores_goleadas` |
| `dashgusbr.viz` | figuras Plotly | `classificacao`, `evolucao`, `historico`, `confronto`, `casa_fora`, `desempenho_contra`, `estados`, `lideres`, `gols_por_temporada`, `mandante_visitante`, `distribuicao_placares` |
| `dashgusbr.export` | exportação de figuras | `salvar_html`, `salvar_imagem` |

## Fontes de dados

Por padrão, `dashgusbr` tenta o CSV publicado no GitHub e, se indisponível, cai para o Google
Sheets. Também é possível apontar para um arquivo local ou URL própria:

```python
br = Brasileirao()                       # auto: GitHub → Sheets
br = Brasileirao(fonte="sheets")         # força o Google Sheets
br = Brasileirao(fonte="dados/obt.csv")  # arquivo local no mesmo schema
br = Brasileirao(github_url="https://raw.githubusercontent.com/.../obt.csv")
```

O CSV baixado fica em cache em disco (`~/.dashgusbr/cache`, validade de 24h), acelerando novas
sessões e permitindo uso offline; controle com `carregar_dados(cache_disco=..., validade_horas=...)`
e limpe com `data.limpar_cache(disco=True)`. Para acompanhar o download:

```python
import logging
logging.basicConfig(level=logging.INFO)   # logger "dashgusbr"
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

# dashgusbr

**Análise e visualização do histórico completo do Campeonato Brasileiro (1971–hoje), em uma linha de Python.**

```python
Brasileirao().dashboard("Palmeiras").show()   # o painel completo do clube na temporada atual
```

`dashgusbr` é a camada de consumo e visualização de uma arquitetura serverless desacoplada em dois
repositórios: o [Infra-Brasileirao](https://github.com/gustavogasperetti/Infra-Brasileirao) roda o
pipeline ETL agendado (cron) que limpa e consolida todas as partidas do Brasileirão em uma
**OBT (One Big Table)** publicada na camada gold; este repositório contém apenas a biblioteca, que
lê essa tabela (CSV no GitHub, com fallback para Google Sheets) e oferece análises prontas em
**Pandas** e gráficos interativos em **Plotly**. O único acoplamento entre os dois é o contrato de
dados: a URL da OBT e o schema documentado abaixo.

```
┌─────────────┐      ┌──────────────┐      ┌──────────────────┐      ┌────────────┐
│Fontes brutas│ ──▶ │ Pipeline ETL │ ──▶  │ OBT (camada gold)│ ──▶ │ dashgusbr  │
└─────────────┘      └──────────────┘      │ GitHub / Sheets  │      │ análise+viz│
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

br.dashboard("Palmeiras").show()       # dashboard completo do time (campeonato atual)

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
br.plot_confronto_evolucao("Grêmio", "Internacional").show()  # saldo do confronto na história
br.plot_estados().show()                   # jogos por estado (UF)
br.plot_mapa_estados().show()              # mapa coroplético do Brasil por UF
br.plot_saldos().show()                    # distribuição do saldo de gols por jogo
br.plot_lideres().show()                   # vezes que cada clube liderou os pontos corridos
br.sequencias("Flamengo")                  # DataFrame: maiores sequências (vitórias, invencibilidade...)
br.forma("Botafogo", n=5)                  # DataFrame: os últimos 5 jogos
br.resumo("Cruzeiro")                      # dict: cartão-resumo do clube (campanhas, recordes)
br.ranking()                               # DataFrame: tabela histórica geral
br.classicos(); br.fases()                 # clássicos × demais jogos; mata-mata × pontos corridos
br.viagem(); br.gols_por_decada()          # fator viagem do visitante; média de gols por década
br.validar()                               # relatório de consistência dos dados
```

Pelo terminal, sem escrever Python:

```bash
python -m dashgusbr tabela 2023            # classificação no terminal
python -m dashgusbr tabela 2023 --html t.html
python -m dashgusbr goleadas 10
python -m dashgusbr resumo Cruzeiro
python -m dashgusbr validar               # checagens de consistência da OBT
```

Métodos utilitários: `br.anos()`, `br.times(ano=2023)`, `br.partidas(ano=2023, time="Grêmio")`,
`br.recarregar()` (força novo download). Nomes de time aceitam variações de caixa e acento
(`"gremio"` resolve para `"Grêmio"`).

> 📓 **Guia completo**: o notebook [`examples/guia_dashgusbr.ipynb`](examples/guia_dashgusbr.ipynb)
> percorre **tudo** que a biblioteca faz — o dashboard por time (seção 3), todos os gráficos,
> análises, combinações de personalização, exportação, validação de dados, camadas puras e CLI.

## Dashboard por time

Um comando, um painel inteiro: `br.dashboard("Palmeiras")` devolve **uma única figura Plotly**
com os gráficos padrão do clube na temporada atual da base.

```python
br.dashboard("Palmeiras").show()                       # campeonato atual
br.dashboard("Palmeiras", ano_campeonato=2020).show()  # temporada antiga, mesmos painéis
br.dashboard("gremio").show()                          # nome tolerante a acento e caixa
br.dashboard(["Palmeiras", "Corinthians"]).show()      # dois clubes, lado a lado
```

Os painéis padrão são sempre os mesmos — é o que faz dois times (ou duas temporadas do mesmo
time) serem comparáveis de bate-pronto:

| Painel | O que mostra |
|---|---|
| `indicadores` | posição, pontos, V/E/D e aproveitamento, com a variação sobre a temporada anterior |
| `evolucao` | pontos acumulados jogo a jogo na temporada |
| `casa_fora` | V/E/D como mandante × como visitante |
| `classificacao` | a tabela da temporada, com o time destacado |
| `adversarios` | aproveitamento contra cada adversário da temporada |
| `forma` | pontos jogo a jogo no fim da temporada |
| `historico` | aproveitamento temporada a temporada, com o ano do recorte marcado |

### Comparando clubes

Passe uma **lista** (até quatro clubes) e o mesmo padrão vira uma comparação:

```python
br.dashboard(["Palmeiras", "Corinthians"], 2023, cores_times=True).show()
br.dashboard(["Flamengo", "Vasco", "Fluminense"], 2019, remover=["adversarios"]).show()
```

Cada painel sabe o que fazer com N clubes:

| Estratégia | Painéis | Como fica |
|---|---|---|
| `unico` | `evolucao`, `classificacao`, `historico`, `posicao` | todos na **mesma** figura — uma série por clube, ou a tabela com todos acesos |
| `repetir` | `casa_fora`, `forma`, `adversarios`, `placares`, `saldos`, `sequencias` | *small multiples*: um tile por clube, lado a lado, na mesma escala |
| `indicadores` | — | uma faixa de números por clube, rotulada com o nome dele |

A coluna `comparacao` de `br.paineis()` mostra a estratégia de cada painel, e
`registrar_painel(..., comparacao="unico")` define a dos seus.

Duas regras que valem conhecer:

- **cor fixa por clube** em todos os painéis — sem isso a comparação não se lê. Com
  `cores_times=True` cada um usa a cor oficial (cuidado: dois alvinegros ficam iguais);
  sem ela, cada clube pega um slot da paleta validada para daltonismo.
- **a temporada é a mais recente que todos disputaram** quando você não passa
  `ano_campeonato`; um ano em que um dos clubes não jogou é erro na entrada, e não um
  painel quebrando no meio.

Com 3 ou 4 clubes os tiles ficam estreitos — vale um `remover=["adversarios"]`
(o painel com os nomes dos adversários no eixo) ou `colunas=1`.

### Modificando o dashboard

A personalização acontece **em cima** do padrão, sem perdê-lo:

```python
br.paineis()                           # DataFrame: catálogo de painéis (nome, padrão?, descrição)

br.dashboard("Santos", incluir=["sequencias", "placares"])   # acrescenta do catálogo
br.dashboard("Santos", remover=["adversarios"])              # tira do padrão
br.dashboard("Santos", paineis=["evolucao", "classificacao"]) # define a lista inteira
br.dashboard("Santos", colunas=3, altura_linha=300)          # grade e altura
br.dashboard("Santos", cores_times=True, template="dashgusbr_escuro")
```

Além dos painéis do catálogo (`posicao`, `sequencias`, `placares`, `saldos`,
`adversarios_historico`), `incluir=` aceita **gráficos seus** — uma figura pronta ou uma função
que recebe o contexto do recorte (base, time já resolvido, temporada e os filtros derivados):

```python
import plotly.express as px

def gols_por_rodada(ctx):                     # ctx.df, ctx.time, ctx.ano, ctx.df_time_ano
    jogos = br.evolucao(ctx.time, ctx.ano)
    return px.bar(jogos, x="jogo", y="gols_pro")

br.dashboard("Santos", incluir=[("Gols por jogo", gols_por_rodada)]).show()
br.dashboard("Santos", incluir=[("Confronto", br.plot_confronto("Santos", "Palmeiras"))]).show()
```

Para reusar um painel seu pelo nome em qualquer dashboard, registre-o no catálogo:

```python
from dashgusbr import dashboard

dashboard.registrar_painel("gols_por_rodada", gols_por_rodada, titulo="Gols por jogo")
br.dashboard("Santos", incluir=["gols_por_rodada"]).show()
```

O resultado é um `go.Figure` comum: `salvar_html(fig, "palmeiras.html")` e
`fig.update_layout(...)` funcionam normalmente. A seção 3 do
[guia](examples/guia_dashgusbr.ipynb) mostra cada variação rodando.

> Um painel entra em **uma** célula da grade, com um par de eixos: uma figura sua com eixo
> secundário (`yaxis2`) cabe como painel, mas as séries saem todas no mesmo eixo — para eixo
> duplo, exporte essa figura à parte.

## Como personalizar os gráficos

Todo método `plot_*` aceita `titulo=` e argumentos de layout do Plotly, repassados a
`fig.update_layout` — e a figura retornada é um `plotly.graph_objects.Figure` normal, então
qualquer ajuste do Plotly funciona depois:

```python
fig = br.plot_tabela(2023, titulo="Meu título", width=1000, height=700)
fig = br.plot_tabela(2023, template="dashgusbr_escuro")    # tema escuro da lib
fig = br.plot_gols_por_temporada(template="plotly_dark")   # ou qualquer tema Plotly

fig.update_traces(marker_color="#ff5722")                  # pós-processamento livre
fig.add_annotation(text="Fonte: OBT Infra-Brasileirao", xref="paper", x=1, y=-0.12)
```

Nas funções de `dashgusbr.viz`, o parâmetro `cores=` substitui a paleta padrão
(`viz.classificacao(tab, cores="#ff5722")`); gráficos com rótulos aceitam
`mostrar_valores=False` e os com legenda, `mostrar_legenda=False`. Rótulos que
caem dentro de barras recebem cor de texto automática por luminância (legíveis
sobre barras escuras).

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

from dashgusbr import dashboard
fig = dashboard.dashboard_time(df, "Palmeiras", 2023)   # painéis compostos em uma figura
```

| Camada | Responsabilidade | Principais funções |
|---|---|---|
| `dashgusbr.data` | carga, fallback e caches (memória + disco) | `carregar_dados`, `carregar_geojson_estados`, `limpar_cache` |
| `dashgusbr.analytics` | agregações Pandas | `classificacao`, `evolucao_pontos`, `historico_time`, `confronto`, `evolucao_confronto`, `casa_fora`, `sequencias`, `forma_recente`, `desempenho_contra`, `corrida_titulo`, `lideres_temporada`, `ranking_historico`, `resumo_time`, `estatisticas_temporada`, `estatisticas_estados`, `fator_viagem`, `media_gols_por_decada`, `comparar_classicos`, `comparar_fases`, `distribuicao_placares`, `distribuicao_saldos`, `maiores_goleadas`, `ultima_temporada` |
| `dashgusbr.viz` | figuras Plotly | `classificacao`, `evolucao`, `historico`, `confronto`, `evolucao_confronto`, `casa_fora`, `desempenho_contra`, `estados`, `mapa_estados`, `lideres`, `gols_por_temporada`, `mandante_visitante`, `distribuicao_placares`, `distribuicao_saldos`, `forma`, `sequencias` |
| `dashgusbr.dashboard` | composição de painéis em uma figura | `dashboard_time`, `paineis_disponiveis`, `registrar_painel`, `PAINEIS`, `PAINEIS_PADRAO` |
| `dashgusbr.schema` | schema canônico e qualidade | `normalizar`, `validar`, `relatorio_consistencia` |
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
pytest                          # suíte offline (fixture com mini-OBT): 161 testes
pytest -m rede -o addopts=""    # smoke tests que baixam a OBT real (requer internet)
ruff check src tests examples   # lint (o mesmo do CI)
python examples/demo.py         # regenera galeria_dashgusbr.html com todos os gráficos
```

Antes da publicação no PyPI, é possível instalar direto do GitHub:

```bash
pip install git+https://github.com/gustavogasperetti/DashGusBr-lib.git
```

## Licença

[MIT](LICENSE)

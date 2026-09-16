# Changelog

Todas as mudanças relevantes deste projeto são documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/).

> As seções `0.1.1`, `0.2.0` e `0.3.0` foram reconstruídas em set/2026 a partir
> do conteúdo de cada tag: até então as entregas ficavam acumuladas em
> "Não lançado" e o arquivo estava uma versão defasado.

## [Não lançado]

## [0.5.0] - 2026-09-15

### Adicionado
- **Comparação entre clubes**: `br.dashboard(["Palmeiras", "Corinthians"], 2023)`
  — até quatro clubes no mesmo padrão de painéis. Painéis `unico` (evolução,
  classificação, histórico, posição) põem todos na mesma figura; os demais
  viram *small multiples*, um tile por clube na mesma escala; os indicadores
  ganham uma faixa por clube. Cada clube tem cor fixa em todos os painéis e,
  sem `ano_campeonato`, o recorte é a última temporada que **todos**
  disputaram. A estratégia de cada painel fica na coluna `comparacao` de
  `br.paineis()` e em `registrar_painel(..., comparacao=)`.
- **`viz.historico` e `viz.classificacao` com vários times**: a primeira
  aceita campanhas empilhadas (uma linha por clube) e a segunda aceita
  `destaque=["Palmeiras", "Corinthians"]`.

### Corrigido
- **Histórico dos clubes entre 1972 e 2000**: `historico_time` (e, por
  consequência, `resumo_time`, `viz.historico` e os painéis "histórico" e
  "posição" do dashboard) pulava direto de 1971 para 2001, porque só
  considerava jogos com `tipo_fase == "Pontos Corridos"` — e nesse período o
  Brasileirão era disputado em fases classificatórias e de grupos. Agora
  toda fase em formato de liga (`schema.TIPOS_FASE_LIGA`) entra na campanha.
  A nova coluna `formato` diz se a linha veio da tabela de pontos corridos
  ou da soma das fases de grupos; nesta última não há classificação geral
  única, então `posicao` fica vazia (`Int64` com `<NA>`), o hover mostra "—"
  e a linha de posição fica com um buraco no ano. `melhor_campanha` e
  `pior_campanha` do resumo consideram só temporadas com posição (`None` se
  não houver nenhuma). Os indicadores do dashboard passam a comparar com a
  temporada anterior de qualquer formato, sem delta de posição quando ela
  não existe.

## [0.4.0] - 2026-09-12

### Adicionado
- **Dashboard por time**: `br.dashboard("Palmeiras")` monta, em uma única
  figura, os painéis padrão do clube no campeonato atual da base —
  indicadores da campanha, evolução de pontos, casa × fora, classificação com
  o time destacado, aproveitamento por adversário, últimos jogos e histórico.
  `ano_campeonato=2020` troca a temporada mantendo os mesmos painéis.
- **Dashboard personalizável**: `incluir=`/`remover=`/`paineis=` ajustam a
  lista sem perder o padrão; `incluir=` também aceita figuras suas e funções
  `(ctx) -> go.Figure`. Catálogo em `br.paineis()` (painéis extras:
  `posicao`, `sequencias`, `placares`, `saldos`, `adversarios_historico`) e
  `dashboard.registrar_painel()` para publicar painéis próprios pelo nome.
- **Duas figuras novas em `viz`**: `viz.forma` (pontos jogo a jogo nos últimos
  jogos, uma série por resultado) e `viz.sequencias` (recordes de vitórias,
  invencibilidade, derrotas e jejum).
- **Destaque na classificação**: `viz.classificacao(tab, destaque="Santos")` e
  `br.plot_tabela(2023, destaque="Santos")` acendem um time e apagam os demais.
- **Campeonato atual**: `analytics.ultima_temporada(df, time=None)` — a última
  temporada da base (ou do time), usada quando o dashboard é chamado sem ano.

## [0.3.0] - 2026-07-29

### Adicionado
- **Tema escuro** próprio: template `dashgusbr_escuro`, aplicável com
  `template="dashgusbr_escuro"` em qualquer `plot_*`/`viz.*`.
- **Contraste automático**: rótulos que caem dentro de barras recebem cor de
  texto por luminância (`cor_texto_para`), legíveis sobre barras escuras.
- **Controle de rótulos/legenda**: `mostrar_valores=` e `mostrar_legenda=`
  nas funções `viz.*` com rótulos/legenda.
- **CLI**: `python -m dashgusbr tabela 2023` (também `goleadas`, `ranking`,
  `resumo`, `times`, `anos`, `validar`; `--fonte` e `--html`).
- **Linha do tempo do confronto**: `analytics.evolucao_confronto` +
  `br.plot_confronto_evolucao(a, b)` (saldo acumulado na história).
- **Fator viagem**: `analytics.fator_viagem` / `br.viagem()` — visitante
  dentro × fora do seu estado.
- **Inflação de gols**: `analytics.media_gols_por_decada` /
  `br.gols_por_decada()` (média por década e era de pontuação).
- **Distribuição de saldos**: `analytics.distribuicao_saldos` +
  `br.plot_saldos()` (a assimetria é o fator casa).
- **Mapa coroplético por UF**: `viz.mapa_estados` + `br.plot_mapa_estados()`,
  com `data.carregar_geojson_estados()` (GeoJSON público, cacheado em disco).
- **Validação de consistência**: `schema.relatorio_consistencia` /
  `br.validar()` — placares × resultados × pontos, datas, duplicatas.
- **Cores de clube**: cauda longa mapeada — de 54 para 120 dos 167 clubes
  da base.
- **Galeria de exemplos**: `examples/demo.py` passa a gerar
  `galeria_dashgusbr.html` com todos os gráficos e a chamada de cada um.
- **Guia completo em notebook**: `examples/guia_dashgusbr.ipynb` percorre toda
  a API — gráficos, análises, personalização, exportação, validação, camadas
  puras e CLI (todas as células executáveis validadas contra a base real).

### Corrigido
- `br.partidas(time="gremio")` agora resolve o nome com a mesma tolerância
  dos demais métodos (antes retornava um filtro vazio silencioso).
- Cache em disco: `validade_horas=0` podia aceitar o cache mesmo assim quando
  o mtime do arquivo ficava milissegundos à frente do relógio (granularidade
  do filesystem no Windows) — causa de um teste intermitente.
- `analytics.distribuicao_placares` valida o ano antes de filtrar.

## [0.2.0] - 2026-07-23

### Adicionado
- **Cores oficiais por time** (`cores_times=True` nos plots por time; `cor_time`
  e `cores_para_times` na API pública), com fallback seguro para a paleta padrão
  e desambiguação de cores repetidas no mesmo gráfico.
- **Personalização dos gráficos**: `titulo=`, `cores=` e `**layout_kwargs`
  (repassados a `fig.update_layout`) em todas as funções `viz.*` e métodos `plot_*`.
- **Novas análises**: `casa_fora`, `sequencias`, `forma_recente`,
  `desempenho_contra`, `corrida_titulo`, `lideres_temporada`, `contagem_lideres`,
  `ranking_historico`, `resumo_time`, `estatisticas_estados`,
  `comparar_classicos`, `comparar_fases` — com os métodos correspondentes na
  fachada `Brasileirao` e novos gráficos (`casa_fora`, `desempenho_contra`,
  `estados`, `lideres`, `plot_corrida_titulo`).
- **Cache em disco** da OBT (`~/.dashgusbr/cache`, validade configurável), retry
  com backoff e timeout no download, logging de progresso (logger `dashgusbr`)
  e fallback para a cópia local quando a rede está fora.
- **Exportação**: `salvar_html` e `salvar_imagem` (extra `dashgusbr[imagem]`
  instala o kaleido).
- **Busca tolerante de time**: nomes resolvem ignorando caixa/acento/hífen
  ("gremio" → "Grêmio"), com sugestões no erro.
- Marcador `py.typed` e lint (`ruff`) no CI.

## [0.1.1] - 2026-07-22

### Adicionado
- **CI/CD de release**: workflow `Release` (escolhe patch/minor/major, grava a
  versão em `__init__.py`, commita, cria a tag e a Release com notas geradas
  dos commits) e gatilho `workflow_dispatch` no `publish.yml`, que sobe o
  pacote no PyPI a partir da tag.

## [0.1.0] - 2026-07-22

### Adicionado
- Cliente `Brasileirao` para consumo da OBT do projeto Infra-Brasileirao.
- Camadas puras `data`, `analytics` e `viz` (gráficos Plotly).
- Módulos de apoio `config`, `schema` e tema visual.
- Suíte de testes (`pytest`) e exemplo de uso em `examples/demo.py`.

[Não lançado]: https://github.com/gustavogasperetti/DashGusBr-lib/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/gustavogasperetti/DashGusBr-lib/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/gustavogasperetti/DashGusBr-lib/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/gustavogasperetti/DashGusBr-lib/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/gustavogasperetti/DashGusBr-lib/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/gustavogasperetti/DashGusBr-lib/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/gustavogasperetti/DashGusBr-lib/releases/tag/v0.1.0

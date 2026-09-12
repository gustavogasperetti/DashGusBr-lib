# Roadmap — dashgusbr

> **Legenda**
> Prioridade: 🔴 alta · 🟡 média · 🟢 baixa
> Esforço: ⚡ pequeno · ⚙️ médio · 🏗️ grande
> Status: `[ ]` não iniciado · `[~]` em andamento · `[x]` concluído · `[!]` bloqueado

Colunas disponíveis na OBT (base para novas contas):
`id_partida, ano_campeonato, data, mandante, visitante, estado_mandante,
estado_visitante, gols_mandante, gols_visitante, resultado_mandante,
resultado_visitante, placar_status, fase, tipo_fase, is_mata_mata,
is_classico_estadual, total_gols, saldo_gols_mandante, saldo_gols_visitante,
pontos_mandante, pontos_visitante`.

---

## Roadmap v1 — CONCLUÍDO ✅

Fechado em jul/2026. Estado final de cada tema:

### 1. Cores oficiais por time 🎨
- [x] Mapa de cores (`_cores_times.py`), normalização robusta, aliases e fallback.
- [x] `usar_cores_times=True` nos plots por time; `cores_times=` na fachada.
- [x] API pública: `from dashgusbr import cor_time`.
- [x] **Contraste/legibilidade** — `cor_texto_para` (luminância WCAG) aplica cor
  de texto automática a rótulos que caem dentro de barras escuras.
- [x] Acessibilidade documentada (recurso opt-in; cores duplicadas caem na
  paleta categórica validada).
- [x] **Cobertura** — 120 dos 167 clubes da base mapeados. Os 47 restantes são
  clubes extintos/regionais cuja cor histórica não é verificável com
  confiança; ficam no fallback seguro (item de pesquisa segue no v2).

### 2. Personalização dos gráficos 🛠️
- [x] `titulo=`, `**layout_kwargs` e `cores=` em todos os `viz.*`/`plot_*`.
- [x] Tema via `template=` em qualquer gráfico.
- [x] **Tema escuro próprio** — template `dashgusbr_escuro`
  (`template="dashgusbr_escuro"`).
- [x] **Controle de rótulos/legenda** — `mostrar_valores=` e `mostrar_legenda=`.

### 3. Experiência do usuário / desenvolvedor 👤
- [x] Cache em disco, logging, retry/backoff, exportação (`salvar_html`,
  `salvar_imagem`), busca tolerante de time, `resumo_time`, `py.typed`.
- [x] **CLI** — `python -m dashgusbr tabela 2023` (+ `goleadas`, `ranking`,
  `resumo`, `times`, `anos`, `validar`; opções `--fonte` e `--html`).
- [~] Docstrings com exemplos — assinaturas documentadas e galeria como
  referência rápida; página de referência gerada fica para o v2 (docs site).

### 4. Novos gráficos e novas análises 📊
- [x] Corrida pelo título, casa × fora, sequências, forma recente, ranking
  histórico, líderes por temporada, retrospecto por adversário, clássicos,
  estados, fases.
- [x] **Linha do tempo do confronto** — `analytics.evolucao_confronto` +
  `br.plot_confronto_evolucao(a, b)` (saldo acumulado na história).
- [x] **Mapa coroplético por UF** — `viz.mapa_estados` + `br.plot_mapa_estados()`;
  GeoJSON público baixado e cacheado por `data.carregar_geojson_estados()`.
- [x] **Fator "viagem"** — `analytics.fator_viagem` / `br.viagem()`.
- [x] **Inflação/deflação de gols** — `analytics.media_gols_por_decada` /
  `br.gols_por_decada()` (média por década e por era de pontuação).
- [x] **Distribuição de saldos** — `analytics.distribuicao_saldos` +
  `br.plot_saldos()`.

### 5. Dados e infraestrutura 🗄️
- [x] **Validação de dados mais rica** — `schema.relatorio_consistencia` /
  `br.validar()`: gols ≥ 0, resultado × placar, espelhamento dos dois lados,
  pontos × resultado, `total_gols`, datas plausíveis, `id_partida` duplicado.
- [x] Snapshot local (`Brasileirao(fonte="obt.csv")`), retry/timeout.
- [!] **Número de rodada** — bloqueado: depende do ETL (Infra-Brasileirao)
  publicar a coluna. Quando existir, `evolucao_pontos` troca a ordem por data
  pela rodada oficial. → v2, tema "contrato com o ETL".

### 6. Qualidade, testes e documentação ✅
- [x] 118 testes offline + 2 smoke de rede; lint (`ruff`) no CI.
- [x] **Galeria de exemplos** — `examples/demo.py` gera
  `galeria_dashgusbr.html` com todos os gráficos e a chamada de cada um.
- [ ] Documentação publicada (site) — movido para o v2 como item principal.

---

## Pós-v1 — entregue em set/2026 📦

Trabalho fechado depois do v1, antes do v2 começar. O dashboard por time saiu
na **v0.4.0**; a comparação entre clubes está pronta e sai na próxima.

### Dashboard por time 🧩
- [x] **`br.dashboard("Palmeiras")`** — uma única `go.Figure` com os painéis
  padrão do clube: indicadores da campanha (com variação sobre a temporada
  anterior), evolução de pontos, casa × fora, classificação com o time
  destacado, aproveitamento por adversário, últimos jogos e histórico.
- [x] **Campeonato atual por padrão** — `analytics.ultima_temporada(df, time)`
  resolve o recorte pela base, não pelo relógio; `ano_campeonato=2020` troca a
  temporada mantendo os mesmos painéis (duas temporadas ficam comparáveis).
- [x] **Personalização em cima do padrão** — `incluir=`/`remover=`/`paineis=`,
  `colunas=`, `altura_linha=`; `incluir=` aceita figuras prontas e funções
  `(ctx) -> go.Figure`. Catálogo em `br.paineis()` (extras: `posicao`,
  `sequencias`, `placares`, `saldos`, `adversarios_historico`) e
  `dashboard.registrar_painel()` para publicar painéis próprios pelo nome.
- [x] **Motor de composição** (`dashgusbr.dashboard`) — grade de subplots que
  remapeia eixos, anotações, formas e barras de cor de cada figura para a
  célula certa, com mini-legenda por painel e reserva de margem/calha para os
  nomes de clube dos gráficos de barras horizontais.
- [x] **Comparação entre clubes** — `br.dashboard(["Palmeiras",
  "Corinthians"])`: até quatro clubes no mesmo padrão, com painéis
  compartilhados (`unico`) e *small multiples* (`repetir`), cor fixa por
  clube e recorte na última temporada comum a todos.
- [x] **Novas figuras de apoio** — `viz.forma`, `viz.sequencias`,
  `viz.historico` com várias campanhas e `destaque=` (um time ou vários) em
  `viz.classificacao`/`br.plot_tabela`.
- [x] **Cobertura** — 184 testes offline (66 só do dashboard); notebook e
  galeria atualizados com a seção do dashboard.
- [ ] 🟡 ⚡ **Conferência visual** — a geometria é validada por teste
  (domínios, alturas, calhas), mas falta uma revisão a olho e um teste de
  imagem (`kaleido` não está instalado no ambiente de dev).

---

## Roadmap v2 — PROPOSTA 🚀

Com a base analítica madura, o v2 muda o foco: **publicar** (docs, PyPI),
**aprofundar** (análises que contam histórias, não só agregam) e **endurecer o
contrato de dados** com o ETL.

### 1. Documentação e alcance 📚
- [ ] 🔴 ⚙️ **Site de documentação** — MkDocs Material + mkdocstrings,
  publicado no GitHub Pages por CI: API de referência gerada das docstrings,
  tutorial "do zero ao gráfico" e a galeria hospedada como página.
- [ ] 🔴 ⚡ **Doctests no CI** — transformar os `Examples` das docstrings em
  testes executáveis (`pytest --doctest-modules` sobre funções puras).
- [ ] 🟡 ⚡ **Galeria como artefato de CI** — regenerar `galeria_dashgusbr.html`
  no workflow (marker `rede`) e anexar ao release; a galeria nunca desatualiza.
  Ela já abre com os dois dashboards (padrão e personalizado).
- [ ] 🟢 ⚙️ **README bilíngue** — versão curta em inglês para a página do PyPI.

### 2. Contrato de dados com o ETL 🤝
- [ ] 🔴 ⚡ **Issue no Infra-Brasileirao: coluna `rodada`** — destrava a
  evolução por rodada oficial, tabelas "na rodada X" e análises de recorte
  (ver 3.2). Do lado da lib: usar a coluna quando presente, manter a ordem
  por data como fallback.
- [ ] 🟡 ⚙️ **Versão do schema na OBT** — combinar com o ETL um manifesto
  (versão + data de geração); a lib loga divergências e o CI roda um teste de
  contrato semanal (cron) contra a OBT real.
- [ ] 🟡 ⚡ **`br.validar()` no pipeline** — o ETL passa a rodar o relatório de
  consistência antes de publicar (a lib já exporta a checagem; falta o hook lá).
- [ ] 🟢 ⚙️ **Snapshot congelado versionado** — publicar um parquet comprimido
  por release para exemplos/notebooks 100% reprodutíveis offline.

### 3. Análises que contam histórias 📖
- [ ] 🟡 🏗️ **Rating Elo histórico** — força relativa dos clubes jogo a jogo
  desde 1971 (`analytics.elo` + `br.plot_elo(["Flamengo", "Palmeiras"])`);
  é a métrica que compara eras melhor que pontos ou aproveitamento.
- [ ] 🟡 ⚙️ **Comparador de campanhas** — sobrepor a evolução de pontos de
  campanhas de anos diferentes (`br.plot_comparar_campanhas([("Palmeiras", 2023),
  ("Flamengo", 2019)])`) normalizando pelo nº de jogos.
- [ ] 🟡 ⚙️ **Quantos pontos dão o quê** — distribuição histórica de pontos do
  campeão, do G4 e do Z4 na era dos 20 clubes; responde "68 pontos dá título?".
- [ ] 🟢 ⚙️ **Painel de eras** — um `br.plot_eras()` comparando as fases do
  campeonato (2 pts × 3 pts, nº de clubes, mata-mata × pontos corridos) em
  small multiples.
- [ ] 🟢 ⚙️ **Zebras e favoritismo** — com o Elo pronto: frequência de upsets,
  maiores zebras da história.
- [ ] 🟢 ⚡ **Cauda de cores restante** — pesquisar a identidade visual dos 47
  clubes ainda no fallback (fontes: escudos históricos, federações estaduais).

### 4. Da biblioteca ao produto 📱
- [ ] 🟡 🏗️ **App pronto** — `dashgusbr[app]` instala um dashboard Streamlit
  (`python -m dashgusbr app`): seletor de temporada/clube, todos os gráficos.
  A arquitetura em camadas puras já foi desenhada para isso — e o
  `dashboard_time` do pós-v1 já entrega a tela principal pronta; sobra o
  chrome (seletores, abas, cache do Streamlit).
- [ ] 🟡 ⚡ **Dashboard no CLI** — `python -m dashgusbr dashboard Palmeiras
  --ano 2020 --html palmeiras.html`: o painel completo sem escrever Python.
- [ ] 🟢 ⚙️ **Outros dashboards prontos** — `dashboard_temporada(ano)`
  reusando o mesmo motor de composição e o mesmo catálogo de painéis (a
  comparação entre clubes já saiu no pós-v1).
- [ ] 🟢 ⚡ **Comparar campanhas de anos diferentes** — hoje a comparação usa
  uma temporada só para todos; falta o recorte `[("Palmeiras", 2023),
  ("Flamengo", 2019)]` (ver 3.2, "comparador de campanhas").
- [ ] 🟢 ⚙️ **Animação da corrida do título** — frames por rodada (depende da
  coluna `rodada`) no `plot_corrida_titulo(animado=True)`.
- [ ] 🟢 ⚡ **Presets de exportação** — `salvar_imagem(fig, preset="twitter")`
  (dimensões/escala prontas para redes e slides).

### 5. Qualidade contínua 🧪
- [ ] 🟡 ⚡ **Cobertura no CI** — `pytest-cov` com relatório e badge no README.
- [ ] 🟡 ⚙️ **mypy estrito** — a base já publica `py.typed`; falta fechar os
  hints internos e ligar `mypy --strict` no CI.
- [ ] 🟢 ⚡ **Validação de contraste da paleta no CI** — teste automático de
  que os slots categóricos seguem seguros (deltas de luminância/matiz), para
  ninguém quebrar a acessibilidade num ajuste de cor.
- [ ] 🟢 ⚙️ **Benchmark leve** — `lideres_temporada`/`ranking_historico`
  recalculam a classificação ano a ano; medir e, se necessário, cachear o
  formato longo por instância.

### Ordem de ataque sugerida

1. **Docs site + doctests** (1) — o maior retorno por esforço: torna o que já
   existe visível e confiável.
2. **Issue da rodada + teste de contrato** (2) — destrava metade das análises
   novas e protege a lib de mudanças silenciosas na OBT.
3. **Elo histórico** (3) — a análise mais diferenciada do v2; puxa zebras e
   favoritismo de graça.
4. **App Streamlit** (4) — quando docs e análises estiverem estáveis, é a
   vitrine natural do projeto.

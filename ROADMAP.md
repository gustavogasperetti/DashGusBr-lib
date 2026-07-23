# Roadmap de melhorias — dashgusbr

Lista viva de melhorias possíveis para a biblioteca, agrupadas por tema.
Cada item traz **o quê**, **por quê** e um **esboço de como** implementar.

> **Legenda**
> Prioridade: 🔴 alta · 🟡 média · 🟢 baixa
> Esforço: ⚡ pequeno · ⚙️ médio · 🏗️ grande
> Status: `[ ]` não iniciado · `[~]` em andamento · `[x]` concluído

Colunas disponíveis na OBT (base para novas contas):
`id_partida, ano_campeonato, data, mandante, visitante, estado_mandante,
estado_visitante, gols_mandante, gols_visitante, resultado_mandante,
resultado_visitante, placar_status, fase, tipo_fase, is_mata_mata,
is_classico_estadual, total_gols, saldo_gols_mandante, saldo_gols_visitante,
pontos_mandante, pontos_visitante`.

---

## 1. Cores oficiais por time 🎨

Cada time passa a ter uma **cor principal** própria (ex.: Palmeiras → verde,
Flamengo → vermelho, Cruzeiro → azul), usada por padrão nos gráficos que
representam times individuais.

- [x] 🔴 ⚙️ **Mapa de cores por time** — novo módulo `_cores_times.py` com um
  dicionário `nome canônico → cor principal (hex)` e, opcionalmente, cor
  secundária. Função `cor_time(nome) -> str` com:
  - normalização robusta (sem acento, caixa baixa, espaços) para casar
    "São Paulo"/"sao paulo"/"SÃO PAULO";
  - **aliases** ("Athletico-PR", "Atlético-PR", "CAP"; "Atlético-MG", "Galo"…);
  - **fallback** para a paleta categórica atual quando o time não estiver no
    mapa (nunca quebrar).

  ```python
  # esboço de src/dashgusbr/_cores_times.py
  CORES_TIMES = {
      "palmeiras":     "#006437",  # verde
      "flamengo":      "#c52613",  # vermelho
      "corinthians":   "#111111",  # preto
      "sao paulo":     "#c8102e",  # vermelho
      "gremio":        "#0d80bf",  # azul
      "internacional": "#c40000",  # vermelho
      "cruzeiro":      "#1e3a8a",  # azul
      "atletico-mg":   "#111111",  # preto
      "vasco da gama": "#111111",  # preto
      "santos":        "#111111",  # preto/branco
      "fluminense":    "#7a1f2b",  # grená
      "botafogo":      "#111111",  # preto
      "bahia":         "#1f6fd6",  # azul
      "fortaleza":     "#1f4fa0",  # azul
      # ... completar com os demais times da base (br.times())
  }
  ```

- [x] 🔴 ⚡ **Usar as cores nos plots por time** — em `viz.evolucao`,
  `viz.historico` e `viz.confronto`, quando `usar_cores_times=True`, pintar
  cada série com `cor_time(...)`. Manter o comportamento atual como padrão
  (`False`) para não quebrar nada.
- [x] 🟡 ⚡ **Expor no `Brasileirao`** — parâmetro `cores_times: bool = False`
  em `plot_evolucao`, `plot_historico`, `plot_confronto` (+ `plot_corrida_titulo`).
- [x] 🟡 ⚡ **API pública da cor** — expor `from dashgusbr import cor_time` para
  o usuário reaproveitar as cores em gráficos próprios.
- [ ] 🟢 ⚡ **Contraste/legibilidade** — amarelos já escurecidos no mapa; falta
  cor de texto automática por luminância para rótulos sobre barras escuras.
- [x] 🟢 ⚡ **Acessibilidade** — cores de time **não** são seguras para
  daltonismo (dois times pretos, dois azuis). `cores_times` é **opt-in**,
  cores duplicadas no mesmo gráfico caem na paleta categórica; documentado.
- [ ] 🟢 ⚙️ **Cobertura completa e testes** — ~55 clubes mapeados (todos com
  presença relevante); falta mapear a cauda longa dos 167 times históricos.

---

## 2. Personalização dos gráficos 🛠️

Hoje os métodos `plot_*` retornam um `Figure` mutável (dá para ajustar tudo
depois), mas a API da lib quase não aceita customização na chamada.

- [x] 🔴 ⚡ **`titulo=` nos métodos `plot_*`** — permitir sobrescrever o título
  fixo (ex.: `br.plot_tabela(2023, titulo="Meu título")`).
- [x] 🔴 ⚙️ **Passar `**layout_kwargs`** para as funções `viz.*` e métodos
  `plot_*`, repassados a `fig.update_layout(...)` (largura, altura, fonte,
  fundo, etc.) sem o usuário precisar pós-processar.
- [x] 🟡 ⚙️ **Paleta customizável** — aceitar `cores=[...]` nas funções `viz.*`
  em vez de constantes cravadas no traço; hoje trocar a paleta exige
  `fig.update_traces(...)`.
- [x] 🟡 ⚡ **Escolher tema** — via `layout_kwargs`: `template="plotly_dark"`
  funciona em qualquer `plot_*`/`viz.*` (documentado no README).
- [ ] 🟢 ⚙️ **Tema escuro** — variante dark do template em `_theme.py`
  (`registrar_tema(modo="dark")`).
- [ ] 🟢 ⚡ **Controle de rótulos/hover** — flags como `mostrar_valores`,
  `mostrar_legenda`, `hover=...` para ligar/desligar detalhes.

---

## 3. Experiência do usuário / desenvolvedor 👤

- [x] 🔴 ⚙️ **Cache em disco** — CSV baixado fica em `~/.dashgusbr/cache` com
  validade configurável (`validade_horas`); fallback para a cópia local quando
  a rede está fora; `limpar_cache(disco=True)`.
- [x] 🔴 ⚡ **Logging** no download da OBT (logger `dashgusbr`: download,
  tentativas, cache usado, fallback) + retry com backoff e timeout.
- [x] 🟡 ⚙️ **Exportação facilitada** — helpers `salvar_html(fig, caminho)` e
  `salvar_imagem(fig, caminho)` (png/svg via kaleido), com kaleido em
  `optional-dependencies` (`pip install dashgusbr[imagem]`).
- [x] 🟡 ⚡ **Busca de time tolerante** — nomes resolvem ignorando
  caixa/acento/hífen ("gremio" → "Grêmio"); aproximação vaga continua sendo
  erro com sugestões (nunca palpite silencioso).
- [x] 🟡 ⚙️ **`resumo_time(time)`** — um dict/tabela com o "cartão" do clube
  (temporadas disputadas, melhor/pior campanha, aproveitamento médio,
  maior goleada a favor/contra).
- [ ] 🟢 ⚙️ **CLI** — `python -m dashgusbr tabela 2023` para gerar tabela/gráfico
  pelo terminal.
- [x] 🟢 ⚙️ **`py.typed`** — marcador publicado; hints já cobrem as assinaturas
  públicas (checagem estática estrita fica para depois).
- [ ] 🟢 ⚡ **Docstrings com exemplos executáveis** e página de referência.

---

## 4. Novos gráficos e novas análises 📊

Novas contas aproveitando colunas ainda subutilizadas (`estado_*`,
`is_mata_mata`, `is_classico_estadual`, `fase`, `saldo_gols_*`).

### 4.1 Times e temporadas
- [x] 🔴 ⚙️ **Corrida pelo título** — `analytics.corrida_titulo` +
  `br.plot_corrida_titulo(ano, n=4, cores_times=True)`.
- [x] 🟡 ⚙️ **Desempenho casa × fora por time** — `analytics.casa_fora` +
  `br.plot_casa_fora` (V/E/D agrupados + aproveitamento por local).
- [x] 🟡 ⚙️ **Sequências (streaks)** — `analytics.sequencias`: maiores
  sequências de vitórias, invencibilidade, derrotas e jejum (com período).
- [x] 🟡 ⚙️ **Forma recente** — `analytics.forma_recente` / `br.forma(time, n)`:
  últimos N jogos + aproveitamento do período em `attrs`.
- [x] 🟢 ⚙️ **Ranking histórico geral** — `analytics.ranking_historico` /
  `br.ranking()`: tabela all-time com aproveitamento normalizado entre eras.
- [x] 🟢 ⚙️ **Líderes por temporada** — `analytics.lideres_temporada` +
  `br.plot_lideres()` (ressalva documentada: líder ≠ campeão até 2002, a base
  não decide o mata-mata final).

### 4.2 Confrontos e clássicos
- [x] 🟡 ⚙️ **Retrospecto contra cada adversário** — `analytics.desempenho_contra`
  + `br.plot_contra(time, top=15)` (aproveitamento, V/E/D, saldo por rival).
- [x] 🟡 ⚙️ **Análise de clássicos** — `analytics.comparar_classicos` /
  `br.classicos()`: clássicos × demais jogos (gols, empates, fator casa).
- [ ] 🟢 ⚙️ **Linha do tempo de um confronto** — saldo acumulado do confronto
  direto ao longo dos anos (quem "abriu vantagem" na história).

### 4.3 Geografia (colunas `estado_mandante` / `estado_visitante`)
- [x] 🟡 ⚙️ **Distribuição por estado/UF** — `analytics.estatisticas_estados` +
  `br.plot_estados()` (jogos, gols, clubes e fator casa por UF).
- [ ] 🟢 🏗️ **Mapa coroplético** — intensidade por UF (participações, gols,
  títulos). Requer geojson dos estados.
- [ ] 🟢 ⚙️ **Fator "viagem"** — desempenho do visitante quando joga fora do seu
  estado vs. dentro (proxy de distância).

### 4.4 Campeonato (visão macro)
- [x] 🟡 ⚙️ **Fases e mata-mata** — `analytics.comparar_fases` / `br.fases()`:
  gols, empates e fator casa em mata-mata × fase de pontos.
- [ ] 🟢 ⚙️ **Inflação/deflação de gols** — média de gols por época/formato,
  destacando mudanças de regulamento.
- [ ] 🟢 ⚙️ **Distribuição de saldos** — histograma de saldo de gols por jogo.

---

## 5. Dados e infraestrutura 🗄️

- [ ] 🟡 ⚙️ **Validação de dados mais rica** — checagens de consistência
  (gols ≥ 0, resultados coerentes com o placar, datas plausíveis) com relatório.
- [x] 🟡 ⚡ **Congelar/anexar snapshot** — `Brasileirao(fonte="caminho/obt.csv")`
  já aceita CSV local no mesmo schema (reprodutibilidade de exemplos/testes).
- [ ] 🟢 ⚙️ **Suporte a número de rodada** — se o ETL passar a publicar a rodada,
  usar em `evolucao_pontos` no lugar da ordem por data.
- [x] 🟢 ⚡ **Retry/timeout no download** — 3 tentativas com backoff e timeout
  de 30s na carga remota.

---

## 6. Qualidade, testes e documentação ✅

- [x] 🔴 ⚡ **Testes das novas features** — cores por time, novos plots, novos
  parâmetros de customização, cache em disco e exportação (95 testes).
- [x] 🟡 ⚡ **Lint no CI** — `ruff check` como etapa do workflow de CI.
- [ ] 🟡 ⚙️ **Galeria de exemplos** — notebook/HTML mostrando cada gráfico
  (evoluir o `examples/demo.py`).
- [ ] 🟢 ⚙️ **Documentação publicada** — site (MkDocs/Sphinx) com API e tutoriais.
- [x] 🟢 ⚡ **Seção "Como personalizar" no README** — exemplos de `update_layout`,
  `update_traces`, exportação e cores por time.

---

### Sugestão de ordem de ataque

~~1–3 concluídos~~ (cores por time, personalização, novas análises, cache em
disco e exportação). Próximos candidatos, conforme interesse:

1. **Galeria de exemplos** (seção 6) — mostrar os novos gráficos.
2. **Mapa coroplético por UF** (seção 4.3) e **linha do tempo do confronto**
   (seção 4.2).
3. **Tema escuro** próprio e **CLI** (seções 2 e 3).

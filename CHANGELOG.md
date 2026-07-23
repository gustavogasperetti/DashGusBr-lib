# Changelog

Todas as mudanças relevantes deste projeto são documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

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

## [0.1.0] - 2026-07-22

### Adicionado
- Cliente `Brasileirao` para consumo da OBT do projeto Infra-Brasileirao.
- Camadas puras `data`, `analytics` e `viz` (gráficos Plotly).
- Módulos de apoio `config`, `schema` e tema visual.
- Suíte de testes (`pytest`) e exemplo de uso em `examples/demo.py`.

[Não lançado]: https://github.com/gustavogasperetti/DashGusBr-lib/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/gustavogasperetti/DashGusBr-lib/releases/tag/v0.1.0

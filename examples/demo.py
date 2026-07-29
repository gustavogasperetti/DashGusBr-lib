"""Galeria da dashgusbr: gera um HTML com TODOS os gráficos da biblioteca.

Uso:
    python examples/demo.py [ano]

Baixa a OBT real (GitHub, com fallback para Sheets) e grava
``galeria_dashgusbr.html`` no diretório atual. Cada figura vem acompanhada
da chamada que a gerou — a galeria é também a referência rápida da API.
"""

import html
import sys

from dashgusbr import Brasileirao
from dashgusbr._theme import TEMA_ESCURO


def main() -> None:
    ano = int(sys.argv[1]) if len(sys.argv) > 1 else 2023

    br = Brasileirao()
    print(f"Base carregada: {len(br.partidas())} partidas, {br.anos()[0]}–{br.anos()[-1]}")

    tabela = br.tabela(ano)
    g4 = list(tabela.head(4)["time"])
    a, b = g4[0], g4[1]
    print(f"G4 de {ano}: {', '.join(g4)}")

    # (título da seção, código exibido, figura)
    galeria = [
        (
            "Classificação",
            f"br.plot_tabela({ano})",
            br.plot_tabela(ano),
        ),
        (
            "Corrida pelo título (cores oficiais dos clubes)",
            f"br.plot_corrida_titulo({ano}, n=4, cores_times=True)",
            br.plot_corrida_titulo(ano, n=4, cores_times=True),
        ),
        (
            "Evolução de pontos",
            f"br.plot_evolucao({g4[:2]!r}, {ano})",
            br.plot_evolucao(g4[:2], ano),
        ),
        (
            "Confronto direto",
            f"br.plot_confronto({a!r}, {b!r}, cores_times=True)",
            br.plot_confronto(a, b, cores_times=True),
        ),
        (
            "Linha do tempo do confronto",
            f"br.plot_confronto_evolucao({a!r}, {b!r}, cores_times=True)",
            br.plot_confronto_evolucao(a, b, cores_times=True),
        ),
        (
            "Histórico de um clube",
            f"br.plot_historico({a!r})",
            br.plot_historico(a),
        ),
        (
            "Casa × fora",
            f"br.plot_casa_fora({a!r})",
            br.plot_casa_fora(a),
        ),
        (
            "Aproveitamento por adversário",
            f"br.plot_contra({a!r})",
            br.plot_contra(a),
        ),
        (
            "Média de gols por temporada",
            "br.plot_gols_por_temporada()",
            br.plot_gols_por_temporada(),
        ),
        (
            "Fator casa na história",
            "br.plot_mandante_visitante()",
            br.plot_mandante_visitante(),
        ),
        (
            "Distribuição de placares",
            "br.plot_placares()",
            br.plot_placares(),
        ),
        (
            "Distribuição de saldos por jogo",
            "br.plot_saldos()",
            br.plot_saldos(),
        ),
        (
            "Jogos por estado",
            "br.plot_estados()",
            br.plot_estados(),
        ),
        (
            "Líderes dos pontos corridos",
            "br.plot_lideres()",
            br.plot_lideres(),
        ),
        (
            "Tema escuro",
            f'br.plot_tabela({ano}, template="{TEMA_ESCURO}")',
            br.plot_tabela(ano, template=TEMA_ESCURO),
        ),
    ]

    try:
        galeria.insert(
            13,
            (
                "Mapa por estado (coroplético)",
                "br.plot_mapa_estados()",
                br.plot_mapa_estados(),
            ),
        )
    except Exception as exc:  # geojson requer internet na primeira vez
        print(f"Mapa por UF pulado (GeoJSON indisponível: {exc})")

    destino = "galeria_dashgusbr.html"
    with open(destino, "w", encoding="utf-8") as saida:
        saida.write(
            "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
            f"<title>dashgusbr — galeria ({ano})</title>"
            "<style>body{font-family:system-ui,sans-serif;max-width:1080px;"
            "margin:0 auto;padding:24px;color:#0b0b0b;background:#fcfcfb}"
            "h1{font-size:1.6rem}h2{font-size:1.15rem;margin:2.5rem 0 .25rem}"
            "code{background:#f0efe9;padding:2px 6px;border-radius:4px;"
            "font-size:.85rem}nav a{margin-right:.75rem;font-size:.85rem}"
            "</style></head><body>"
            "<h1>dashgusbr — galeria de gráficos</h1>"
            "<p>Todos os gráficos prontos da biblioteca, com a chamada que gera "
            "cada um. Figuras são interativas (Plotly).</p><nav>"
        )
        for i, (titulo, _, _) in enumerate(galeria):
            saida.write(f"<a href='#g{i}'>{html.escape(titulo)}</a>")
        saida.write("</nav>")
        for i, (titulo, codigo, fig) in enumerate(galeria):
            saida.write(
                f"<h2 id='g{i}'>{html.escape(titulo)}</h2>"
                f"<p><code>{html.escape(codigo)}</code></p>"
            )
            saida.write(fig.to_html(full_html=False, include_plotlyjs=(i == 0)))
        saida.write("</body></html>")
    print(f"Galeria gravada em {destino} ({len(galeria)} gráficos)")


if __name__ == "__main__":
    main()

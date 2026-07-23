"""Demonstração da dashgusbr: gera um relatório HTML com os gráficos do MVP.

Uso:
    python examples/demo.py [ano]

Baixa a OBT real (GitHub, com fallback para Sheets) e grava
``demo_brasileirao.html`` no diretório atual.
"""

import sys

from dashgusbr import Brasileirao


def main() -> None:
    ano = int(sys.argv[1]) if len(sys.argv) > 1 else 2023

    br = Brasileirao()
    print(f"Base carregada: {len(br.partidas())} partidas, {br.anos()[0]}–{br.anos()[-1]}")

    tabela = br.tabela(ano)
    lideres = list(tabela.head(4)["time"])
    print(f"G4 de {ano}: {', '.join(lideres)}")

    figuras = [
        br.plot_tabela(ano),
        br.plot_evolucao(lideres, ano),
        br.plot_confronto(lideres[0], lideres[1]),
        br.plot_historico(lideres[0]),
        br.plot_gols_por_temporada(),
        br.plot_mandante_visitante(),
        br.plot_placares(),
    ]

    destino = "demo_brasileirao.html"
    with open(destino, "w", encoding="utf-8") as saida:
        saida.write(
            f"<html><head><meta charset='utf-8'>"
            f"<title>dashgusbr — {ano}</title></head><body>"
        )
        for i, fig in enumerate(figuras):
            saida.write(fig.to_html(full_html=False, include_plotlyjs=(i == 0)))
        saida.write("</body></html>")
    print(f"Relatório gravado em {destino}")


if __name__ == "__main__":
    main()

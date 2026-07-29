"""CLI da dashgusbr: consultas rápidas pelo terminal.

Uso::

    python -m dashgusbr tabela 2023
    python -m dashgusbr tabela 2023 --html tabela.html
    python -m dashgusbr goleadas 10
    python -m dashgusbr ranking --min-temporadas 10
    python -m dashgusbr resumo Cruzeiro
    python -m dashgusbr times 2023
    python -m dashgusbr anos
    python -m dashgusbr validar

``--fonte`` aceita ``auto`` (padrão), ``github``, ``sheets`` ou o caminho de
um CSV local no schema da OBT — útil para trabalhar offline/reprodutível.
"""

from __future__ import annotations

import argparse
import sys

from .client import Brasileirao
from .export import salvar_html


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dashgusbr",
        description="Consultas rápidas ao histórico do Brasileirão (OBT).",
    )
    parser.add_argument(
        "--fonte",
        default="auto",
        help="auto (padrão), github, sheets ou caminho de um CSV local",
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    p_tabela = sub.add_parser("tabela", help="classificação de uma temporada")
    p_tabela.add_argument("ano", type=int)
    p_tabela.add_argument(
        "--html", metavar="ARQUIVO", help="salva o gráfico da tabela em HTML"
    )

    p_goleadas = sub.add_parser("goleadas", help="maiores goleadas da história")
    p_goleadas.add_argument("n", type=int, nargs="?", default=10)

    p_ranking = sub.add_parser("ranking", help="tabela histórica geral")
    p_ranking.add_argument("--min-temporadas", type=int, default=1)
    p_ranking.add_argument("--top", type=int, default=20)

    p_resumo = sub.add_parser("resumo", help="cartão-resumo de um clube")
    p_resumo.add_argument("time")

    p_times = sub.add_parser("times", help="times da base (ou de uma temporada)")
    p_times.add_argument("ano", type=int, nargs="?", default=None)

    sub.add_parser("anos", help="temporadas disponíveis na base")
    sub.add_parser("validar", help="relatório de consistência dos dados")

    return parser


def main(argv: "list[str] | None" = None) -> int:
    args = _construir_parser().parse_args(argv)
    br = Brasileirao(fonte=args.fonte)

    if args.comando == "tabela":
        print(br.tabela(args.ano).to_string(index=False))
        if args.html:
            destino = salvar_html(br.plot_tabela(args.ano), args.html)
            print(f"\nGráfico salvo em {destino}")
    elif args.comando == "goleadas":
        print(br.goleadas(args.n).to_string(index=False))
    elif args.comando == "ranking":
        tabela = br.ranking(min_temporadas=args.min_temporadas).head(args.top)
        print(tabela.to_string(index=False))
    elif args.comando == "resumo":
        for chave, valor in br.resumo(args.time).items():
            print(f"{chave}: {valor}")
    elif args.comando == "times":
        for time in br.times(ano=args.ano):
            print(time)
    elif args.comando == "anos":
        anos = br.anos()
        print(f"{len(anos)} temporadas: {anos[0]}–{anos[-1]}")
    elif args.comando == "validar":
        relatorio = br.validar()
        print(relatorio.to_string(index=False))
        if relatorio["problemas"].sum() > 0:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

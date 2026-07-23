"""Cores oficiais (principais) dos clubes do Brasileirão.

Mapa opt-in usado pelos gráficos por time (``usar_cores_times=True``):
cada clube é pintado com sua cor de identidade (Palmeiras → verde,
Flamengo → vermelho...). Times fora do mapa caem na paleta categórica
padrão — a função nunca falha por time desconhecido.

Atenção (acessibilidade): cores de clube NÃO são seguras para daltonismo
(vários clubes pretos, vários vermelhos). Por isso o recurso é opt-in e a
paleta padrão validada de :mod:`dashgusbr._theme` continua sendo o default.
"""

from __future__ import annotations

import unicodedata
from typing import Iterable, Optional

from ._theme import CORES_CATEGORICAS

# Chaves normalizadas (sem acento, caixa baixa, sem hífen): ver _normalizar.
# Cores escolhidas pela identidade visual predominante de cada clube, com
# ajuste de contraste para fundo claro (amarelos escurecidos, nunca #fff).
CORES_TIMES = {
    # Série A / grandes
    "flamengo": "#c52613",  # vermelho rubro-negro
    "sao paulo": "#c8102e",  # vermelho tricolor
    "corinthians": "#1b1b1b",  # preto alvinegro
    "atletico mineiro": "#1b1b1b",  # preto alvinegro
    "internacional": "#e5050f",  # vermelho colorado
    "santos": "#1b1b1b",  # preto alvinegro
    "gremio": "#0d80bf",  # azul celeste
    "fluminense": "#7a1f2b",  # grená tricolor
    "palmeiras": "#006437",  # verde alviverde
    "cruzeiro": "#0033a0",  # azul celeste
    "botafogo": "#1b1b1b",  # preto alvinegro
    "vasco": "#1b1b1b",  # preto cruzmaltino
    "athletico paranaense": "#c8102e",  # vermelho rubro-negro
    "bahia": "#005ca9",  # azul tricolor
    "goias": "#00693e",  # verde esmeraldino
    "coritiba": "#005953",  # verde coxa
    "vitoria": "#e4032e",  # vermelho rubro-negro
    "sport": "#c8161d",  # vermelho rubro-negro
    "portuguesa": "#046a38",  # verde rubro-verde
    "guarani": "#006b3f",  # verde bugre
    "ponte preta": "#1b1b1b",  # preto alvinegro
    "nautico": "#a6001a",  # vermelho alvirrubro
    "ceara": "#1b1b1b",  # preto alvinegro
    "juventude": "#009344",  # verde papo
    "fortaleza": "#1f4fa0",  # azul tricolor
    "figueirense": "#1b1b1b",  # preto alvinegro
    "america mineiro": "#008542",  # verde coelho
    "red bull bragantino": "#d50032",  # vermelho braga
    "santa cruz": "#c00d1e",  # vermelho tricolor
    "parana": "#1c3f94",  # azul paranista
    "paysandu": "#005daa",  # azul papão
    "criciuma": "#d7a000",  # amarelo tigre (escurecido p/ contraste)
    "atletico goianiense": "#ce1126",  # vermelho rubro-negro
    "america rj": "#e4032e",  # vermelho
    "avai": "#005baa",  # azul leão
    "chapecoense": "#009846",  # verde chape
    "remo": "#10316b",  # azul marinho
    "america rn": "#ce181e",  # vermelho mecão
    "sao caetano": "#00539f",  # azul azulão
    "csa": "#005ca9",  # azul azulão
    "joinville": "#d0111b",  # vermelho jec
    "bangu": "#e4032e",  # vermelho alvirrubro
    "crb": "#cf2029",  # vermelho galo
    "cuiaba": "#c39738",  # dourado
    "botafogo sp": "#d20a11",  # vermelho pantera
    "abc": "#1b1b1b",  # preto alvinegro
    "sampaio correa": "#cfa000",  # amarelo tricolor (escurecido)
    "vila nova": "#c8102e",  # vermelho tigre
    "londrina": "#00539f",  # azul tubarão
    "mirassol": "#f9b000",  # amarelo leão
    "santo andre": "#005baa",  # azul ramalhão
    "brasil de pelotas": "#c8161d",  # vermelho xavante
    "operario ferroviario": "#1b1b1b",  # preto fantasma
    "ituano": "#c8102e",  # vermelho galo de itu
}

# Apelidos e variações de grafia -> chave canônica (ambos normalizados)
ALIASES = {
    "athletico pr": "athletico paranaense",
    "atletico pr": "athletico paranaense",
    "cap": "athletico paranaense",
    "furacao": "athletico paranaense",
    "atletico mg": "atletico mineiro",
    "galo": "atletico mineiro",
    "atletico go": "atletico goianiense",
    "america mg": "america mineiro",
    "coelho": "america mineiro",
    "vasco da gama": "vasco",
    "bragantino": "red bull bragantino",
    "tricolor paulista": "sao paulo",
    "spfc": "sao paulo",
    "verdao": "palmeiras",
    "mengao": "flamengo",
    "timao": "corinthians",
    "peixe": "santos",
    "imortal": "gremio",
    "raposa": "cruzeiro",
    # "colorado" NÃO é alias do Internacional: existe o clube Colorado-PR na base
}


def _normalizar(nome: str) -> str:
    """Normaliza um nome de time para busca: sem acento, caixa baixa, sem hífen."""
    sem_acento = (
        unicodedata.normalize("NFKD", str(nome))
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    return " ".join(sem_acento.lower().replace("-", " ").replace("_", " ").split())


def cor_time(nome: str, padrao: Optional[str] = None) -> Optional[str]:
    """Cor principal do clube (hex), ou ``padrao`` se não mapeado.

    Aceita variações de acento/caixa/hífen ("Grêmio", "gremio", "GRÊMIO") e
    apelidos comuns ("Atlético-MG", "CAP"). Nunca levanta erro por time
    desconhecido — devolve ``padrao`` (``None`` por default).

    Examples
    --------
    >>> cor_time("Palmeiras")
    '#006437'
    >>> cor_time("Time Inexistente", padrao="#999999")
    '#999999'
    """
    chave = _normalizar(nome)
    chave = ALIASES.get(chave, chave)
    return CORES_TIMES.get(chave, padrao)


def cores_para_times(times: Iterable[str]) -> "list[str]":
    """Uma cor por time, para uso direto como paleta de um gráfico.

    Times mapeados recebem sua cor oficial; não mapeados (e repetições de
    uma cor já usada no mesmo gráfico — ex.: dois clubes pretos) caem nos
    slots da paleta categórica padrão, garantindo séries distinguíveis.
    """
    cores: "list[str]" = []
    usadas: "set[str]" = set()
    reserva = [c for c in CORES_CATEGORICAS]
    for time in times:
        cor = cor_time(time)
        if cor is None or cor in usadas:
            cor = next((c for c in reserva if c not in usadas), None)
            if cor is None:  # paleta esgotada: repete a categórica ciclando
                cor = CORES_CATEGORICAS[len(cores) % len(CORES_CATEGORICAS)]
        cores.append(cor)
        usadas.add(cor)
    return cores

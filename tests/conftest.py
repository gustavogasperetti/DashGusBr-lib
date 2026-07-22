"""Fixtures compartilhadas: uma mini-OBT no formato exato publicado pelo ETL.

Cobre os dois regimes de pontuação (1971: vitória = 2 pontos; 2023: vitória
= 3 pontos) e inclui um jogo de mata-mata que NÃO deve contar para a
classificação. Os nomes de coluna capitalizados, gols como float e booleanos
como texto reproduzem fielmente o CSV da fonte.
"""

import io

import pandas as pd
import pytest

from dashgusbr import schema

CSV_OBT = """\
id_partida,ano_campeonato,Data,Mandante,Visitante,estado_mandante,estado_visitante,gols_mandante,gols_visitante,resultado_mandante,resultado_visitante,placar_status,Fase,tipo_fase,is_mata_mata,is_classico_estadual,total_gols,saldo_gols_mandante,saldo_gols_visitante,pontos_mandante,pontos_visitante
1,1971,1971-08-07,Palmeiras,Santos,SP,SP,2.0,0.0,V,D,NORMAL,1R,Pontos Corridos,False,True,2,2,-2,2,0
2,1971,1971-08-08,Santos,Botafogo,SP,RJ,1.0,1.0,E,E,NORMAL,1R,Pontos Corridos,False,False,2,0,0,1,1
3,1971,1971-08-14,Botafogo,Palmeiras,RJ,SP,0.0,3.0,D,V,NORMAL,2R,Pontos Corridos,False,False,3,-3,3,0,2
4,1971,1971-08-21,Santos,Palmeiras,SP,SP,2.0,1.0,V,D,NORMAL,2R,Pontos Corridos,False,True,3,1,-1,2,0
5,1971,1971-08-22,Botafogo,Santos,RJ,SP,1.0,0.0,V,D,NORMAL,3R,Pontos Corridos,False,False,1,1,-1,2,0
6,1971,1971-08-28,Palmeiras,Botafogo,SP,RJ,1.0,1.0,E,E,NORMAL,3R,Pontos Corridos,False,False,2,0,0,1,1
7,2023,2023-04-15,Palmeiras,Santos,SP,SP,1.0,0.0,V,D,NORMAL,1R,Pontos Corridos,False,True,1,1,-1,3,0
8,2023,2023-04-16,Santos,Botafogo,SP,RJ,2.0,2.0,E,E,NORMAL,1R,Pontos Corridos,False,False,4,0,0,1,1
9,2023,2023-04-22,Botafogo,Palmeiras,RJ,SP,1.0,2.0,D,V,NORMAL,2R,Pontos Corridos,False,False,3,-1,1,0,3
10,2023,2023-04-29,Palmeiras,Botafogo,SP,RJ,0.0,0.0,E,E,NORMAL,3R,Pontos Corridos,False,False,0,0,0,1,1
11,2023,2023-12-03,Palmeiras,Santos,SP,SP,5.0,0.0,V,D,NORMAL,Final,Mata-mata,True,True,5,5,-5,3,0
"""


@pytest.fixture()
def csv_texto() -> str:
    return CSV_OBT


@pytest.fixture()
def obt(csv_texto) -> pd.DataFrame:
    """A mini-OBT já normalizada para o schema canônico."""
    bruto = pd.read_csv(io.StringIO(csv_texto))
    return schema.validar(schema.normalizar(bruto))


@pytest.fixture()
def caminho_csv(tmp_path, csv_texto) -> str:
    """A mini-OBT gravada em disco, para exercitar a carga por caminho local."""
    arquivo = tmp_path / "brasileirao_obt.csv"
    arquivo.write_text(csv_texto, encoding="utf-8")
    return str(arquivo)

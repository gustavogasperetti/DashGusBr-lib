import io

import pandas as pd
import pytest

from dashgusbr import schema


def test_normalizar_renomeia_e_tipa(obt):
    assert "data" in obt.columns and "Data" not in obt.columns
    assert "mandante" in obt.columns and "fase" in obt.columns
    assert pd.api.types.is_datetime64_any_dtype(obt["data"])
    assert str(obt["gols_mandante"].dtype) == "Int64"
    assert obt["is_mata_mata"].dtype == bool
    assert obt["is_classico_estadual"].dtype == bool


def test_normalizar_converte_booleanos_texto(obt):
    assert obt.loc[obt["id_partida"] == 11, "is_mata_mata"].iloc[0]
    assert not obt.loc[obt["id_partida"] == 1, "is_mata_mata"].iloc[0]


def test_normalizar_remove_bom():
    bruto = pd.read_csv(io.StringIO("﻿id_partida,ano_campeonato\n1,2023"))
    normalizado = schema.normalizar(bruto)
    assert "id_partida" in normalizado.columns


def test_validar_aponta_colunas_faltantes(obt):
    incompleto = obt.drop(columns=["pontos_mandante", "tipo_fase"])
    with pytest.raises(schema.SchemaInvalidoError, match="pontos_mandante"):
        schema.validar(incompleto)


def test_validar_retorna_df_valido(obt):
    assert schema.validar(obt) is obt

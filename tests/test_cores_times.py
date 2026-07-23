from dashgusbr import cor_time, cores_para_times
from dashgusbr._cores_times import _normalizar
from dashgusbr._theme import CORES_CATEGORICAS


def test_cor_time_nome_exato():
    assert cor_time("Palmeiras") == "#006437"
    assert cor_time("Flamengo") == "#c52613"


def test_cor_time_tolerante_a_caixa_acento_e_hifen():
    assert cor_time("palmeiras") == "#006437"
    assert cor_time("GRÊMIO") == cor_time("gremio") == "#0d80bf"
    assert cor_time("São Paulo") == cor_time("sao paulo")


def test_cor_time_aliases():
    assert cor_time("Atlético-MG") == cor_time("Atlético Mineiro")
    assert cor_time("Athletico-PR") == cor_time("Athletico Paranaense")
    assert cor_time("Vasco da Gama") == cor_time("Vasco")
    assert cor_time("Bragantino") == cor_time("Red Bull Bragantino")


def test_cor_time_desconhecido_usa_padrao_sem_erro():
    assert cor_time("Time Inexistente FC") is None
    assert cor_time("Time Inexistente FC", padrao="#999999") == "#999999"


def test_normalizar():
    assert _normalizar("  Grêmio  Maringá ") == "gremio maringa"
    assert _normalizar("Athletico-PR") == "athletico pr"


def test_cores_para_times_mapeados():
    assert cores_para_times(["Palmeiras", "Flamengo"]) == ["#006437", "#c52613"]


def test_cores_para_times_desconhecido_cai_na_paleta_categorica():
    cores = cores_para_times(["Palmeiras", "Time Inexistente FC"])
    assert cores[0] == "#006437"
    assert cores[1] == CORES_CATEGORICAS[0]


def test_cores_para_times_evita_cor_duplicada_no_mesmo_grafico():
    # Corinthians e Santos são ambos pretos: o segundo cai na categórica
    cores = cores_para_times(["Corinthians", "Santos"])
    assert cores[0] == "#1b1b1b"
    assert cores[1] != "#1b1b1b"
    assert cores[1] in CORES_CATEGORICAS
    assert len(set(cores)) == len(cores)


def test_cores_para_times_muitos_times_sempre_devolve_uma_cor_por_time():
    times = [f"Time {i}" for i in range(20)]
    cores = cores_para_times(times)
    assert len(cores) == 20
    assert all(isinstance(c, str) and c.startswith("#") for c in cores)

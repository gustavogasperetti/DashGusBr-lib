"""Dashboard por time: painéis padrão, recorte de temporada e personalização."""

import plotly.graph_objects as go
import pytest

from dashgusbr import Brasileirao, analytics, dashboard, viz

# ---------------------------------------------------------------------------
# Recorte: campeonato atual × temporada antiga
# ---------------------------------------------------------------------------


def test_ultima_temporada_e_o_campeonato_atual_da_base(obt):
    assert analytics.ultima_temporada(obt) == 2023
    assert analytics.ultima_temporada(obt, "palmeiras") == 2023


def test_ultima_temporada_ignora_quem_nunca_jogou_pontos_corridos(obt):
    with pytest.raises(ValueError, match="não encontrado"):
        analytics.ultima_temporada(obt, "Inexistente FC")


def test_sem_ano_usa_o_campeonato_atual(obt):
    fig = dashboard.dashboard_time(obt, "palmeiras")
    assert fig.layout.title.text == "Palmeiras — Brasileirão 2023"


def test_ano_campeonato_recorta_uma_temporada_antiga(obt):
    fig = dashboard.dashboard_time(obt, "Palmeiras", ano_campeonato=1971)
    assert fig.layout.title.text == "Palmeiras — Brasileirão 1971"
    assert "Temporada 1971" in _anotacoes(fig)


def test_ano_tambem_aceito_como_apelido(obt):
    fig = dashboard.dashboard_time(obt, "Palmeiras", ano=1971)
    assert "1971" in fig.layout.title.text


def test_ano_fora_da_base_e_erro(obt):
    with pytest.raises(ValueError, match="1999"):
        dashboard.dashboard_time(obt, "Palmeiras", 1999)


def test_time_desconhecido_e_erro_com_sugestoes(obt):
    with pytest.raises(ValueError, match="não encontrado"):
        dashboard.dashboard_time(obt, "Coringão")


# ---------------------------------------------------------------------------
# O padrão de painéis
# ---------------------------------------------------------------------------


def _anotacoes(fig) -> str:
    return " | ".join(a.text or "" for a in fig.layout.annotations)


def test_traz_todos_os_paineis_padrao(obt):
    fig = dashboard.dashboard_time(obt, "Palmeiras")
    textos = _anotacoes(fig)
    for esperado in (
        "Pontos acumulados",
        "Casa × fora",
        "Classificação",
        "adversário",
        "Últimos jogos",
        "Aproveitamento por temporada",
    ):
        assert esperado in textos


def test_faixa_de_indicadores_resume_a_campanha(obt):
    fig = dashboard.dashboard_time(obt, "Palmeiras")
    kpis = {t.title.text: t.value for t in fig.data if t.type == "indicator"}
    tabela = analytics.classificacao(obt, 2023)
    linha = tabela[tabela["time"] == "Palmeiras"].iloc[0]
    assert kpis["Posição"] == linha["posicao"]
    assert kpis["Pontos"] == linha["pontos"]
    assert kpis["Vitórias"] == linha["vitorias"]
    assert kpis["Aproveitamento"] == pytest.approx(linha["aproveitamento"])


def test_indicadores_comparam_com_a_temporada_anterior_disputada(obt):
    fig = dashboard.dashboard_time(obt, "Palmeiras")
    posicao = next(
        t for t in fig.data if t.type == "indicator" and t.title.text == "Posição"
    )
    anterior = analytics.classificacao(obt, 1971)
    esperado = anterior[anterior["time"] == "Palmeiras"].iloc[0]["posicao"]
    assert posicao.delta.reference == esperado
    # posição é "menor é melhor": subir no número tem que pintar de ruim
    assert posicao.delta.increasing.color == dashboard.VERMELHO


def test_sem_temporada_anterior_o_indicador_nao_tem_delta(obt):
    fig = dashboard.dashboard_time(obt, "Palmeiras", 1971)
    assert all(t.delta.reference is None for t in fig.data if t.type == "indicator")


def test_uma_unica_figura_com_um_subplot_por_painel(obt):
    fig = dashboard.dashboard_time(obt, "Palmeiras")
    assert isinstance(fig, go.Figure)
    eixos = [k for k in fig.layout.to_plotly_json() if k.startswith("xaxis")]
    assert len(eixos) == 6  # os seis painéis cartesianos do padrão
    assert fig.layout.height > 1000


def test_paineis_nao_se_sobrepoem(obt):
    fig = dashboard.dashboard_time(obt, "Palmeiras")
    layout = fig.layout.to_plotly_json()
    dominios = sorted(
        (layout[k]["domain"], layout[k.replace("yaxis", "xaxis")]["domain"])
        for k in layout
        if k.startswith("yaxis")
    )
    for (y_a, x_a), (y_b, x_b) in zip(dominios, dominios[1:]):
        separados_na_vertical = y_a[1] <= y_b[0] or y_b[1] <= y_a[0]
        separados_na_horizontal = x_a[1] <= x_b[0] or x_b[1] <= x_a[0]
        assert separados_na_vertical or separados_na_horizontal


def test_classificacao_destaca_o_time_do_dashboard(obt):
    fig = dashboard.dashboard_time(obt, "Santos")
    tabela = analytics.classificacao(obt, 2023).sort_values(
        "posicao", ascending=False
    )
    barras = next(
        t
        for t in fig.data
        if t.type == "bar" and isinstance(t.marker.color, (list, tuple))
    )
    destacadas = {
        time
        for time, cor in zip(tabela["time"], barras.marker.color)
        if cor != dashboard.CINZA_NEUTRO
    }
    assert destacadas == {"Santos"}


# ---------------------------------------------------------------------------
# Personalização
# ---------------------------------------------------------------------------


def test_incluir_acrescenta_painel_do_catalogo(obt):
    padrao = dashboard.dashboard_time(obt, "Palmeiras")
    maior = dashboard.dashboard_time(obt, "Palmeiras", incluir=["sequencias"])
    assert "Maiores sequências" in _anotacoes(maior)
    assert maior.layout.height > padrao.layout.height


def test_remover_tira_painel_do_padrao(obt):
    fig = dashboard.dashboard_time(obt, "Palmeiras", remover=["classificacao"])
    assert "Classificação" not in _anotacoes(fig)


def test_remover_painel_ausente_e_erro(obt):
    with pytest.raises(ValueError, match="não está no dashboard"):
        dashboard.dashboard_time(obt, "Palmeiras", remover=["placares"])


def test_painel_inexistente_e_erro_com_o_catalogo(obt):
    with pytest.raises(ValueError, match="não existe"):
        dashboard.dashboard_time(obt, "Palmeiras", incluir=["gols_de_bicicleta"])


def test_paineis_substitui_a_lista_inteira(obt):
    fig = dashboard.dashboard_time(obt, "Palmeiras", paineis=["evolucao"])
    assert len(fig.data) == 1
    assert "Classificação" not in _anotacoes(fig)


def test_aceita_figura_pronta_do_usuario(obt):
    minha = go.Figure(go.Scatter(x=[1, 2], y=[3, 4]))
    fig = dashboard.dashboard_time(
        obt, "Palmeiras", paineis=["evolucao", ("Meu gráfico", minha)]
    )
    assert "<b>Meu gráfico</b>" in _anotacoes(fig)
    assert len(fig.data) == 2


def test_aceita_funcao_que_recebe_o_contexto(obt):
    vistos = {}

    def meu_painel(ctx):
        vistos["time"], vistos["ano"] = ctx.time, ctx.ano
        vistos["jogos_do_time"] = len(ctx.df_time_ano)
        return go.Figure(go.Bar(x=["a"], y=[1]))

    dashboard.dashboard_time(
        obt, "palmeiras", 2023, paineis=[("Painel novo", meu_painel)]
    )
    assert vistos == {"time": "Palmeiras", "ano": 2023, "jogos_do_time": 4}


def test_registrar_painel_publica_no_catalogo(obt):
    dashboard.registrar_painel(
        "so_para_teste",
        lambda ctx: go.Figure(go.Bar(x=[ctx.time], y=[1])),
        titulo="Painel de teste",
        descricao="usado nos testes",
    )
    try:
        assert "so_para_teste" in dashboard.paineis_disponiveis()["painel"].values
        fig = dashboard.dashboard_time(
            obt, "Palmeiras", paineis=["so_para_teste"]
        )
        assert "<b>Painel de teste</b>" in _anotacoes(fig)
    finally:
        del dashboard.PAINEIS["so_para_teste"]


def test_colunas_controla_a_grade(obt):
    uma = dashboard.dashboard_time(obt, "Palmeiras", colunas=1)
    duas = dashboard.dashboard_time(obt, "Palmeiras", colunas=2)
    assert uma.layout.height > duas.layout.height
    assert uma.layout.xaxis.domain == (0.0, 1.0)


def test_colunas_invalida_e_erro(obt):
    with pytest.raises(ValueError, match="colunas"):
        dashboard.dashboard_time(obt, "Palmeiras", colunas=4)


def test_layout_kwargs_tem_a_ultima_palavra(obt):
    fig = dashboard.dashboard_time(obt, "Palmeiras", height=900, width=1000)
    assert (fig.layout.height, fig.layout.width) == (900, 1000)


def test_titulo_e_subtitulo_personalizados(obt):
    fig = dashboard.dashboard_time(
        obt, "Palmeiras", titulo="Meu painel", subtitulo="minha fonte"
    )
    assert fig.layout.title.text == "Meu painel"
    assert "minha fonte" in _anotacoes(fig)


def test_tema_escuro_e_repassado(obt):
    fig = dashboard.dashboard_time(obt, "Palmeiras", template="dashgusbr_escuro")
    assert fig.layout.template.layout.paper_bgcolor == "#16181d"


def test_cores_times_pinta_com_a_cor_do_clube(obt):
    fig = dashboard.dashboard_time(
        obt, "Palmeiras", paineis=["evolucao"], cores_times=True
    )
    assert fig.data[0].line.color == "#006437"


# ---------------------------------------------------------------------------
# Painéis opcionais do catálogo
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "painel",
    ["posicao", "sequencias", "placares", "saldos", "adversarios_historico"],
)
def test_painel_opcional_desenha(obt, painel):
    fig = dashboard.dashboard_time(obt, "Palmeiras", paineis=[painel])
    assert len(fig.data) >= 1


def test_heatmap_ganha_barra_de_cor_na_propria_celula(obt):
    fig = dashboard.dashboard_time(obt, "Palmeiras", paineis=["evolucao", "placares"])
    heatmap = next(t for t in fig.data if t.type == "heatmap")
    assert heatmap.colorbar.x > 0.5  # colada na segunda coluna, não no meio da figura


# ---------------------------------------------------------------------------
# Novas figuras de viz
# ---------------------------------------------------------------------------


def test_viz_forma_uma_serie_por_resultado(obt):
    fig = viz.forma(analytics.forma_recente(obt, "Palmeiras", n=4))
    assert {t.name for t in fig.data} <= {"Vitórias", "Empates", "Derrotas"}
    assert fig.layout.xaxis.ticktext  # adversário + (C)/(F) no eixo


def test_viz_sequencias_rotula_os_quatro_tipos(obt):
    fig = viz.sequencias(analytics.sequencias(obt, "Palmeiras"))
    assert set(fig.data[0].y) == set(viz.ROTULO_SEQUENCIA.values())


def test_destaque_com_nome_fora_da_tabela_e_erro(obt):
    with pytest.raises(ValueError, match="não está nesta tabela"):
        viz.classificacao(analytics.classificacao(obt, 2023), destaque="Flamengo")


def test_destaque_tolera_acento_e_caixa(obt):
    fig = viz.classificacao(analytics.classificacao(obt, 2023), destaque="palmeiras")
    assert fig.data[0].marker.color.count(dashboard.CINZA_NEUTRO) == 2


# ---------------------------------------------------------------------------
# Fachada
# ---------------------------------------------------------------------------


def test_cliente_expoe_dashboard_e_catalogo(caminho_csv):
    br = Brasileirao(fonte=caminho_csv, cache=False)
    fig = br.dashboard("palmeiras")
    assert fig.layout.title.text == "Palmeiras — Brasileirão 2023"
    assert br.dashboard("palmeiras", ano_campeonato=1971).layout.title.text.endswith(
        "1971"
    )
    catalogo = br.paineis()
    assert set(catalogo.columns) == {"painel", "padrao", "descricao"}
    assert catalogo["padrao"].sum() == len(dashboard.PAINEIS_PADRAO)


def test_plot_tabela_aceita_destaque(caminho_csv):
    br = Brasileirao(fonte=caminho_csv, cache=False)
    fig = br.plot_tabela(2023, destaque="Santos")
    assert isinstance(fig.data[0].marker.color, (list, tuple))


# ---------------------------------------------------------------------------
# Espaço para os rótulos dos gráficos de barras horizontais
# ---------------------------------------------------------------------------


def test_barras_horizontais_reservam_margem_para_os_nomes(obt):
    margem = dashboard.PAINEIS["classificacao"].margem_esquerda
    fig = dashboard.dashboard_time(obt, "Palmeiras", paineis=["classificacao"])
    assert fig.layout.margin.l == margem


def test_painel_da_segunda_coluna_ganha_calha_em_vez_de_margem(obt):
    fig = dashboard.dashboard_time(
        obt, "Palmeiras", paineis=["evolucao", "adversarios"]
    )
    esquerda, direita = fig.layout.xaxis.domain, fig.layout.xaxis2.domain
    calha = direita[0] - esquerda[1]
    largura_util = dashboard.LARGURA_NOMINAL - fig.layout.margin.l - 56
    assert calha * largura_util >= dashboard.PAINEIS["adversarios"].margem_esquerda
    assert fig.layout.margin.l == dashboard.MARGEM_ESQUERDA  # evolucao não precisa


def test_calha_nunca_fica_maior_que_o_painel(obt):
    fig = dashboard.dashboard_time(obt, "Palmeiras", colunas=6)
    dominios = [
        fig.layout[k]["domain"]
        for k in sorted(k for k in fig.layout.to_plotly_json() if k.startswith("xaxis"))
    ]
    larguras = [d[1] - d[0] for d in dominios]
    calhas = [b[0] - a[1] for a, b in zip(dominios, dominios[1:]) if b[0] > a[1]]
    assert min(larguras) >= max(calhas) - 1e-9  # o teto bate exato em 6 colunas

"""Exportação de figuras da dashgusbr para HTML e imagem.

Atalhos finos sobre o Plotly, com mensagens de erro amigáveis. A exportação
de imagem estática (PNG/SVG/PDF) depende do pacote opcional ``kaleido``::

    pip install dashgusbr[imagem]
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import plotly.graph_objects as go

Caminho = Union[str, Path]

_FORMATOS_IMAGEM = (".png", ".svg", ".pdf", ".jpg", ".jpeg", ".webp")


def salvar_html(fig: go.Figure, caminho: Caminho, **kwargs) -> Path:
    """Salva a figura como página HTML interativa e retorna o caminho.

    ``kwargs`` são repassados a ``fig.write_html`` (ex.:
    ``include_plotlyjs="cdn"`` para um arquivo bem menor).
    """
    destino = Path(caminho)
    if destino.suffix.lower() not in (".html", ".htm"):
        destino = destino.with_suffix(".html")
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(destino), **kwargs)
    return destino


def salvar_imagem(
    fig: go.Figure, caminho: Caminho, escala: float = 2, **kwargs
) -> Path:
    """Salva a figura como imagem estática (PNG/SVG/PDF...) e retorna o caminho.

    Requer o extra ``imagem`` (``pip install dashgusbr[imagem]``). ``escala``
    multiplica a resolução (2 = retina). ``kwargs`` vão para
    ``fig.write_image`` (``width``, ``height``...).
    """
    destino = Path(caminho)
    if destino.suffix.lower() not in _FORMATOS_IMAGEM:
        destino = destino.with_suffix(".png")
    try:
        import kaleido  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "Exportar imagem estática requer o pacote 'kaleido'. "
            "Instale com: pip install dashgusbr[imagem]"
        ) from exc
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(str(destino), scale=escala, **kwargs)
    return destino

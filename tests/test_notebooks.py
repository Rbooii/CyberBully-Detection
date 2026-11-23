import re
from pathlib import Path

import nbformat
import pytest

from cyberbully.config import ROOT

NOTEBOOK_DIR = ROOT / "notebooks"
NOTEBOOKS = sorted(NOTEBOOK_DIR.glob("*.ipynb"))
REQUIRED_HEADINGS = ("Tujuan", "Prasyarat", "Glosarium", "Ringkasan")


def test_notebooks_exist() -> None:
    assert len(NOTEBOOKS) >= 3, "notebook 00, 01, dan 06 harus ada"


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda item: item.name)
def test_notebook_has_required_explanations(path: Path) -> None:
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)

    assert re.fullmatch(r"\d{2}_[a-z0-9_]+\.ipynb", path.name), (
        f"nama {path.name} tidak sesuai NN_topik_snake_case.ipynb"
    )

    markdown = "\n".join(
        cell.source for cell in notebook.cells if cell.cell_type == "markdown"
    )
    for heading in REQUIRED_HEADINGS:
        assert heading.lower() in markdown.lower(), f"{path.name} tidak punya '{heading}'"

    previous = None
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            assert cell.source.strip(), f"{path.name} sel {index} kosong"
            assert previous is not None and previous.cell_type == "markdown", (
                f"{path.name} sel {index}: setiap sel kode harus didahului markdown"
            )
            assert len(previous.source.strip()) >= 120, (
                f"{path.name} sel {index}: penjelasan sebelum kode terlalu pendek"
            )
        previous = cell

    source = "\n".join(cell.source for cell in notebook.cells)
    assert "/Users/" not in source, f"{path.name} memuat path absolut pengguna"

    if path.name != "99_report.ipynb":
        outputs = [
            output
            for cell in notebook.cells
            if cell.cell_type == "code"
            for output in cell.get("outputs", [])
        ]
        assert not outputs, f"{path.name} masih menyimpan output; bersihkan sebelum commit"

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def runtime_dir():
    # Keep test scratch files inside the checkout, including in Windows sandboxes.
    root = Path(__file__).resolve().parents[1] / "data" / "tests"
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as directory:
        yield Path(directory)

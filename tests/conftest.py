import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def fixture_json():
    def load(name: str) -> dict[str, Any]:
        path = Path(__file__).parent / "fixtures" / name
        value = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(value, dict)
        return value

    return load

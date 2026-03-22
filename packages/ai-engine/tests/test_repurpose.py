import pytest

from iterra_ai.repurpose.engine import RepurposeEngine
from iterra_ai.repurpose.schemas import RepurposeInput


def test_repurpose_engine_raises_not_implemented(repurpose_input):
    engine = RepurposeEngine()
    with pytest.raises(NotImplementedError):
        engine.repurpose(repurpose_input)


def test_repurpose_input_valid():
    inp = RepurposeInput(
        original_content="Hello world",
        source_platform="twitter",
        target_platforms=["linkedin"],
    )
    assert inp.source_platform == "twitter"
    assert "linkedin" in inp.target_platforms

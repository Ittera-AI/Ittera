from iterra_ai.repurpose.engine import RepurposeEngine
from iterra_ai.repurpose.schemas import RepurposeInput


def test_repurpose_engine_returns_mock_outputs(repurpose_input):
    engine = RepurposeEngine()
    output = engine.repurpose(repurpose_input)
    assert output.repurposed
    assert output.repurposed[0].content


def test_repurpose_input_valid():
    inp = RepurposeInput(
        original_content="Hello world",
        source_platform="twitter",
        target_platforms=["linkedin"],
    )
    assert inp.source_platform == "twitter"
    assert "linkedin" in inp.target_platforms

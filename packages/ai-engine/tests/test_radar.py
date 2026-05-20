from iterra_ai.radar.engine import TrendRadar
from iterra_ai.radar.schemas import RadarInput


def test_radar_engine_returns_mock_trends(radar_input):
    engine = TrendRadar()
    output = engine.scan(radar_input)
    assert output.trends
    assert output.trends[0].platforms == radar_input.platforms


def test_radar_input_defaults():
    inp = RadarInput(niche="fitness", platforms=["instagram"])
    assert inp.limit == 10

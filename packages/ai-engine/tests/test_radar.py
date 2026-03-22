import pytest

from iterra_ai.radar.engine import TrendRadar
from iterra_ai.radar.schemas import RadarInput


def test_radar_engine_raises_not_implemented(radar_input):
    engine = TrendRadar()
    with pytest.raises(NotImplementedError):
        engine.scan(radar_input)


def test_radar_input_defaults():
    inp = RadarInput(niche="fitness", platforms=["instagram"])
    assert inp.limit == 10

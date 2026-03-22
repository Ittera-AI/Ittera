from iterra_ai.radar.schemas import RadarInput, RadarOutput


class TrendRadar:
    """Scans and surfaces trending topics relevant to a given niche.

    TODO: Implement using web search APIs + LLM summarization.
    See prompts/radar.py for prompt templates.
    """

    def scan(self, input: RadarInput) -> RadarOutput:
        """Scan for current trends in the given niche.

        Args:
            input: Niche, platform list, and result limit.

        Returns:
            RadarOutput with ranked trend items.

        Raises:
            NotImplementedError: Until the engine is implemented.
        """
        # TODO: implement trend scanning using search API + LLM
        raise NotImplementedError(
            "TrendRadar.scan is not yet implemented. "
            "See iterra_ai/radar/engine.py to implement."
        )

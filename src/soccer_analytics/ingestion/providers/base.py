from __future__ import annotations

from abc import ABC, abstractmethod

from soccer_analytics.domain import PipelineBundle


class SportsDataProvider(ABC):
    name: str

    @abstractmethod
    async def fetch_bundle(self, league_code: str, season_year: int) -> PipelineBundle:
        raise NotImplementedError

from abc import ABC, abstractmethod
from enum import Enum

from pydantic import Field, BaseModel, computed_field
from typing import List


class MapType(str, Enum):
    GOOGLE = "google"
    BING = "bing"
    LIVING_ATLAS = "living_atlas"
    SENTINEL_HUB = "sentinel_hub"


class BaseMapUrl(BaseModel, ABC):
    lat: float
    lon: float
    zoom: int
    type: MapType

    @abstractmethod
    def generate_url(self) -> str:
        pass

    @property
    def url(self) -> str:
        return self.generate_url()

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        return self.url

    model_config = {
        # This ensures that when the object is printed or converted to string,
        # it uses our custom __str__ method
        "str_strip_whitespace": True,
        "str_max_length": None
    }


class GoogleMapUrl(BaseMapUrl):
    type: MapType = MapType.GOOGLE

    def generate_url(self) -> str:
        return f"https://www.google.com/maps/@{self.lat},{self.lon},{self.zoom}z/data=!3m1!1e3"


class BingMapUrl(BaseMapUrl):
    type: MapType = MapType.BING

    def generate_url(self) -> str:
        return f"https://www.bing.com/maps?cp={self.lat}~{self.lon}&lvl={self.zoom}&style=h"


class LivingAtlasMapUrl(BaseMapUrl):
    type: MapType = MapType.LIVING_ATLAS

    def generate_url(self) -> str:
        return f"https://livingatlas.arcgis.com/wayback/#active=34007&mapCenter={self.lon}%2C{self.lat}%2C{self.zoom}"


class SentinelHubMapUrl(BaseMapUrl):
    type: MapType = MapType.SENTINEL_HUB

    def generate_url(self) -> str:
        return f"https://apps.sentinel-hub.com/eo-browser/?zoom={self.zoom}&lat={self.lat}&lng={self.lon}"

class Location(BaseModel):
    lat: float = Field(description="Latitude of the site")
    lon: float = Field(description="Longitude of the site")
    radius: int = Field(description="Radius of the site in meters")

    def _calculate_zoom_level(self) -> int:
        """Calculate appropriate zoom level based on radius"""
        if self.radius > 10000:
            return 12
        elif self.radius > 5000:
            return 13
        elif self.radius > 1000:
            return 14
        elif self.radius < 100:
            return 18
        return 15

    @computed_field
    @property
    def maps(self) -> List[BaseMapUrl]:
        """Automatically generate map URLs based on site coordinates"""
        zoom_level = self._calculate_zoom_level()

        return [
            GoogleMapUrl(
                lat=self.lat,
                lon=self.lon,
                zoom=zoom_level
            ),
            BingMapUrl(
                lat=self.lat,
                lon=self.lon,
                zoom=zoom_level
            ),
            LivingAtlasMapUrl(
                lat=self.lat,
                lon=self.lon,
                zoom=zoom_level
            ),
            SentinelHubMapUrl(
                lat=self.lat,
                lon=self.lon,
                zoom=zoom_level
            )
        ]

class Site(Location):
    name: str = Field(description="Name of the site")

class Hotspot(Location):
    rationale: str = Field(description="Reasoning behind the selection of this hotspot. Backed up by image analysis.")
    score: int = Field(description="Likelihood of an architectural or historical new finding. Score from 1 to 100.")
    name: str = Field(description="Name of the hotspot")
    sources: str = Field(description="Sources supporting the rationale")

    def to_prompt_str(self) -> str:
        out = f"Hotspot {self.name} @ ({self.lat}, {self.lon})\n"
        out += f"Score: {self.score}\n"
        out += f"Rationale: {self.rationale}\n"
        out += "Sources:\n" + "\n".join(f"- {s}" for s in self.sources)
        return out

class ImageAnalysis(BaseModel):
    analysis_raw: str = Field(description="Raw text of the image analysis output")
    hotspots: List[Hotspot] = Field(description="List of hotspots or precis point of interest with anomalies that are relevant to the potential site")

    def to_prompt_str(self):
        return ("Image Analysis: " + self.analysis_raw +
                "\n\n".join(h.to_prompt_str() for h in self.hotspots))


class PotentialSite(Site):
    sources: List[str] = Field(description="List of sources that support the selection of this potential site")
    rationale: str = Field(description="Reasoning behind the selection of this potential site")

    def to_prompt_str(self):
        return f"""Potential site:
        - lat: {self.lat}; 
        - lon: {self.lon}; 
        - radius: {self.radius}; 
        - rationale: {self.rationale}; 
        - public sources: {"; ".join(self.sources)}."""


class ClosestKnownSite(Site):
    distance: List[str] = Field(description="List of maps urls that show the potential site. Bing, google or ArcGis.")
    is_within_search_radius: bool = Field(description="Is distance within search radius of PotentialSite.")
    type: str = Field(description="Type of the Site.")
    id: str = Field(description="Site ID.")
    description: str = Field(description="Site Description.")
    site_summary: str = Field(description="Site Summary.")

class Image(BaseModel):
    label: str = Field(description="Image type")
    url: str = Field(description="Image url")

class UserInput(BaseModel):
    lat: float | None = Field(description="Latitude of the potential site", default=None)
    lon: float | None = Field(description="Longitude of the potential site", default=None)
    radius: int | None = Field(description="Radius of the potential site in meters", default=None)
    exact: bool | None = Field(description="Whether coordinates are exact or approximate. "
                                    "If exact AI will look only there otherwise it will look close to the coordinates.",
                               default=None)
    no_input: bool = Field(default=False, description="Whether coordinates are exact or approximate. "
                                    "If exact AI will look only there otherwise it will look close to the coordinates.")

class RemoteSensingState(BaseModel):
    images: List[Image] | None = []
    potential_site: PotentialSite | None = None
    closest_known_site: ClosestKnownSite | None = None
    image_analysis: ImageAnalysis | None = None
    cross_verification: str | None = None
    user_input: UserInput | None = None
    prompt_log: List[str] = Field(default_factory=list, description="Prompt log")


from pydantic import Field
from typing import List
from crewai import LLM
from jinja2 import Template
from pydantic import BaseModel
import datetime
import re

# Models. Price per 1M Tokens: Input | Cached Input | Output
model_41 = "gpt-4.1"  # $2.00 $0.50 $8.00
model_41_mini = "gpt-4.1-mini"  # $0.40 $0.10 $1.60
model_41_nano = "gpt-4.1-nano"  # $0.10 $0.025 $0.40
model_o3 = "o3"  # $10.00 $2.50 $40.00
model_o3_mini = "o3-mini"  # $1.10 $0.55 $4.40
model_o4_mini = "o4-mini"  # $1.10 $0.275 $4.40
model_4o = "gpt-4o"  # $2.5 $1.25 $10

llm_provider_azure = "azure"
llm_provider_openai = "openai"
llm_azure_api_version = "2025-04-01-preview"


# llm factory function
def get_llm_azure(model_name: str) -> LLM:
    return LLM(
        model=f"{llm_provider_azure}/{model_name}",
        api_version=llm_azure_api_version,  # only use with azure
        additional_drop_params=["stop"],
        drop_params=True,
        verbose=True,
    )

class Hotspot(BaseModel):
    lat: float = Field(description="Precise Latitude of the hotspot")
    lon: float = Field(description="Precise Longitude of the hotspot")
    radius: int = Field(description="Precise Radius of the hotspot")
    rationale: str = Field(description="Reasoning behind the selection of this hotspot. Backed up by image analysis.")
    maps: List[str] = Field(description="List of maps urls that show the hotspot. Zoomed at the relevant level and in satellite view. Bing, google or ArcGis.")
    score: int = Field(description="Likelihood of an architectural or historical new finding. Score from 1 to 100.")

    def to_prompt_str(self, show_maps: bool = False) -> str:
        out = f"{self.label} @ ({self.lat}, {self.lon})\n"
        out += f"Rationale: {self.rationale}\n"
        if show_maps:
            out += "Maps:\n" + "\n".join(f"- {m}" for m in self.maps) + "\n"
        out += "Sources:\n" + "\n".join(f"- {s}" for s in self.sources)
        return out

class ImageAnalysis(BaseModel):
    analysis_raw: str = Field(description="Raw text of the image analysis output")
    hotspots: List[Hotspot] = Field(description="List of hotspots or precis point of interest with anomalies that are relevant to the potential site")

    def to_prompt_str(self, show_maps=False):
        return self.analysis_raw + "\n\n".join(h.to_prompt_str(show_maps=show_maps) for h in self.hotspots)

class PotentialSite(BaseModel):
    name: str = Field(description="Name of the potential site")
    lat: float = Field(description="Latitude of the potential site")
    lon: float = Field(description="Longitude of the potential site")
    radius: int = Field(description="Radius of the potential site in meters")
    rationale: str = Field(description="Reasoning behind the selection of this potential site")
    maps: List[str] = Field(description="List of maps urls that show the potential site. Bing, google or ArcGis.")
    sources: List[str] = Field(description="List of sources that support the selection of this potential site")

class Image(BaseModel):
    label: str = Field(description="Image type")
    url: str = Field(description="Image url")

class UserInput(BaseModel):
    lat: float = Field(description="Latitude of the potential site")
    lon: float = Field(description="Longitude of the potential site")
    radius: int = Field(description="Radius of the potential site in meters")

class RemoteSensingState(BaseModel):
    images: List[Image] = []
    potential_site: PotentialSite = None
    image_analysis: ImageAnalysis = None
    cross_verification: str = None
    user_input: UserInput = None
    prompt_log: List[str] = Field(default_factory=list, description="Prompt log")


def create_safe_filename(base_name: str, extension: str = "", timestamp:bool = False) -> str:
    """
    Create a safe filename by replacing invalid characters
    """
    timestamp_str = ''
    if timestamp:
        timestamp = datetime.datetime.now()
        # Format timestamp in a safe way
        timestamp_str = "_" + timestamp.strftime("%Y-%m-%d_%H-%M-%S")

    # Replace any invalid Windows characters
    safe_name = re.sub(r'[<>:"/\\|?*\s]', '-', base_name)

    return f"{safe_name}{timestamp_str}{extension}"


def get_markdown_potential_site(potential_site: PotentialSite) -> str:
    template_str = """
    ### 🏷️ Potential Site

    **Name:** `{{ site.name }}`  
    **Latitude:** `{{ site.lat }}`  
    **Longitude:** `{{ site.lon }}`  
    **Radius:** `{{ site.radius }} meters`

    ---

    #### 🧠 Rationale

    {{ site.rationale }}

    ---

    #### 🗺️ Maps

    {% for url in site.maps %}
    - [{{ url }}]({{ url }})
    {% endfor %}

    ---

    #### 📚 Sources

    {% for src in site.sources %}
    - {{ src }}
    {% endfor %}
    """

    template = Template(template_str)
    md_content = template.render(site=potential_site)
    return md_content


def get_markdown_image_analysis(image_analysis: ImageAnalysis) -> str:
    template_str = """
    # 🧠 Image Analysis Summary

    ## 🔍 Raw Analysis
    
    {{ analysis.analysis_raw }}
    
    {% if analysis.hotspots %}
    ## 📌 Hotspots
    
    {% for h in analysis.hotspots %}
    ### 🔸 Hotspot {{ loop.index }}
    
    - **Latitude:** {{ h.lat }}
    - **Longitude:** {{ h.lon }}
    - **Radius:** {{ h.radius }} meters
    - **Rationale:** {{ h.rationale }}
    - **Score:** {{ h.score }} / 100
    
    {% if h.maps %}
    **Maps:**
    {% for m in h.maps %}
    - [Map {{ loop.index }}]({{ m }})
    {% endfor %}
    {% endif %}
    
    ---
    {% endfor %}
    {% else %}
    _No hotspots identified._
    {% endif %}
    """

    template = Template(template_str)
    md_content = template.render(analysis=image_analysis)
    return md_content
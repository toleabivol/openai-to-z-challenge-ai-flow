import asyncio

from litellm import ContentPolicyViolationError, BadRequestError
from models import PotentialSite, ImageAnalysis
from crewai import LLM
from jinja2 import Template
from pydantic import BaseModel
import datetime
import re
from math import radians, sin, cos, sqrt, atan2
import logging
LOGGER = logging.getLogger('remote_sensing_flow_helpers')
LOGGER.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
LOGGER.addHandler(handler)

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
def get_llm_azure(model_name: str, temperature: float = None) -> LLM:
    return LLM(
        model=f"{llm_provider_azure}/{model_name}",
        api_version=llm_azure_api_version,  # only use with azure
        additional_drop_params=["stop"],
        drop_params=True,
        verbose=True,
        temperature=temperature
    )

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

MAX_RETRIES = 3
async def safe_kickoff(agent, prompt: str, response_format = None) -> BaseModel:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = await agent.kickoff_async(prompt, response_format=response_format)
            return result
        except ContentPolicyViolationError as e:
            LOGGER.warning(f"[Attempt {attempt}] Content policy violation: {e}")
        except BadRequestError as e:
            if "prompt policy" in str(e).lower():
                LOGGER.warning(f"[Attempt {attempt}] Bad request due to prompt policy: {e}")
            else:
                raise  # Not related to prompt policy – re-raise
        await asyncio.sleep(1)
    raise RuntimeError("Failed after 3 attempts due to content policy violations.")


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two points on Earth using Haversine formula"""
    r = 6371000  # Earth's radius in meters

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = r * c

    return distance
import asyncio
from typing import List

import pandas as pd
from litellm import ContentPolicyViolationError, BadRequestError
from models import PotentialSite, ImageAnalysis, Hotspot, ClosestKnownSite
from crewai import LLM
from jinja2 import Template
from pydantic import BaseModel
import datetime
import re
from math import radians, sin, cos, sqrt, atan2
import logging
import cv2
from pyproj import Geod
import os

LOGGER = logging.getLogger('remote_sensing_flow_helpers')
LOGGER.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s - %(message)s")
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
    # Image Analysis Summary

    ## Raw Analysis
    
    {{ analysis.analysis_raw }}
    
    {% if analysis.hotspots %}
    ## Hotspots
    
    {% for h in analysis.hotspots %}
    ### Hotspot {{ loop.index }}
    
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


def get_markdown_closest_known_site(closest_known_site: ClosestKnownSite) -> str:
    template_str = """
    ## Known Sites Check Results

    ## Closest Known Site
    
    - Name: {{ closest_known_site.name }}
    - Site ID: {{ closest_known_site.id }}
    - Distance: {{ closest_known_site.distance[0] }}
    - Type: {{ closest_known_site.type }}
    - Description: {{ closest_known_site.description }}
    - Coordinates: {{ closest_known_site.lat }}, {{closest_known_site.lon }}
    
    ## Analysis
    - Search radius: {{ closest_known_site.radius }} meters
    - Is within search radius: {{ closest_known_site.is_within_search_radius }}
    
    {% if closest_known_site.maps %}
    **Maps:**
    {% for m in closest_known_site.maps %}
    - [Map {{ loop.index }}]({{ m }})
    {% endfor %}
    {% endif %}
    """

    template = Template(template_str)
    md_content = template.render(closest_known_site=closest_known_site)
    return md_content

def get_closest_known_site(lat: float, lon: float, radius: int) -> ClosestKnownSite | None :
    known_sites_df = pd.read_csv('input_data/known_sites.csv')

    closest_distance = float('inf')
    closest_site = None

    for _, site in known_sites_df.iterrows():
        distance = haversine_distance(
            lat,
            lon,
            site['latitude'],
            site['longitude']
        )

        if distance < closest_distance:
            closest_distance = distance
            closest_site = site

    closest_known_site = None
    if closest_site is not None:
        LOGGER.info(f"Closest known site found: {closest_site}")

        closest_known_site = ClosestKnownSite(
            name=closest_site['site_name'],
            lat=closest_site['latitude'],
            lon=closest_site['longitude'],
            radius=radius,
            distance=[f"{closest_distance:.2f} meters"],
            is_within_search_radius=closest_distance <= radius,
            type=closest_site['site_type_description'],
            id=str(closest_site['site_id']),
            description=closest_site.get('nature_description', 'No description available'),
            site_summary=closest_site['site_summary'] if pd.notna(
                closest_site['site_summary']) else 'No summary available'
        )

        LOGGER.info(f"Closest known site: {closest_known_site.name}")
        LOGGER.info(f"Distance to closest site: {closest_distance:.2f} meters")
        LOGGER.info(f"Within search radius: {closest_known_site.is_within_search_radius}")

    return closest_known_site

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

def draw_hotspots_on_image(image_path: str, hotspots: List[Hotspot], image_size: tuple[int,int],
                           llm_received_image_size: tuple[int,int],
                           output_path: str = None):
    """
    Draw hotspots on an image as circles with text labels.
    
    Args:
        image_path: Path to the input image
        hotspots: List of Hotspot objects with lat, lon, radius, name, and x_from_center/y_from_center attributes
        output_path: Path where to save the output image. If None, will append '_hotspots' to original name
    """


    img = cv2.imread(image_path)
    LOGGER.info(f"Drawing hotspots on image: {image_path}")
    if img is None:
        LOGGER.error(f"Failed to load image from {image_path}")
        return
    
    height, width = img.shape[:2]
    LOGGER.info(f"Original Image size {width} {height}")
    LOGGER.info(f"Received by LLM Image size {llm_received_image_size[0]} {llm_received_image_size[1]}")

    # Calculate the scaling factor
    scale_x = width / llm_received_image_size[0]
    scale_y = height / llm_received_image_size[1]

    LOGGER.info(f"Scale factor x: {scale_x}, y: {scale_y}")
    
    # For each hotspot
    for hotspot in hotspots:
        # Calculate pixel coordinates using x_from_center and y_from_center
        # These values should be between -1 and 1, representing position relative to center
        center_x = int(hotspot.x * scale_x)
        center_y = int(hotspot.y * scale_y)
        radius = int(hotspot.radius_in_pixels * scale_x)

        LOGGER.info(f"Hotspot {hotspot.name} {str(center_x)} {str(center_y)} {radius}")

        # Draw circle
        cv2.circle(img, (center_x, center_y), radius, (0, 255, 0), 4)
        
        # Add text label
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        text_size = cv2.getTextSize(hotspot.name, font, font_scale, 1)[0]
        text_x = center_x - text_size[0]//2
        text_y = center_y - radius - 10
        
        # Draw text with background for better visibility
        cv2.putText(img, f"{hotspot.name} {str(center_x)} {str(center_y)}", (text_x, text_y), font, font_scale, (0, 255, 0), 2)
        cv2.putText(img, f"{hotspot.name} {str(center_x)} {str(center_y)}", (text_x, text_y), font, font_scale, (0, 0, 0), 1)
    
    # Generate output path if not provided
    if output_path is None:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_hotspots{ext}"
    
    # Save the image
    cv2.imwrite(output_path, img)
    LOGGER.info(f"Saved annotated image to {output_path}")
    return output_path
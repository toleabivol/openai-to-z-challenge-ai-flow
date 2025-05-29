# WahrCo.de Crew — OpenAI to Z Challenge Flow

Welcome to the WahrCo.de Crew to Z Crew project, powered by [crewAI](https://crewai.com). 
A multi-agent AI system that also uses tools and direct llm calls to collaborate effectively on the task: 
**Archaeological remote sensing of the Amazon river bazin region.**

## Installation

Ensure you have Python >=3.12 <3.13 installed on your system. 

Install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

```bash
crewai install
```

### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

## Running the Project

To kickstart your flow and begin execution, run this from the root folder of your project:

```bash
crewai run
```

This command initializes the `remote_sensing_flow` Flow.

The result will be a folder with satellite images and .md files (mainly `report.md`) in the `output/{potential_site_name}/`.
See `output_example/`

## Output Report Example

Verified Archaeological Site Report  
Site Name: Piquiatuba Levee Village Site  
Coordinates (WGS84): Latitude –0.4962, Longitude –54.2453  
Search Radius: 300 m  

1. Confidence Score: 80/100  
   Rationale:  
   • Multispectral satellite imagery (Landsat 8 & Sentinel-2) shows a distinct elliptical clearing (~300 m) with reduced vegetation (NDVI/NBR anomalies) and possible open‐soil or water patches.  
   • DEM analysis (Copernicus & Mapzen 30 m) reveals a 15–20 m elevation mound consistent with pre-Columbian earthworks.  
   • LIDAR studies (Stenborg et al. 2018; de Souza et al. 2018) document similar Amazon‐rim mound complexes.  
   • A 1660 expedition diary (LOC) and a 1661 colonial map note a village (“Vila de Piquiatuba”) at nearly these same coordinates.  

2. Comparison to Known Feature  
   The mound morphology and vegetation anomalies closely resemble other Amazonian earthwork sites (e.g., Marajo ring‐dikes, Kuhikugu mound complexes), which share elevated terrain on natural levees, proximity to waterways, and patterns of clearings visible in remote sensing.

3. Recommended Next Steps  
   • Conduct targeted high‐resolution LiDAR survey to resolve fine‐scale earthwork architecture.  
   • Undertake ground‐truthing soil and test‐pitting to confirm cultural stratigraphy.  
   • Engage local stakeholders and heritage authorities for permissions and community consultation.

4. Map Links to Coordinates  
   • Google Maps: https://www.google.com/maps/@-0.4962,-54.2453,17z  
   • Bing Maps: https://www.bing.com/maps?cp=-0.4962~-54.2453&lvl=17  
   • Sentinel-Hub EO Browser: https://apps.sentinel-hub.com/eo-browser/?zoom=17&lat=-0.4962&lng=-54.2453  
   • Living Atlas Wayback: https://livingatlas.arcgis.com/wayback/#active=34007&mapCenter=-54.2453%2C-0.4962%2C14  

5. Sources  
   • LOC Expedition Diaries (1660): https://www.loc.gov/resource/gdclccn.02029950/?st=gallery  
   • Stenborg et al. 2018 (LIDAR Amazon earthworks): https://www.tandfonline.com/doi/full/10.1080/00934690.2017.1417198  
   • de Souza et al. 2018 (Pre-Columbian Amazon): https://www.nature.com/articles/s41467-018-03510-7  
   • The Archaeology of the Upper Amazon (2021): https://books.google.com/books?hl=en&lr=&id=B4DSEAAAQBAJ  

Recommendation: Given the high confidence score and multiple lines of evidence, this site merits follow-up archaeological survey and local stakeholder engagement.

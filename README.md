# WahrCo.de Crew — OpenAI to Z Challenge Flow

Welcome to the WahrCo.de Crew to Z project, powered by [crewAI](https://crewai.com). 
A multi-agent AI system that also uses tools and direct llm calls to collaborate effectively on the task: 
**Archaeological remote sensing of the Amazon river bazin region.**

Uses AI workflow based on [CrewAI Flow](https://docs.crewai.com/concepts/flows) 

## Flow

1. User input
2. Researcher Agent
3. Check Close Known Sites
4. Collect Data (Satellite Imagery)
5. Analyze Images with LLM
6. Add Hotspots on the images
7. Cross Verification
8. Reporting Agent

## Installation

Details at https://docs.crewai.com/installation

Ensure you have Python >=3.12 <3.13 installed on your system. 

Install uv:

```bash
pip install uv
```
Install CrewAI uv tool:
```bash
uv tool install crewai
```

Next, navigate to your project directory and install the dependencies 
(this will also create a virtual environment in `.venv`):

```bash
crewai install
```

### Customizing

Copy the `.env.template` to `.env` and add/replace the env var values in it

Depending on your LLM provider you can configure that in .env by selecting the and then adding specific to the provider 
configuration as described in the [CrewAI Docs>LLMs](https://docs.crewai.com/concepts/llms#provider-configuration-examples)

For OpenAI :
```text
# Required
LLM_PROVIDER=OPENAI
OPENAI_API_KEY=sk-...
```

For Azure OpenAI :
```text
LLM_PROVIDER=AZURE
AZURE_API_KEY=<your-api-key>
AZURE_API_BASE=<your-resource-url>
AZURE_API_VERSION=<api-version>
```

To chose which model is used where open the `src/remote_sensing_flow/main.py` then 
search for places `get_llm(model_41_mini` and change to a desired model. 
Available models are in `src/remote_sensing_flow/helpers.py`.

## Running the Project

To kickstart your flow and begin execution, run this from the root folder of your project:

```bash
crewai run
```
or activate the virtual env and run the python script
```bash
source .venv/bin/activate
python src/remote_sensing_flow/main.py
```

There are more ways to run this project

### Option 0 - fast test no inputs argument
If not already done, activate virtual env: 
```bash
source .venv/bin/activate
```

This is a shortcut for: option 1 > input "y" > hit enter.
Run the python script with `--ni 1`. This will tell the script not to ask anything and let Researcher Agent select a location.
```bash
python src/remote_sensing_flow/main.py --ni 1
```

### Option 1 - select no inputs

After running the script will ask you if you want to input coordinates. Input "n" and hit enter.
The script will then tell the Researcher Agent to select a location and pass it on through the flow.

### Option 2 - add inputs 

After running the script will ask you if you want to input coordinates. Input "y" and hit enter.
The script will then ask for lat, long and radius in meters. 
The script will ask if you want exactly this location to be used. 

#### Option 2.1 non-exact
Input "n" and enter.
The Researcher agent will then use the input as a reference but may diverge from it.

#### Option 2.2 exact
Input "y" and enter.
The Researcher agent will then use the input and do not diverge from it. The flow will also be based on the input. 
E.g. the images will be of the exact coordinates with the exact size (only limited to certain hardcoded min and max). 

After that the Researcher 
Agent will check the coordinates for textual or historical significants and add this info and pass it on through the flow. 

This command initializes the `remote_sensing_flow` Flow.

The result will be a folder with satellite images and .md files (mainly `report.md`) in the `output/{potential_site_name}/`.
For examples see `output_example/`

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

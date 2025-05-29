"""
Full OpenAI to Z Challenge completion. For Checkpoint 2 see main.py
"""
from crewai import Agent, Task, Crew, Process
from crewai_tools.aws.s3 import S3ReaderTool
from crewai_tools import FileReadTool, VisionTool

from tools.gee import GEEImageTool, GEEImageURLTool
from tools.s3 import S3DownloadTool
from tools.search import SearchTool
from tools.read_local_image import ReadLocalImageTool
from tools.sentinel_hub_png import SentinelS3PngUploader
from tools.satellite_imagery_analysis import SatelliteImageryAnalysisTool
from utils.helpers import get_llm_azure, model_o4_mini, model_41_nano, model_41_mini, model_41

# Initialize the tool
s3_reader_tool = S3ReaderTool()
s3_download_tool = S3DownloadTool()
gee_image_tool = GEEImageTool()
gee_image_url_tool = GEEImageURLTool()
file_read_tool = FileReadTool()
local_image_read_tool = ReadLocalImageTool()
sentinel_image_url_tool = SentinelS3PngUploader(result_as_amswer=True)
satellite_iamgery_analysis_tool = SatelliteImageryAnalysisTool(llm=get_llm_azure(model_o4_mini))

# Agents
researcher = Agent(
    role="Archaeological Researcher",
    goal="Conduct research to identify potential archeological sites. "
         "Analyze documents, vocal records, and legends for spatial clues. "
         "Do not perform any satellite imagery analysis unless already done by someone else and published.",
    backstory="Expert in archaeological studies and historical research. Language expert.",
    tools=[SearchTool()],
    llm=get_llm_azure(model_o4_mini),
    verbose=True,
)

data_collector = Agent(
    role="Satellite & Text Data Collector",
    goal="Gather high-resolution satellite imagery. Use the Sentinel HUB S3 URL Tool to obtain urls to satellite imagery.",
    backstory="Specializes in geospatial data acquisition.",
    tools=[
        # SearchTool(),
        # s3_download_tool,
        sentinel_image_url_tool
    ],
    llm=get_llm_azure(model_41_mini),  # the more rational models tend to not use the tool
    verbose=True
)

image_analyst = Agent(
    role="Remote Sensing Analyst",
    goal="Identify potential sites through vegetation anomalies and terrain patterns",
    backstory="Expert in multispectral satellite imagery analysis. Make sure you use the tools provided.",
    tools=[
        # s3_reader_tool,
        # file_read_tool,
        # local_image_read_tool,
        satellite_iamgery_analysis_tool
    ],
    llm=get_llm_azure(model_41_mini),
    allow_delegation=False
)

cross_verification = Agent(
    role="Validation Agent",
    goal="Confirm coordinates through at least two independent methods",
    backstory="Geospatial data integrity expert",
    llm=get_llm_azure(model_41)
)

reporting_agent = Agent(
    role="Chief Archaeologist",
    goal="Compile findings into verified reports",
    backstory="Senior researcher with publication experience",
    llm=get_llm_azure(model_o4_mini)  # TODO use model o3 or o4 recommended, keeping mini for testing costs reduction
)

academic_references = """
Archaeological point data:
The Archeo Blog https://www.jqjacobs.net/blog/ shares sampled data already drawn from the Amazonian region.

Academic references with links:

Clasby, Ryan, and Jason Nesbitt, eds. The Archaeology of the Upper Amazon: Complexity and
Interaction in the Andean Tropical Forest. University Press of Florida, 2021.
https://books.google.com/books?hl=en&lr=&id=B4DSEAAAQBAJ&oi=fnd&pg=PP1&dq=amazon+lidar+ar
chaeology&ots=oK0FItet27&sig=oFAGRog0cFkX9MooeDiaoRvVWzs#v=onepage&q=amazon%20lidar%
20archaeology&f=false

Anna Cohen, Sarah Klassen & Damian Evans. (2020) Ethics in Archaeological Lidar. Journal of Computer
Applications in Archaeology 3:1, pages 76-91.
https://journal.caa-international.org/articles/10.5334/jcaa.48

de Souza, J.G., Schaan, D.P., Robinson, M. et al. Pre-Columbian earth-builders settled along the entire
southern rim of the Amazon. Nat Commun 9, 1125 (2018).
https://www.nature.com/articles/s41467-018-03510-7

Denise Maria Cavalcante Gomes. Urban Archaeology in the Lower Amazon: Fieldwork Uncovering Large
Pre-Colonial Villages in Santarém City, Brazil. Journal of Field Archaeology 0:0, pages 1-20.
https://www.tandfonline.com/doi/full/10.1080/00934690.2025.2466877

Jose Iriarte, Mark Robinson, Jonas de Souza, Antonia Damasceno, Franciele da Silva, Francisco
Nakahara, Alceu Ranzi & Luiz Aragao. (2020) Geometry by Design: Contribution of Lidar to the
Understanding of Settlement Patterns of the Mound Villages in SW Amazonia. Journal of Computer
Applications in Archaeology 3:1, pages 151-169.
https://journal.caa-international.org/articles/10.5334/jcaa.45

Khan, S., Aragão, L., & Iriarte, J. (2017). A UAV–lidar system to map Amazonian rainforest and its ancient
landscape transformations. International Journal of Remote Sensing, 38(8–10), 2313–2330.
https://www.tandfonline.com/doi/abs/10.1080/01431161.2017.1295486

Prümers, H., Betancourt, C.J., Iriarte, J. et al. Lidar reveals pre-Hispanic low-density urbanism in the
Bolivian Amazon. Nature 606, 325–328 (2022)
https://www.nature.com/articles/s41586-022-04780-4

Vinicius Peripato et al, (2023) More than 10,000 pre-Columbian earthworks are still hidden throughout
Amazonia. Science 382:6666, pages 103-109
https://www.science.org/doi/10.1126/science.ade2541

Fabien H. Wagner, Vinícius Peripato, Renato Kipnis, Sara L. Werdesheim, Ricardo Dalagnol, Luiz E.O.C.
Aragão & Mayumi C. M. Hirye. (2022) Fast computation of digital terrain model anomalies based on
LiDAR data for geoglyph detection in the Amazon. Remote Sensing Letters 13:9, pages 935-945.
https://www.tandfonline.com/doi/full/10.1080/2150704X.2022.2109942

Robert S. Walker, Jeffrey R. Ferguson, Angelica Olmeda, Marcus J. Hamilton, Jim Elghammer & Briggs
Buchanan. (2023) Predicting the geographic distribution of ancient Amazonian archaeological sites with
machine learning. PeerJ 11, pages e15137.
https://peerj.com/articles/15137/

Per Stenborg, Denise Schaan, Camila G. Figueiredo, Contours of the Past: LiDAR Data Expands the
Limits of Late Pre-Columbian Human Settlement in the Santarém Region, Lower Amazon, Journal of
Field Archaeology, (2018) Vol. 43, No. 1, 44–57
https://www.tandfonline.com/doi/full/10.1080/00934690.2017.1417198
"""

online_research_repositories = """
Online Research Repositories :

    Internet Archive Sources https://archive.org/search?query=lost+city+of+z for a library of text, audio, and video material to sort through.

    Library of Congress public‑domain expedition books https://www.loc.gov/resource/gdclccn.02029950/?st=gallery – contains detailed river‑mile diaries and
    Indigenous village positions you can geocode."""

# Tasks
research_task = Task(
    description=f"""Conduct remote archeological research to identify potential new archeological sites in the Amazon river region.
    Findings should be reasonably bound by the Amazon biome in Northern South America. Focus on Brazil, 
    with allowed extension into the outskirts of Bolivia, Columbia, Ecuador, Guyana, Peru, Suriname, Venezuela, and French Guiana.
    Check:
    1. Historical and archaeological significance of the Amazon region
    2. Indigenous oral histories and legends
    3. Colonial-era expedition diaries
    4. Historical maps
    5. Archaeological reports of existing sites

    {academic_references}

    {online_research_repositories}

    Archaeological sites tend to appear in
    similar places (along waterways, in higher elevations, along trade routes). Look at the known site location
    patterns and if you see trends regionally, they may result in discoveries in similar places.

    Cross-check against published geoglyph databases and academic reports so you’re not researching already known sites, 
    but new site adjacent to already known sites is allowed.
    Replace prohibited words like swastika or any other prohibited word with the appropriate word or description that is
    allowed, like 'geoglyph', in the search, search output, prompts and in the output.
    """,
    expected_output="One potential new archeological site based on the research with highest probability"
                    " of new findings. The output should be a short name, a list of coordinates "
                    "(latitude, longitude, radius) in WGS84 format followed by a short rationale, followed by direct "
                    "links to the google, bing and https://livingatlas.arcgis.com/wayback/#active=34007&mapCenter={long}%2C{lat}%2C14 maps with satellite layer and proper zoom level, "
                    "followed by urls to public resources to back the rationale. Must have at least one historical map or text.",
    agent=researcher,
    # human_input=True
)
data_task = Task(
    description="For the potential new archeological site proposed, collect following satellite imagery : "
                "- ESA Sentinel-2 imagery (10m resolution); "
    # "2. Published LiDAR tiles from AmazonGIS"
    # "3. GEDI data (Global Ecosystem Dynamics Observatory)"
    # "4. OpenTopography LiDAR for High-res canopy-penetrating elevation (1-10m)"
                "- SRTM Elevation data (10m resolution); "
                "- Landsat 8 L2 imagery (30m resolution); "
                "- NDVI and NDWI (10m resolution); "
                """
                Images should not have more than 20% cloud cover.
                
                Some sources to get you started (but do not limit yourself to these):
                Satellite imagery and map sources:
                Sentinel-2 10m on Sentinel Hub using Sentinel HUB S3 Tool.
                Landsat8 L2 30m on Sentinel Hub using Sentinel HUB S3 Tool
                Copernicus DEM 30m on Sentinel Hub using Sentinel HUB S3 Tool. 
                For Sentinel, Landsat and DEM images, use the Sentinel HUB S3 URL to get the public PNG url by passing lat long coordinates and radius in meters to the tool.
                Pass a bigger radius to the Sentinel HUB S3 URL than the possible site radius - at least 15000m and at most 25000m.
                Always use the Sentinel HUB S3 URL and make sure the tool returns urls before continuing.
                """,

    # """
    # Sentinel-2 COPERNICUS/S2_SR_HARMONIZED, NDVI, USGS/SRTMGL1_003 and Landsat8 on Google Earth Engine (GEE).
    # For GEE images, use the GEEImageURLTool to get the public image url by passing lat long coordinates and radius in meters to the tool.
    # Pass a bigger radius to the GEEImageURLTool than the possible site radius - at least 2000m and at most 25000m.
    # Always use the GEEImageURLTool and make sure the tool returns urls before continuing.
    # """,
    # """
    # European Space Agency https://earth.esa.int/eogateway/search?category=data: a surplus of incredible open-source data collected over the last decades.
    # NASA https://data.nasa.gov/dataset/: The NASA catalogue is open to use and home to 25,000+ data sets.
    # OpenTopography https://portal.opentopography.org/datasets LiDAR for High-res canopy-penetrating elevation (1-10m).
    #
    # ============
    #
    # Following data sources, from registry.opendata.aws, can be read using S3 Download Tool and downloaded using S3 Download Tool to the data folder for example s3://sentinel-s2-l2a/tiles/20/N/KF/2025/5/22/0/R60m/TCI.jp2 and output file sentinel-s2-l2a_tiles_20_N_KF_2025_5_22_0_R60m_TCI.jp2.
    # If available first read the inventory bucket with S3 Read Tool to see if the files for the specified coordinates exist, then go for the requester-pays full data with S3 Download Tool.
    # ----
    # Sentinel-2 on AWS S3 https://registry.opendata.aws/sentinel-2/ optical imagery for 10m, 13-band scenes (good for vegetation scars).
    # Documentation on how to use : https://roda.sentinel-hub.com/sentinel-s2-l1c/readme.html , https://roda.sentinel-hub.com/sentinel-s2-l2a/readme.html .
    # Available S3 buckets:
    # Level 1C scenes and metadata, in Requester Pays S3 bucket s3://sentinel-s2-l1c ;
    # S3 Inventory files for L1C (ORC and CSV) s3://sentinel-inventory/sentinel-s2-l1c ;
    # Level 2A scenes and metadata, in Requester Pays S3 bucket s3://sentinel-s2-l2a ;
    # S3 Inventory files for L2A (ORC and CSV) s3://sentinel-inventory/sentinel-s2-l2a ;
    # Zipped archives for each L1C product with 3 day retention period, in Requester Pays bucket s3://sentinel-s2-l1c-zips ;
    # Zipped archives for each L2A product with 3 day retention period, in Requester Pays bucket s3://sentinel-s2-l2a-zips ;
    # ----
    # Amazonia EO satellite on AWS S3:  https://registry.opendata.aws/amazonia/ .
    # Available S3 buckets:
    # STAC static catalog s3://br-eo-stac-1-0-0 ;
    # Amazonia 1 imagery (COG files, quicklooks, metadata) s3://brazil-eosats ;
    #
    #
    # """,
    agent=data_collector,
    expected_output="For the proposed coordinates output the coordinates again as in the input then output High-resolution satellite imagery, "
    # "LiDAR data. Binary data output, like images, should be either in datauri string format or public url to be used into next tasks."
    # "S3 object reference should be downloaded with the S3 Download Tool to the data folder and output should be the file path ex ./data/sentinel-s2-l2a_tiles_20_N_KF_2025_5_22_0_R60m_TCI.jp2 . "
    # "GEE image reference should be public urls form the tool GEEImageURLTool."
                    "Sentinel image reference should be public urls form the tool Sentinel HUB S3 URL."
                    "The url should not lead to non-existing pages or 404 errors or content under paywall, login or S3 bucket not existing or access denied.",
    # human_input=True
)

analysis_task = Task(
    description="""For the data in the input:
    - list it ;
    - check if it is available. For example if it's an URL check that it is not a malformed url or url that is leading to a 404 or non-existing page.
     and then pass the links to the Satellite Imagery Analysis Tool ;
    Using the images in the input Identify:
    - Vegetation spectral anomalies (NDVI/NDWI);
    - Terrain roughness patterns;
    - Legend-described geological features;
    - Multispectral analysis of satellite imagery;
    - Detect features algorithmically (e.g., Hough transform, segmentation model);

    Be more sceptical and critical of the proposed findings.
        """,
    agent=image_analyst,
    expected_output="List the input first."
                    "Potential site locations based on input data analysis. Output the coordinates (latitude, longitude, radius) "
                    "in WGS84 format followed by the analysis. Use a 1 to 100 scale to rate the findings where 1 is not likely it "
                    "is a potential site and 100 is very likely."
                    "Add google,bing and livingatlas maps direct links with zoomed in to the features detected.",
    human_input=True
)

validation_task = Task(
    description="""Verify coordinates using:
    - Satellite image analysis;
    - Textual location descriptions;
    - Cross-reference with Historical maps;
    - Cross-reference with historical text (diary snippet, oral map);
    """,
    agent=cross_verification,
    expected_output="Confirmed coordinates with high confidence",
    human_input=True
)

report_task = Task(
    description="""Produce final report with:
    - Confirmed coordinates (WGS84) of at least 1 potential site;
    - Confidence scoring;
    - Compares the discovery to an already known archaeological feature;""",
    agent=reporting_agent,
    expected_output="Verified report with confirmed coordinates and recommendations. "
                    "Include also the google, bing and livingatlas.arcgis.com/wayback/ maps link to the coordinates.",
    human_input=True
)

# Assemble crew with workflow
discovery_crew = Crew(
    agents=[researcher, data_collector, image_analyst, cross_verification, reporting_agent],
    tasks=[
        research_task,
        data_task,
        analysis_task,
        validation_task,
        report_task
    ],
    process=Process.sequential,
    verbose=True,
    # memory=True,
    # Long-term memory for persistent storage across sessions
    # long_term_memory = LongTermMemory(
    #     storage=LTMSQLiteStorage(
    #         db_path="crew/long_term_memory_storage.db"
    #     )
    # ),
    # Short-term memory for current context using RAG
    # short_term_memory = ShortTermMemory(
    #     storage = RAGStorage(
    #         embedder_config={
    #             "provider": "openai",
    #             "config": {
    #                 "model": 'text-embedding-3-small'
    #             }
    #         },
    #         type="short_term",
    #         path="crew/short_term_memory/"
    #     ),
    # ),
    # Entity memory for tracking key information about entities
    # entity_memory = EntityMemory(
    #     storage=RAGStorage(
    #         embedder_config={
    #             "provider": "openai",
    #             "config": {
    #                 "model": 'text-embedding-3-small'
    #             }
    #         },
    #         type="short_term",
    #         path="crew/entity_memory/"
    #     )
    # ),
)

result = discovery_crew.kickoff()
print(result)

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
https://www.tandfonline.com/doi/full/10.1080/00934690.2017.1417198"""

online_research_repositories = """
Online Research Repositories :

    Internet Archive Sources https://archive.org/search?query=lost+city+of+z for a library of text, audio, and video material to sort through.

    Library of Congress public‑domain expedition books https://www.loc.gov/resource/gdclccn.02029950/?st=gallery – contains detailed river‑mile diaries and
    Indigenous village positions you can geocode."""

research_task = f"""Conduct remote archeological research to identify potential new archeological sites in the Amazon river region.
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
    Avoid high populated regions like cities and towns. Do not pick locations in the 20km radius of Santarém city center.
    Do not select locations on deep waters.
    Focus on the southern part of the amazon river bazin. For example between the -6 and -14 degrees latitude and between -72 and -55 longitude. 

    Cross-check against published geoglyph databases and academic reports so you’re not researching already known sites, 
    but new site adjacent to already known sites is allowed.
    Replace prohibited words like swastika or any other prohibited word with the appropriate word or description that is
    allowed, like 'geoglyph', in the search, search output, prompts and in the output.
    
    Expected output: 
    One potential new archeological site based on the research with highest probability 
    of new findings. Urls to public resources to back the rationale. Must have at least one historical map or text. Use WGS84 for coordinates.
    """
    # """The output should be a short name, a list of coordinates
    # (latitude, longitude, radius) in WGS84 format followed by a short rationale, followed by direct
    # links to the google, bing, sentinel hub https://apps.sentinel-hub.com/eo-browser/?zoom={{zoom}}&lat={{lat}}&lng={{lang}} and livingatlas https://livingatlas.arcgis.com/wayback/#active=34007&mapCenter={{long}}%2C{{lat}}%2C14 maps with satellite layer and proper zoom level.
    # """

data_collection_task ="""For the potential new archeological site proposed, collect following satellite imagery : 
    - ESA Sentinel-2 imagery (10m resolution); 
    - SRTM Elevation data (10m resolution); 
    - Landsat 8 L2 imagery (30m resolution); 
    - NDVI and NDWI (10m resolution); 
                
    Images should not have more than 20% cloud cover.
    
    Some sources to get you started (but do not limit yourself to these):
    Satellite imagery and map sources:
    Sentinel-2 10m on Sentinel Hub using Sentinel HUB S3 Tool.
    Landsat8 L2 30m on Sentinel Hub using Sentinel HUB S3 Tool
    Copernicus DEM 30m on Sentinel Hub using Sentinel HUB S3 Tool. 
    For Sentinel, Landsat and DEM images, use the Sentinel HUB S3 URL Tool to get the public PNG url by passing lat long coordinates and radius in meters to the tool.
    Pass a bigger radius to the Sentinel HUB S3 URL Tool than the possible site radius - at least 15000m and at most 25000m.
    Always use the Sentinel HUB S3 URL and make sure the tool returns urls before continuing.
    
    Expected output: 
    For the proposed coordinates output the coordinates again as in the input then output High-resolution satellite imagery.
    Sentinel image reference should be public urls form the tool Sentinel HUB S3 URL.
    The url should not lead to non-existing pages or 404 errors or content under paywall, login or S3 bucket not existing or access denied."""

# Be realistic - it is fine to not find anything worthy of archaeological or historical value in the images.
image_analysis_task = f"""List all the images you received and state their: label, size, received by you in pixels.
    Perform remote sensing on the attached images for archaeological anomalies.
    Analyze these layers together and propose any new potential archaeological sites (e.g., mounds, canals, earthworks, or other human-made anomalies) that appear in this area.
    Identify hotspots and pin point them with lat lon, radius and x,y px from top left corner of the image. Add a rationale. 
    
    Use only the data from the attached here images and do not use external knowledge.
    Do not assume any facts or features not directly observable in the image data.
    Avoid guessing, hallucinating, or inferring based on prior geographical or historical knowledge.
    If an observation cannot be confirmed from the data provided, respond with: "Not enough data in the image to determine this."
    
    Explain which spectral/DEM cues led you to flag it (e.g., subtle mound shape in DEM + vegetation anomaly in NDVI, linear discoloration in false-color, moisture signature in NDWI, etc.) 
    
    Additionally to the identified archaeological hotspots: add one exactly at the bottom right corner of the image for debugging.
    
    When you find something worthy give a lot more info and details.
    All images have the same coordinates and cover the same area, therefore can be overlaid one on top of each-other.
    Center of the images correspond to the proposed general potential site lat and long.
    Give each identified hotspot a score from 1 to 100 based on the likelihood of being new historical or archaeological findings.
    Use WGS84 for coordinates.
    Do not include next steps or recommendations in the output."""
# """
# All original images have a resolution of 10 meters per pixel.
# """
# """
# Corners of the images correspond to the proposed general potential site bbox.
# """
# """
#     Additionally to the identified archaeological hotspots: add
#     one exactly with the center on the bottom left corner of the image.
#     Then one exactly with the center on the top right corner of the image.
# """
# """
#     For DEM the resolution is 30m and for all the rest of the images it is 10m. Use this info to calculate hotspot
#     precise coordinates based of the distance from center of image.
# """
# """
# Additionally to the identified archaeological hotspots:
#     add one hotspot right in the middle of the image and 4 on each of the corners of the image so that the circle drawn from center of hotspot with the radius is tangent to the edges of the image and is fully inside the image.
# """

validation_task = """Verify coordinates using:
    - Provided Satellite image analysis;
    - Textual location descriptions;
    - Cross-reference with Historical maps;
    - Cross-reference with historical text (diary snippet, oral map).
    Give each identified hotspot a score from 1 to 100 bsed on the likelihood of being new historical or archaeological findings.
    Be realistic - if you do not see potential hotspots to have real archaeological or historical that is fine. You can reevaluate the hotspots' score as well.
    Replace prohibited words like swastika or any other prohibited word with the appropriate word or description that is
    allowed, like 'geoglyph', in the search, search output, prompts and in the output
    Use WGS84 for coordinates.
    Do not include next steps or recommendations in the output. """

reporting_task = """Produce final report with:
    - Confirmed coordinates (WGS84) of at least 1 potential site;
    - Confidence scoring 1-100 where 1 is not likely and 100 is likely that the potential site is worth further investigation;
    - Compares the discovery to an already known archaeological feature;
    Verified report with confirmed coordinates and recommendations. 
    Include also the google, bing, sentinel hub, livingatlas map links to the coordinates.
    If no hotspots identified by the validation or image analysis keep the report short as you do not have any confirmed potential site and report a false finding.
    Do not include the debug hotspots in the report."""

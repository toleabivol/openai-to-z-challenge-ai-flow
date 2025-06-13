
    # Image Analysis Summary

    ## Raw Analysis
    
    Received images and their sizes in pixels:
- copernicus_dem: 512x512 px
- landsat89_l2_true_color: 512x512 px
- landsat89_l2_false_color: 512x512 px
- s2_l2a_true_color: 512x512 px
- s2_l2a_false_color: 512x512 px
- s2_l2a_B08_nir: 512x512 px
- s2_l2a_NDVI: 512x512 px
- s2_l2a_NDWI: 512x512 px
- s2_l2a_NBR: 512x512 px

Analysis of images for archaeological anomalies:

1. copernicus_dem (Digital Elevation Model):
- Shows subtle elevation variations with some rounded and elongated mound-like features mainly in the central and upper central parts of the image.
- These features appear as lighter gray areas indicating slightly higher elevation compared to surroundings.

2. landsat89_l2_true_color and s2_l2a_true_color:
- Both true color images show vegetation and soil patterns.
- There are irregular patches of lighter green and brownish areas in the central and lower central parts, possibly indicating soil disturbance or different vegetation.

3. landsat89_l2_false_color and s2_l2a_false_color:
- False color images highlight vegetation health and moisture.
- The dark curvilinear features visible in false color images correspond to water or wetland channels.
- Some enclosed shapes with distinct boundaries are visible, especially near the center, which may indicate earthworks or anthropogenic features.

4. s2_l2a_B08_nir (Near Infrared):
- Highlights vegetation vigor.
- The irregular patches seen in true color are more contrasted here, with some areas showing lower NIR reflectance, possibly indicating soil or disturbed ground.

5. s2_l2a_NDVI (Normalized Difference Vegetation Index):
- Shows vegetation density.
- Some circular and semi-circular patches with lower NDVI values are visible near the center and slightly to the right, suggesting less dense or different vegetation.

6. s2_l2a_NDWI (Normalized Difference Water Index):
- Highlights water presence.
- The dark curvilinear features correspond to water channels.
- A distinct bright patch near the center-right indicates a water body or wetland.

7. s2_l2a_NBR (Normalized Burn Ratio):
- Shows differences in vegetation and soil moisture.
- Some irregular shapes with different reflectance values are visible near the center.

Identified Hotspots:

Hotspot 1:
- Location: Approx center of image at x=260 px, y=280 px
- Lat/Lon: approx -12.083, -53.828
- Radius: 300 m (approx 30 px)
- Rationale: This area shows a subtle mound-like elevation in DEM, combined with irregular vegetation patterns in NDVI and NIR, and distinct boundaries in false color images. The combination suggests a possible anthropogenic earthwork or mound.
- Score: 75

Hotspot 2:
- Location: Upper central part at x=230 px, y=150 px
- Lat/Lon: approx -12.070, -53.832
- Radius: 250 m (approx 25 px)
- Rationale: A rounded elevation feature in DEM with corresponding vegetation anomaly in NDVI and NIR, and a distinct boundary in false color images. Possible mound or earthwork.
- Score: 70

Hotspot 3:
- Location: Center-right near water body at x=320 px, y=270 px
- Lat/Lon: approx -12.083, -53.823
- Radius: 200 m (approx 20 px)
- Rationale: Presence of a water body or wetland with surrounding irregular shapes visible in DEM and false color images, possibly indicating human modification or canal.
- Score: 65

Hotspot 4 (Debugging):
- Location: Bottom right corner at x=511 px, y=511 px
- Lat/Lon: approx -12.03497, -53.78534
- Radius: 50 m (approx 5 px)
- Rationale: Debugging point as requested.
- Score: 1

Summary: The analysis of DEM combined with vegetation indices (NDVI, NIR) and false color imagery reveals several subtle mound-like and irregular features with distinct boundaries that may represent archaeological earthworks or human-made modifications. The presence of water bodies and channels with adjacent irregular shapes further supports potential anthropogenic landscape modifications.
    
    
    ## Hotspots
    
    
    ### Hotspot 1
    
    - **Latitude:** -12.083
    - **Longitude:** -53.828
    - **Radius:** 300 meters
    - **Rationale:** Subtle mound-like elevation in DEM combined with irregular vegetation patterns in NDVI and NIR, and distinct boundaries in false color images, suggesting possible anthropogenic earthwork or mound.
    - **Score:** 75 / 100
    
    
    **Maps:**
    
    - [Map 1](https://www.google.com/maps/@-12.083,-53.828,15z/data=!3m1!1e3)
    
    - [Map 2](https://www.bing.com/maps?cp=-12.083~-53.828&lvl=15&style=h)
    
    - [Map 3](https://livingatlas.arcgis.com/wayback/#active=34007&mapCenter=-53.828%2C-12.083%2C15)
    
    - [Map 4](https://apps.sentinel-hub.com/eo-browser/?zoom=15&lat=-12.083&lng=-53.828)
    
    
    
    ---
    
    ### Hotspot 2
    
    - **Latitude:** -12.07
    - **Longitude:** -53.832
    - **Radius:** 250 meters
    - **Rationale:** Rounded elevation feature in DEM with corresponding vegetation anomaly in NDVI and NIR, and distinct boundary in false color images, indicating possible mound or earthwork.
    - **Score:** 70 / 100
    
    
    **Maps:**
    
    - [Map 1](https://www.google.com/maps/@-12.07,-53.832,15z/data=!3m1!1e3)
    
    - [Map 2](https://www.bing.com/maps?cp=-12.07~-53.832&lvl=15&style=h)
    
    - [Map 3](https://livingatlas.arcgis.com/wayback/#active=34007&mapCenter=-53.832%2C-12.07%2C15)
    
    - [Map 4](https://apps.sentinel-hub.com/eo-browser/?zoom=15&lat=-12.07&lng=-53.832)
    
    
    
    ---
    
    ### Hotspot 3
    
    - **Latitude:** -12.083
    - **Longitude:** -53.823
    - **Radius:** 200 meters
    - **Rationale:** Water body or wetland with surrounding irregular shapes visible in DEM and false color images, possibly indicating human modification or canal.
    - **Score:** 65 / 100
    
    
    **Maps:**
    
    - [Map 1](https://www.google.com/maps/@-12.083,-53.823,15z/data=!3m1!1e3)
    
    - [Map 2](https://www.bing.com/maps?cp=-12.083~-53.823&lvl=15&style=h)
    
    - [Map 3](https://livingatlas.arcgis.com/wayback/#active=34007&mapCenter=-53.823%2C-12.083%2C15)
    
    - [Map 4](https://apps.sentinel-hub.com/eo-browser/?zoom=15&lat=-12.083&lng=-53.823)
    
    
    
    ---
    
    ### Hotspot 4
    
    - **Latitude:** -12.034970088675234
    - **Longitude:** -53.78534307971686
    - **Radius:** 50 meters
    - **Rationale:** Debugging hotspot at bottom right corner of the image as requested.
    - **Score:** 1 / 100
    
    
    **Maps:**
    
    - [Map 1](https://www.google.com/maps/@-12.034970088675234,-53.78534307971686,18z/data=!3m1!1e3)
    
    - [Map 2](https://www.bing.com/maps?cp=-12.034970088675234~-53.78534307971686&lvl=18&style=h)
    
    - [Map 3](https://livingatlas.arcgis.com/wayback/#active=34007&mapCenter=-53.78534307971686%2C-12.034970088675234%2C18)
    
    - [Map 4](https://apps.sentinel-hub.com/eo-browser/?zoom=18&lat=-12.034970088675234&lng=-53.78534307971686)
    
    
    
    ---
    
    
    
import os
from matplotlib.colors import LightSource, Normalize
from PIL import Image
import earthaccess
import pdal
import json
import richdem as rd
import rasterio
import numpy as np
from scipy.ndimage import uniform_filter
import dotenv
import logging
from .sentinel_hub_png import s3_upload_and_get_link, create_safe_filename

LOGGER = logging.getLogger('lidar_data')
LOGGER.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s - %(message)s")
handler.setFormatter(formatter)
LOGGER.addHandler(handler)

dotenv.load_dotenv()


async def get_lidar_data(bbox, root_output_folder):
    try:
        output_folder = f'{root_output_folder}/lidar'
        input_folder = f'{root_output_folder}/lidar/downloads'
        # output_folder = 'output_data/lidar/' + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # bbox = (-53.832, -11.995829, -53.830, -11.986777)

        # ====== Get lidar data from Earthaccess =========
        results = earthaccess.search_data(
            short_name="LiDAR_Forest_Inventory_Brazil_1644",
            bounding_box=bbox,
            temporal=("2017-01-01", "2019-12-31"),
            # provider="ORNL_DAAC",
            # doi="10.3334/ORNLDAAC/1644"
        )

        if results:

            LOGGER.info(f"Found nr results: {len(results)}")
            LOGGER.info(results)

            files = earthaccess.download(results, input_folder)
            LOGGER.info(files)

            # === START keep one version of each
            merged = f"{output_folder}/merged.laz"
            noise_removed = f"{output_folder}/noise_removed.laz"
            dem_tif = f"{output_folder}/dem.tif"

            # ==== or below =====

            # merged = "input_data/lidar/DUC_A01_2008_laz_10.laz"
            # noise_removed = "output_data/lidar/noise_removed.laz"
            # dem_tif = "output_data/lidar/dem.tif"
            # === FINISH keep one version of each

            dsm_tif = f"{output_folder}/dsm.tif"

            os.makedirs(output_folder, exist_ok=True)

            laz_files = [
                os.path.join(input_folder, f)
                for f in os.listdir(input_folder)
                if f.endswith(".laz") and not f.endswith(".copc.laz") and os.path.isfile(os.path.join(input_folder, f))
            ]

            LOGGER.info(f"Found {len(laz_files)} .laz files")

            merge_pipeline = {
                "pipeline": laz_files + [
                    {"type": "filters.merge"},
                    {"type": "writers.las", "filename": merged}
                ]
            }

            pipeline = pdal.Pipeline(json.dumps(merge_pipeline))
            pipeline.execute()
            LOGGER.info(f"Merged .laz saved as {merged}")

            # no need for noise removal as far as i see, since below we use 2:2 only
            # pipeline = {
            #   "pipeline": [
            #     merged,
            #     {"type":"filters.range", "limits":"Classification![7:7]"},
            #     noise_removed
            #   ]
            # }
            # pd = pdal.Pipeline(json.dumps(pipeline))
            # pd.execute()
            # LOGGER.info("Lidar noise removed")

            pipeline_json = {
                "pipeline": [
                    merged,
                    {"type": "filters.range", "limits": "Classification[2:2]"},
                    {
                        "type": "writers.gdal",
                        "filename": dem_tif,
                        "resolution": 1,
                        "output_type": "idw",
                        "window_size": 3,
                        "radius": 0.5,
                        "data_type": "float32",
                        "gdaldriver": "GTiff",
                        "nodata": -9999
                    }
                ]
            }

            pipeline = pdal.Pipeline(json.dumps(pipeline_json))
            pipeline.execute()
            LOGGER.info(f"DEM generated: {dem_tif}")

            dem_png_files = convert_dem_to_png(dem_tif)

            dem_png_path, dem_png_size = dem_png_files["dem"]
            dem_png_filename = create_safe_filename(f"dem_high_resolution_{bbox[0]}_{bbox[1]}",
                                            '.png', True)
            dem_s3_url = await s3_upload_and_get_link(dem_png_path, 'earthaccess', dem_png_filename)

            hillshade_png_path, hillshade_png_size = dem_png_files["hillshade"]
            hillshade_png_filename = create_safe_filename(f"hillshade_high_resolution_{bbox[0]}_{bbox[1]}",
                                            '.png', True)
            hillshade_s3_url = await s3_upload_and_get_link(hillshade_png_path, 'earthaccess', hillshade_png_filename)

            try:
                # Terrain attributes from DEM
                dem = rd.LoadGDAL(dem_tif)
                aspect = rd.TerrainAttribute(dem, attrib='aspect')
                slope = rd.TerrainAttribute(dem, attrib='slope_degrees')
                curvature = rd.TerrainAttribute(dem, attrib='profile_curvature')

                rd.SaveGDAL(f'{output_folder}/aspect.tif', aspect)
                rd.SaveGDAL(f'{output_folder}/slope.tif', slope)
                rd.SaveGDAL(f'{output_folder}/curvature.tif', curvature)
                LOGGER.info("Built aspect.tif, slope.tif, curvature.tif")

                # dem_smoothed = rd.TerrainAttribute(dem, attrib='mean')
                # lrm = dem - dem_smoothed
                # rd.SaveGDAL(f'{output_folder}/lrm.tif', lrm)
                # LOGGER.info("Built lrm.tif")

                # Intensity
                intensity_pipeline = {
                  "pipeline": [
                    merged,
                    {"type": "filters.range", "limits": "Classification[2:2]"},
                    {
                      "type": "writers.gdal",
                      "filename": f"{output_folder}/intensity_be.tif",
                      "resolution": 1,
                      "output_type": "idw",
                      "radius": 1.0,
                      "window_size": 3,
                      "gdaldriver": "GTiff",
                      "data_type": "float32",
                      "dimension": "Intensity",
                      "nodata": 0
                    }
                  ]
                }
                pl = pdal.Pipeline(json.dumps(intensity_pipeline))
                pl.execute()
                LOGGER.info("Built intensity_be.tif")

                # DSM
                dsm_pipeline = {
                  "pipeline": [
                    merged,
                    {"type": "filters.range", "limits": "ReturnNumber[1:1]"},
                    {
                      "type": "writers.gdal",
                      "filename": dsm_tif,
                      "resolution": 1,
                      "output_type": "max",
                      "data_type": "float32",
                      "gdaldriver": "GTiff",
                      "nodata": -9999
                    }
                  ]
                }
                pl = pdal.Pipeline(json.dumps(dsm_pipeline))
                pl.execute()
                LOGGER.info("Built dsm.tif")

                # CHM
                with rasterio.open(dsm_tif) as dsmd:
                    dsm_array = dsmd.read(1)
                    dsm_meta = dsmd.meta
                with rasterio.open(dem_tif) as demd:
                    dem_array = demd.read(1)
                    dem_meta = demd.meta

                chm = dsm_array - dem_array
                chm[chm < 0] = 0

                canopy_threshold = 5
                chm_masked = np.where(chm <= canopy_threshold, chm, dsm_meta['nodata'])

                dsm_meta.update(dtype='float32', nodata=0)
                with rasterio.open(f'{output_folder}/chm.tif', 'w', **dsm_meta) as dst:
                    dst.write(chm_masked.astype('float32'), 1)

                high_canopy = np.where(chm > canopy_threshold, chm, 0)
                with rasterio.open(f'{output_folder}/chm_high_canopy.tif', 'w', **dsm_meta) as dst:
                    dst.write(high_canopy.astype('float32'), 1)

                LOGGER.info("Built chm.tif and chm_high_canopy.tif")

                # TPI
                window_size = 9  # adjust for scale
                mean_dem = uniform_filter(dem_array, size=window_size, mode='nearest')
                tpi = dem_array - mean_dem
                with rasterio.open(f"{output_folder}/tpi.tif", 'w', **dem_meta) as dst:
                    dst.write(tpi.astype('float32'), 1)

                # LRM
                smoothed = uniform_filter(dem_array, size=30, mode='nearest')
                lrm = dem_array - smoothed
                with rasterio.open(f"{output_folder}/lrm.tif", 'w', **dem_meta) as dst:
                    dst.write(lrm.astype('float32'), 1)

                LOGGER.info("Saved TPI and LRM rasters.")
            except Exception as e:
                LOGGER.exception(f"Error in terrain attributes: {e}")

            return {
                "dem_high_resolution" : (dem_s3_url, dem_png_filename, dem_png_size),
                "hillshade_high_resolution" : (hillshade_s3_url, hillshade_png_filename, hillshade_png_size)
            }
        else:
            LOGGER.info("No lidar tiles found.")
            return None
    except Exception as e:
        LOGGER.exception(f"Error in get_lidar_data: {e}")
        return None


def convert_dem_to_png(tif_path, png_path=None, colormap='terrain', hillshade=True):
    """
    Convert a DEM TIF file to a visually appealing PNG image.

    Parameters:
    -----------
    tif_path : str
        Path to the input DEM TIF file
    png_path : str, optional
        Path for the output PNG file. If None, will use the same name as input with .png extension
    colormap : str, optional
        Matplotlib colormap to use for elevation visualization (default: 'terrain')
    hillshade : bool, optional
        Whether to apply hillshading for 3D effect (default: True)

    Returns:
    --------
    str
        Path to the created PNG file
    """


    if png_path is None:
        png_path = tif_path.replace('.tif', '.png')
    hillshade_path = png_path.replace('.png', '_hillshade.png')

    with rasterio.open(tif_path) as src:
        dem = src.read(1)  # Read the first band

        # Mask out no-data values
        dem = np.ma.masked_equal(dem, src.nodata)

        # Apply a buffer to min and max elevation to improve contrast
        buffer = (np.max(dem) - np.min(dem)) * 0.05  # 5% buffer
        vmin = np.min(dem) - buffer
        vmax = np.max(dem) + buffer

        # Normalize elevation with buffer
        norm = Normalize(vmin=vmin, vmax=vmax, clip=True)
        dem_normalized = norm(dem.filled(0))  # Replace masked with 0 for image

        # Convert to 8-bit grayscale (0-255)
        dem_uint8 = (dem_normalized * 255).astype(np.uint8)

        # Create a PIL image and save as PNG
        img = Image.fromarray(dem_uint8)
        img.save(png_path)
        LOGGER.info(f"DEM converted and saved to {png_path}")

        # Generate hillshade using matplotlib's LightSource
        ls = LightSource(azdeg=315, altdeg=45)
        hillshade_data = ls.hillshade(dem.filled(np.nan), vert_exag=1.0, dx=1, dy=1)

        # Convert hillshade to 8-bit, Replace NaNs with 0 before casting
        hillshade_uint8 = (np.nan_to_num(hillshade_data, nan=0.0) * 255).astype(np.uint8)
        hill_img = Image.fromarray(hillshade_uint8)
        hill_img.save(hillshade_path)
        LOGGER.info(f"Hillshade image saved to {hillshade_path}")

    LOGGER.info(f"DEM converted to PNG: {png_path} {hillshade_path}")
    return {"dem": (png_path, img.size), "hillshade": (hillshade_path, hill_img.size)}

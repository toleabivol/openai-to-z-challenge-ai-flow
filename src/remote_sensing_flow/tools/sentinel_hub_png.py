import asyncio
import shutil
import tempfile
import boto3
from asyncio import gather, to_thread
from crewai.tools import BaseTool
from dotenv import load_dotenv
import rasterio
import numpy as np
import os
# from ..helpers import create_safe_filename
from sentinelhub import (
    CRS, BBox, DataCollection, MimeType,
    MosaickingOrder, SentinelHubRequest,
    bbox_to_dimensions, SHConfig, SentinelHubStatistical
)
import logging
LOGGER = logging.getLogger('remote_sensing_flow_s_hub_png')
LOGGER.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s - %(message)s")
handler.setFormatter(formatter)
LOGGER.addHandler(handler)
load_dotenv()

def create_safe_filename(base_name: str, extension: str = "", timestamp:bool = False) -> str:
    import datetime
    import re
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

class SentinelS3PngUploader(BaseTool):
    name: str = "Sentinel HUB S3 URL"
    description: str = ("Fetches Sentinel-2, Landsat-8-9 and Copernicus DEM data and uploads PNGs to S3 and returns S3 "
                        "signed urls creating temporarily public image urls.")

    async def _run(self, lat: float, lon: float, bbox: tuple[float,float,float,float],
                   output_folder: str = None) -> dict[str,tuple]:
        LOGGER.info(f"Requested images with: {lat} {lon} {bbox}")
        bbox = BBox(bbox , CRS.WGS84)
        config = SHConfig()
        config.instance_id = os.environ.get("SENTINEL_HUB_INSTANCE_ID")
        config.sh_client_id = os.environ.get("SENTINEL_HUB_CLIENT_ID")
        config.sh_client_secret = os.environ.get("SENTINEL_HUB_CLIENT_SECRET")

        if not config.sh_client_id or not config.sh_client_secret:
            raise ValueError("Missing Sentinel Hub credentials")

        date_from = '2023-01-01'
        date_to = '2025-05-25'

        LOGGER.info(f"Getting min max elevation from DEM GeoTIFF")

        # elevation_min, elevation_max = self.get_elevation_stats(config, bbox, date_from, date_to)
        script = """
        //VERSION=3
        function setup() {
          return {
            input: ["DEM"],
            output: { bands: 1, sampleType: "FLOAT32" }
          };
        }
        
        function evaluatePixel(sample) {
          return [sample.DEM];
        }
        """
        label, s3_url, filename, size = await self.process_image("elevation_dem", lat, lon, script, config, bbox, date_from, date_to, output_folder, False)
        elevation_min, elevation_max = self.get_elevation_from_dem_image(os.path.join(output_folder, filename))

        LOGGER.info(f"Min elevation: {elevation_min:.2f} m")
        LOGGER.info(f"Max elevation: {elevation_max:.2f} m")

        # I think we need to add some buffer?
        elevation_min += 10
        elevation_max += 10

        evalscripts = {
            #  DEM values are in meters and can be negative for areas which lie below sea level,
            #  so it is recommended to set the output format in your evalscript to FLOAT32.
            # But we cannot do that since FLOAT32 does not work with PNG but only with TIFF
            "copernicus_dem": """
                //VERSION=3
                function setup() {
                  return {
                    input: ["DEM"],
                    output: {
                      bands: 1,
                      sampleType: "UINT8"
                    }
                  };
                }
                
                // Amazon‐focused window: 0–200 m above sea level.
                // Elevations below 0 m clamp at 0; above 200 m clamp at 200.
                const DEM_MIN = """ + str(elevation_min) + """;
                const DEM_MAX = """ + str(elevation_max) + """;
                
                function evaluatePixel(sample) {
                  let elev = sample.DEM;
                
                  // 1) Clamp elevation to [DEM_MIN..DEM_MAX m]
                  if (elev < DEM_MIN) elev = DEM_MIN;
                  else if (elev > DEM_MAX) elev = DEM_MAX;
                
                  // 2) Normalize → [0..1]
                  let norm = (elev - DEM_MIN) / (DEM_MAX - DEM_MIN);
                
                  // 3) Scale to [0..255] and round to integer
                  let byteVal = Math.round(norm * 255.0);
                
                  return [byteVal];
                }

            """,
            # "mapzen_dem": """
            #     //VERSION=3
            #     function setup() {
            #       return {
            #         input: ["DEM"],
            #         output: {
            #           bands: 1,
            #           sampleType: "UINT8"
            #         }
            #       };
            #     }
            #
            #     // Amazon‐focused window: 0–500 m above sea level.
            #     // Elevations below DEM_MIN m clamp at DEM_MIN; above 200 m clamp at 200.
            #     const DEM_MIN = """ + elevation_min + """;
            #     const DEM_MAX = """ + elevation_max + """;
            #
            #     function evaluatePixel(sample) {
            #       let elev = sample.DEM;
            #
            #       // 1) Clamp elevation to [DEM_MIN..DEM_MAX m]
            #       if (elev < DEM_MIN) elev = DEM_MIN;
            #       else if (elev > DEM_MAX) elev = DEM_MAX;
            #
            #       // 2) Normalize → [0..1]
            #       let norm = (elev - DEM_MIN) / (DEM_MAX - DEM_MIN);
            #
            #       // 3) Scale to [0..255] and round to integer
            #       let byteVal = Math.round(norm * 255.0);
            #
            #       return [byteVal];
            #     }
            # """,
            "landsat89_l2_true_color": """
                //VERSION=3
                function setup() {
                    return {
                        input: [{
                            bands: ["B02", "B03", "B04"]
                        }],
                        output: {
                            bands: 3,
                            sampleType: "AUTO" // default value - scales the output values from [0,1] to [0,255].
                        }
                    };
                }
                function evaluatePixel(s) {
                   return [3.5 * s.B04, 3.5 * s.B03, 3.5 * s.B02]  // 3.5 factor to increase brightness
                }
            """,
            # False Color Composite (NIR, Red, Green)
            "landsat89_l2_false_color": """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B05", "B04", "B03"],
                        output: { 
                            bands: 3,
                            sampleType: "AUTO"
                        }
                    };
                }
                
                function evaluatePixel(sample) {
                    return [sample.B05, sample.B04, sample.B03];
                }
            """,
            "s2_l2a_true_color": """
                //VERSION=3
                function setup() {
                    return {
                        input: [{
                            bands: ["B02", "B03", "B04"]
                        }],
                        output: {
                            bands: 3,
                            sampleType: "AUTO" // default value - scales the output values from [0,1] to [0,255].
                        }
                    };
                }
                function evaluatePixel(s) {
                   return [3.5 * s.B04, 3.5 * s.B03, 3.5 * s.B02]  // 3.5 factor to increase brightness
                }
            """,
            "s2_l2a_false_color": """
                //VERSION=3
                function setup() {
                    return {
                        input: [{
                            bands: ["B08", "B04", "B03"]
                        }],
                        output: {
                            bands: 3,
                            sampleType: "AUTO"
                        }
                    };
                }
                function evaluatePixel(s) {
                   return [s.B08, s.B04, s.B03]
                }
            """,
            "s2_l2a_B08_nir": """
                //VERSION=3
                function setup() {
                    return { 
                        input: ["B08"], 
                        output: { 
                            bands: 1,
                            sampleType: "AUTO" 
                        }
                    };
                }
                function evaluatePixel(s) {
                    return [s.B08];
                }
            """,
            "s2_l2a_NDVI": """
                //VERSION=3
                function setup() {
                    return { 
                        input: ["B04", "B08"], 
                        output: { 
                            bands: 1,
                            sampleType: "UINT8" 
                        }
                    };
                }
                function evaluatePixel(s) {
                  let ndvi = (s.B08 - s.B04) / (s.B08 + s.B04);
                  // Remap: [-1,1] → [0,1], then [0,1] → [0,255].
                  let scaled = Math.round(((ndvi + 1.0) / 2.0) * 255.0);
                  return [scaled];
                }
            """,
            "s2_l2a_NDWI": """
                //VERSION=3
                function setup() {
                    return { input: ["B03", "B08"], output: { bands: 1, sampleType: "UINT8"  } };
                }
                function evaluatePixel(s) {
                    let ndwi = (s.B03 - s.B08) / (s.B03 + s.B08);
                    let scaled = Math.round(((ndwi + 1.0) / 2.0) * 255.0);
                    return [scaled];
                }
            """,
            "s2_l2a_NBR": """
                //VERSION=3
                function setup() {
                    return { input: ["B08", "B12"], output: { bands: 1, sampleType: "UINT8" } };
                }
                function evaluatePixel(s) {
                    let nbr = (s.B08 - s.B12) / (s.B08 + s.B12);
                    let scaled = Math.round(((nbr + 1.0) / 2.0) * 255.0);
                    return [scaled];
                }
            """
        }


        tasks = []
        for label, script in evalscripts.items():
            tasks.append(self.process_image(label, lat, lon, script, config, bbox, date_from, date_to, output_folder))
        sentinelhub_results = await gather(*tasks)

        result_urls = {label: (url, filename, size) for label, url, filename, size in sentinelhub_results}

        return result_urls

    async def process_image(self, label, lat, lon, script, config, bbox, date_from, date_to, output_folder, upload_to_s3: bool = True):

        s3 = boto3.client('s3')
        bucket_name = os.getenv("S3_DATA_BUCKET")

        LOGGER.info(f'Requesting sentinel hub for {label}')
        tmp_output_folder = tempfile.mkdtemp(label)
        data_collection = DataCollection.SENTINEL2_L2A
        resolution = 10
        if label.startswith('landsat'):
            data_collection = DataCollection.LANDSAT_OT_L2
        elif label in ['copernicus_dem', 'elevation_dem']:
            data_collection = DataCollection.DEM_COPERNICUS_30
            # resolution = 30
        elif label == 'mapzen_dem':
            data_collection = DataCollection.DEM_MAPZEN
            # resolution = 30

        size = bbox_to_dimensions(bbox, resolution=resolution)
        LOGGER.info(size)

        request = SentinelHubRequest(
            evalscript=script,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=data_collection,
                    time_interval=(date_from, date_to),
                    mosaicking_order=MosaickingOrder.LEAST_CC,
                )
            ],
            responses=[SentinelHubRequest.output_response("default", MimeType.TIFF if label == 'elevation_dem' else MimeType.PNG)],
            bbox=bbox,
            size=size,
            config=config,
            data_folder=tmp_output_folder,
        )

        def request_save_data(s_hub_request):
            s_hub_request.save_data()

        def request_get_data(s_hub_request):
            s_hub_request.get_data()

        if output_folder:
            await to_thread(request_save_data, request)
        else:
            return await to_thread(request_get_data, request)

        png_path = None
        for root, _, files in os.walk(tmp_output_folder):
            for file in files:
                if file.endswith('.tiff' if label == 'elevation_dem' else '.png'):
                    png_path = os.path.join(root, file)
                    break
            if png_path:
                break

        if not png_path:
            raise FileNotFoundError(f"PNG/TIFF file not found in {tmp_output_folder} for {label}.")

        #TODO optimize image losslessly with pngcrush ? should not influence image analysis later

        filename = create_safe_filename(f"{label}_{lat}_{lon}_{date_from}_{date_to}", '.tiff' if label == 'elevation_dem' else '.png', True)

        s3_url = ''
        if upload_to_s3:
            LOGGER.info(f'Uploading to s3 {label}')
            key = f"sentinel_hub/{filename}"

            await asyncio.to_thread(s3.upload_file, png_path, bucket_name, key)

            s3_url = await asyncio.to_thread(s3.generate_presigned_url,
                'get_object',
                Params={'Bucket': bucket_name, 'Key': key},
                ExpiresIn=7200
            )

        if output_folder:
            self.copy_and_rename(png_path, output_folder, filename)
        shutil.rmtree(tmp_output_folder)
        return label, s3_url, filename, size

    def copy_and_rename(self, src_path: str, dest_path: str, new_name: str):
        # Copy the file
        shutil.copy(src_path, dest_path)
        old_filename = os.path.basename(src_path)
        # Rename the copied file
        new_path = f"{dest_path}/{new_name}"
        shutil.move(f"{dest_path}/{old_filename}", new_path)

    def get_elevation_stats(self, config, bbox, date_from, date_to):
        """
        Could not get this work - i get an 500 error no matter what i do
        Switching for now to the solution to get the dem image without constraints
        analyze it and then get it again with elevation constraints
        """
        LOGGER.info("Get elevation stats")
        # input_data = SentinelHubStatistical.input_data(
        #     data_collection=DataCollection.DEM_COPERNICUS_30,
        #     other_args={
        #         'type' : "DEM"
        #     }
        # )

        input_data = [{
            "type": "dem",
            "dataFilter": {
                "demInstance": "COPERNICUS_30"
            }
        }]

        aggregation = {
            "timeRange": {
                "from": date_to + "T00:00:00Z",
                "to": date_to + "T23:59:59Z"
            },
            "aggregationInterval": {
                "of": "P1D"
            },
            "evalscript": """
                //VERSION=3
                function setup() {
                    return {
                        input: ["DEM"],
                        output: [{ id: "elevation", bands: 1, sampleType: "FLOAT32" }]
                    };
                }
                function evaluatePixel(sample) {
                    return {
                        elevation: [sample.DEM]
                    };
                }
            """
        }

        calculations = {
            "default": {
                "statistics": {
                    "elevation": {
                        "min": {},
                        "max": {}
                    }
                }
            }
        }

        request = SentinelHubStatistical(
            aggregation=aggregation,
            input_data=input_data,
            bbox=bbox,
            # calculations=calculations,
            config=config
        )


        response = request.get_data()
        print(response)
        elevation_stats = response['data'][0]['outputs']['default']['stats']['statistics']

        print(f"Min elevation: {elevation_stats['min']} m")
        print(f"Max elevation: {elevation_stats['max']} m")

        return elevation_stats['min'], elevation_stats['max']

    def get_elevation_from_dem_image(self, filename):
        with rasterio.open(filename) as src:
            # Read the first band (elevation data)
            elevation_data = src.read(1)

            # Mask no-data values
            elevation_data = np.ma.masked_equal(elevation_data, src.nodata)

            # Compute stats
            elevation_min = float(elevation_data.min())
            elevation_max = float(elevation_data.max())

        return elevation_min, elevation_max


if __name__ == "__main__":
    tool = SentinelS3PngUploader()
    b_box = (-67.4, -7.96, -67.2, -7.94)
    result = asyncio.run( tool._run(lat=-7.95, lon=-67.3, bbox=b_box, output_folder='../output/test') )
    LOGGER.info(result)

import asyncio
import shutil
import tempfile
import boto3
from asyncio import gather, to_thread
from crewai.tools import BaseTool
from dotenv import load_dotenv
import os
from ..helpers import create_safe_filename
from sentinelhub import (
    CRS, BBox, DataCollection, MimeType,
    MosaickingOrder, SentinelHubRequest,
    bbox_to_dimensions, SHConfig
)
import logging
LOGGER = logging.getLogger('remote_sensing_flow_s_hub_png')
LOGGER.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
LOGGER.addHandler(handler)
load_dotenv()


class SentinelS3PngUploader(BaseTool):
    name: str = "Sentinel HUB S3 URL"
    description: str = ("Fetches Sentinel-2, Landsat-8-9 and Copernicus DEM data and uploads PNGs to S3 and returns S3 "
                        "signed urls creating temporarily public image urls.")

    async def _run(self, lat: float, lon: float, radius_in_meters: int, output_folder: str = None) -> dict[str,str]:
        LOGGER.info(f"Requested images with: {lat} {lon} {radius_in_meters}")
        delta_deg = radius_in_meters / 111_000.0
        bbox = BBox((lon - delta_deg, lat - delta_deg, lon + delta_deg, lat + delta_deg), crs=CRS.WGS84)
        LOGGER.info(f"Calculated bbox: {bbox}")
        config = SHConfig()
        config.instance_id = os.environ.get("SENTINEL_HUB_INSTANCE_ID")
        config.sh_client_id = os.environ.get("SENTINEL_HUB_CLIENT_ID")
        config.sh_client_secret = os.environ.get("SENTINEL_HUB_CLIENT_SECRET")

        if not config.sh_client_id or not config.sh_client_secret:
            raise ValueError("Missing Sentinel Hub credentials")

        evalscripts = {
            #  DEM values are in meters and can be negative for areas which lie below sea level,
            #  so it is recommended to set the output format in your evalscript to FLOAT32.
            # But we cannot do that since FLOAT32 does not work with PNG but only with TIFF
            "copernicus_dem": """
                function setup() {
                  return {
                    input: ["DEM"],
                    output: { bands: 1 }
                  }
                }
                function evaluatePixel(sample) {
                  return [sample.DEM/1000]
                }
            """,
            "mapzen_dem": """
                function setup() {
                  return {
                    input: ["DEM"],
                    output: { bands: 1 }
                  }
                }
                function evaluatePixel(sample) {
                  return [sample.DEM/1000]
                }
            """,
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
                        output: { bands: 3 }
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
                            bands: 3
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
                    return { input: ["B08"], output: { bands: 1 } };
                }
                function evaluatePixel(s) {
                    return [s.B08];
                }
            """,
            "s2_l2a_NDVI": """
                //VERSION=3
                function setup() {
                    return { input: ["B04", "B08"], output: { bands: 1 } };
                }
                function evaluatePixel(s) {
                    let ndvi = (s.B08 - s.B04) / (s.B08 + s.B04);
                    return [ndvi];
                }
            """,
            "s2_l2a_NDWI": """
                //VERSION=3
                function setup() {
                    return { input: ["B03", "B08"], output: { bands: 1 } };
                }
                function evaluatePixel(s) {
                    let ndwi = (s.B03 - s.B08) / (s.B03 + s.B08);
                    return [ndwi];
                }
            """,
            "s2_l2a_NBR": """
                //VERSION=3
                function setup() {
                    return { input: ["B08", "B12"], output: { bands: 1 } };
                }
                function evaluatePixel(s) {
                    let nbr = (s.B08 - s.B12) / (s.B08 + s.B12);
                    return [nbr];
                }
            """
        }


        tasks = []
        for label, script in evalscripts.items():
            tasks.append(self.process_image(label, lat, lon, script, config, bbox, output_folder))
        sentinelhub_results = await gather(*tasks)

        result_urls = {label: url for label, url in sentinelhub_results}

        return result_urls

    async def process_image(self, label, lat, lon, script, config, bbox, output_folder):
        date_from = '2023-01-01'
        date_to = '2025-05-25'

        s3 = boto3.client('s3')
        bucket_name = os.getenv("S3_DATA_BUCKET")

        LOGGER.info(f'Requesting sentinel hub for {label}')
        tmp_output_folder = tempfile.mkdtemp(label)
        data_collection = DataCollection.SENTINEL2_L2A
        resolution = 10
        if label.startswith('landsat'):
            data_collection = DataCollection.LANDSAT_OT_L2
        elif label == 'copernicus_dem':
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
            responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
            bbox=bbox,
            size=size,
            config=config,
            data_folder=tmp_output_folder,
        )

        def request_save_data(s_hub_request):
            s_hub_request.save_data()

        await to_thread(request_save_data, request)

        png_path = None
        for root, _, files in os.walk(tmp_output_folder):
            for file in files:
                if file.endswith('.png'):
                    png_path = os.path.join(root, file)
                    break
            if png_path:
                break

        if not png_path:
            raise FileNotFoundError(f"PNG file not found in {tmp_output_folder} for {label}.")

        #TODO optimize image losslessly with pngcrush ? should not influence image analysis later

        LOGGER.info(f'Uploading to s3 {label}')
        filename = create_safe_filename(f"{label}_{lat}_{lon}_{date_from}_{date_to}", '.png', True)
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
        return label, s3_url

    def copy_and_rename(self, src_path: str, dest_path: str, new_name: str):
        # Copy the file
        shutil.copy(src_path, dest_path)
        old_filename = os.path.basename(src_path)
        # Rename the copied file
        new_path = f"{dest_path}/{new_name}"
        shutil.move(f"{dest_path}/{old_filename}", new_path)


if __name__ == "__main__":
    tool = SentinelS3PngUploader()
    result = tool._run(lat=-7.95, lon=-67.3, radius_in_meters=20000)
    LOGGER.info(result)

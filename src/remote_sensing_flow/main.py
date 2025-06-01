import json
import os
from typing import List
from crewai import Agent
from crewai.flow.flow import Flow, listen, start
from crewai.flow.persistence import persist
import logging
import argparse
import pandas as pd

from remote_sensing_flow.helpers import get_llm_azure, model_41_mini, model_o4_mini, model_o3, \
    get_markdown_image_analysis, model_41, safe_kickoff, haversine_distance, draw_hotspots_on_image
from remote_sensing_flow.tasks import research_task, validation_task, reporting_task, \
    image_analysis_task
from remote_sensing_flow.tools.search import SearchTool
from remote_sensing_flow.tools.sentinel_hub_png import SentinelS3PngUploader
from remote_sensing_flow.helpers import get_markdown_potential_site, create_safe_filename
from remote_sensing_flow.models import RemoteSensingState, PotentialSite, Image, ImageAnalysis, UserInput, \
    ClosestKnownSite

LOGGER = logging.getLogger('remote_sensing_flow')
LOGGER.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
LOGGER.addHandler(handler)

@persist(verbose=True)
class RemoteSensingFlow(Flow[RemoteSensingState]):

    output_root_folder: str = 'output'
    output_folder: str = None

    @start()
    async def user_input(self):
        LOGGER.info("\n=== Start User Input ===\n")
        if not self.state.user_input:
            # Ask for user input ask if they want to input lat long radius coordinates or if they let the AI search
            # for a potential site.
            while True:
                response = input("Do you want to input the coordinates of the potential site? (y/n)").lower().strip()
                if response in ['yes', 'y', '1']:
                    break
                elif response in ['no', 'n', '0']:
                    return None
                logging.warning("Please answer with 'yes' or 'no'")

            response = input("Input the coordinates of the potential site. Latitude (float):").lower().strip()
            self.state.user_input = UserInput(lat=0,lon=0,radius=0,exact=False)
            if response:
                self.state.user_input.lat = float(response)
            response = input("Input the coordinates of the potential site. Longitude (float):").lower().strip()
            if response:
                self.state.user_input.lon = float(response)
            response = input("Input the coordinates of the potential site. Radius in meters (int):").lower().strip()
            if response:
                self.state.user_input.radius = int(response)
            response = input("Coordinates are exact? (y/n):").lower().strip()
            if response in ['yes', 'y', '1']:
                self.state.user_input.exact = True
        else:
            LOGGER.info(f'Using user input from from script args or --ni (no input) arg provided.')

        return {"user_input": self.state.user_input}

    @listen(user_input)
    async def research(self):
        LOGGER.info("=== Start Research ===")
        if self.state.user_input and not self.state.user_input.no_input:
            LOGGER.info(f'Adding user input proposed coordinates to the prompt {self.state.user_input}')
            proximity = "exactly at" if self.state.user_input.exact else "close to"
            potential_site_input_location = (f"Findings should be {proximity} the following coordinates: "
                                             f"lat {self.state.user_input.lat}; "
                                             f"long {self.state.user_input.lon}; "
                                             f"radius {self.state.user_input.radius}. ")
        else:
            potential_site_input_location = ("Findings should be reasonably bound by the Amazon biome in Northern South "
                                             "America. Focus on Brazil, with allowed extension into the outskirts of "
                                             "Bolivia, Columbia, Ecuador, Guyana, Peru, Suriname, Venezuela, "
                                             "and French Guiana.")
        os.makedirs(self.output_root_folder, exist_ok=True)

        prompt = research_task + potential_site_input_location
        self.state.prompt_log.append(prompt)

        researcher = Agent(
            role="Archaeological Researcher",
            goal="Conduct research to identify potential archeological sites. "
                 "Analyze documents, vocal records, and legends for spatial clues. "
                 "Do not perform any satellite imagery analysis unless already done by someone else and published.",
            backstory="Expert in archaeological studies and historical research. Language expert.",
            tools=[SearchTool()],
            llm=get_llm_azure(model_41_mini, 0.7),
            verbose=True,
            reasoning=True,
            max_iter=5,
        )

        try:
            result = await safe_kickoff(researcher, prompt, PotentialSite)
        except Exception as e:
            LOGGER.warning("Error calling AI", e)
            exit(1)

        self.state.potential_site = result.pydantic
        LOGGER.info(self.state.potential_site.model_dump_json(indent=2))

        self.output_folder = os.path.join(
            self.output_root_folder, create_safe_filename(
                f"{self.state.potential_site.lat}_{self.state.potential_site.lon}_{self.state.potential_site.name}",
                timestamp=True))
        os.makedirs(self.output_folder)

        site_file_path = os.path.join(self.output_folder, "site.md")
        with open(site_file_path, "w") as f:
            f.write(str(get_markdown_potential_site(self.state.potential_site)))

        return {"potential_site": result.pydantic}

    @listen(research)
    def check_known_sites(self, research_output):
        """
        Check if the potential site is already known by comparing coordinates with known sites.
        Returns a dictionary with the check results.
        """
        LOGGER.info("Checking if site is already known...")

        try:
            known_sites_df = pd.read_csv('input_data/known_sites.csv')

            # Get the potential site coordinates
            potential_lat = self.state.potential_site.lat
            potential_lon = self.state.potential_site.lon
            search_radius = self.state.potential_site.radius

            # Initialize variables for closest site
            closest_distance = float('inf')
            closest_site = None

            # Check each known site
            for _, site in known_sites_df.iterrows():
                distance = haversine_distance(
                    potential_lat,
                    potential_lon,
                    site['latitude'],
                    site['longitude']
                )

                if distance < closest_distance:
                    closest_distance = distance
                    closest_site = site

            if closest_site is not None:
                LOGGER.info(f"Closest known site found: {closest_site}")
                # Create ClosestKnownSite instance
                closest_known_site = ClosestKnownSite(
                    name=closest_site['site_name'],
                    lat=closest_site['latitude'],
                    lon=closest_site['longitude'],
                    radius=search_radius,
                    distance=[f"{closest_distance:.2f} meters"],
                    is_within_search_radius=closest_distance <= search_radius,
                    type=closest_site['site_type_description'],
                    id=str(closest_site['site_id']),
                    description=closest_site.get('nature_description', 'No description available'),
                    site_summary=closest_site['site_summary']
                )

                # Log the results
                LOGGER.info(f"Closest known site: {closest_known_site.name}")
                LOGGER.info(f"Distance to closest site: {closest_distance:.2f} meters")
                LOGGER.info(f"Within search radius: {closest_known_site.is_within_search_radius}")

                # Save the check results to a file in the output folder
                check_results_path = os.path.join(self.output_folder, "known_sites_check.md")
                with open(check_results_path, "w") as f:
                    f.write("# Known Sites Check Results\n\n")
                    f.write(f"## Closest Known Site\n")
                    f.write(f"- Name: {closest_known_site.name}\n")
                    f.write(f"- Site ID: {closest_known_site.id}\n")
                    f.write(f"- Distance: {closest_known_site.distance[0]}\n")
                    f.write(f"- Type: {closest_known_site.type}\n")
                    f.write(f"- Description: {closest_known_site.description}\n")
                    f.write(f"- Coordinates: {closest_known_site.lat}, {closest_known_site.lon}\n")
                    f.write(f"\n## Analysis\n")
                    f.write(f"- Search radius: {closest_known_site.radius} meters\n")
                    f.write(f"- Is within search radius: {closest_known_site.is_within_search_radius}\n")
                    f.write(f"\n## Maps\n")
                    for map_url in closest_known_site.maps:
                        f.write(f"- {map_url}\n")
                self.state.closest_known_site = closest_known_site
                return closest_known_site
            return {"No known sites found"}

        except FileNotFoundError:
            LOGGER.warning("Known sites database file not found at input_data/known_sites.csv")
            return {"error": "Known sites database file not found"}
        except Exception as e:
            LOGGER.error(f"Error checking known sites: {str(e)}")
            return {"error": str(e)}

    @listen(check_known_sites)
    async def collect_data(self, research_output):

        radius = self.state.potential_site.radius
        if not self.state.user_input.exact:
            radius = max(self.state.potential_site.radius, 10000)
            radius = min(radius, 12400) # 2500 diameter is the limit

        images = await SentinelS3PngUploader()._run(self.state.potential_site.lat, self.state.potential_site.lon,
                                                    radius, self.output_folder)
        for label, (url, filename) in images.items():
            self.state.images.append(Image(label=label,url=url, filename=filename))

        return {"images": images}

    @listen(collect_data)
    def analyze_images(self, images: List[Image]):
        LOGGER.info("Analyzing data...")

        llm = get_llm_azure(model_41_mini, 0.1)
        llm.response_format=ImageAnalysis

        analysis_role = "You are a Remote Sensing Analyst. Expert in multispectral satellite imagery analysis."
        content = [{"type": "text", "text": f"""Proposed General Potential site: 
            - lat: {self.state.potential_site.lat};
            - lon: {self.state.potential_site.lon};
            - radius: {self.state.potential_site.radius}."""},
            {"type": "text", "text": image_analysis_task}
        ]
        for image in self.state.images:
            # Make it clear to the LLM which image it is.
            # NDVI, true color, DEM etc.
            # as from the url sometimes it does not assume correctly
            content.append(
                {"type": "text", "text": f"Image {image.label}:"}
            )
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": image.url},
                    "detail": "high"  # want the model to have a better understanding of the image.
                }
            )

        LOGGER.info(content)

        messages = [
            {"role": "system", "content": analysis_role},
            {"role": "user", "content": content}
        ]

        self.state.prompt_log.append(json.dumps(messages))

        response = llm.call(messages=messages)

        LOGGER.info(response)

        self.state.image_analysis = ImageAnalysis.model_validate_json(response)

        image_analysis_file_path = os.path.join(self.output_folder, f"image_analysis.md")
        with open(image_analysis_file_path, "w") as f:
            f.write(get_markdown_image_analysis(self.state.image_analysis))

        # Draw hotspots on each image
        LOGGER.info(f"Drawing hotspots on images")
        for image in self.state.images:
            draw_hotspots_on_image(
                os.path.join(self.output_folder, image.filename),
                self.state.image_analysis.hotspots
            )

        return {'image_analysis': response}

    @listen(analyze_images)
    async def cross_verify(self, analysis):
        LOGGER.info("Cross verifying data...")
        validation_file_path = os.path.join(self.output_folder, f"validation.md")
        if not self.state.image_analysis.hotspots:
            LOGGER.info("No hotspots identified. Skipping cross verification.")
            result = "No hotspots identified. Skipping cross verification."
        else:
            validator = Agent(
                role="Validation Agent",
                goal="Confirm coordinates through at least two independent methods",
                backstory="Geospatial data integrity expert",
                llm=get_llm_azure(model_o4_mini, 0.1),
                tools=[SearchTool()],
                verbose=True,
            )
            validation_prompt = f"""{validation_task}
                {self.state.potential_site.to_prompt_str()}
                {self.state.image_analysis.to_prompt_str()}"""

            try:
                result = await safe_kickoff(validator, validation_prompt)
            except Exception as e:
                LOGGER.info(f"Error in validation {e}")
                result = f"No cross verification performed due to error calling LLM. Continuing without validation."
            else:
                result = self.state.cross_verification = result.raw

            self.state.prompt_log.append(validation_prompt)

        with open(validation_file_path, "a") as f:
            f.write(result)

        return {"cross_verification": self.state.cross_verification}

    @listen(cross_verify)
    async def report(self, analysis):
        LOGGER.info("Reporting...")
        reporter = Agent(
            role="Chief Archaeologist",
            goal="Compile findings into verified reports",
            backstory="Senior researcher with publication experience",
            tools=[SearchTool()],
            llm=get_llm_azure(model_o4_mini, 0.4),  # TODO use model o3 or o4 recommended, keeping mini for testing costs reduction
            verbose=True,
        )
        prompt = (f"{reporting_task} . Potential site: {self.state.potential_site}. "
                  f"Satellite imagery analysis: {self.state.image_analysis}.")
        if self.state.cross_verification:
            prompt += f" Cross Verification: {self.state.cross_verification}"
        if self.state.closest_known_site:
            prompt += f" Closest known site : {self.state.closest_known_site}. "

        try:
            result = await safe_kickoff(reporter, prompt)
        except Exception as e:
            LOGGER.info("Error in reporting LLm call:", e)
            exit(1)

        self.state.prompt_log.append(prompt)

        report_file_path = os.path.join(self.output_folder, "report.md")
        with open(report_file_path, "w") as f:
            f.write(result.raw)

        report_file_path = os.path.join(self.output_folder, "prompt_log.md")
        with open(report_file_path, "w") as f:
            f.write("\n\n==========\n\n".join(self.state.prompt_log))

        return result

def parse_args():
    parser = argparse.ArgumentParser(description="Remote Sensing Flow CLI")
    parser.add_argument("--lat", type=float, help="Latitude of the potential site")
    parser.add_argument("--lon", type=float, help="Longitude of the potential site")
    parser.add_argument("--radius", type=int, help="Radius in meters around the site")
    parser.add_argument("--exact", type=bool, help="Coordinates are exact", default=False)
    parser.add_argument("--ni", type=bool, help="No input. Don't ask for any input", default=False)
    return parser.parse_args()

def kickoff():
    """Run the guide creator flow"""
    args = parse_args()
    # flow_id = "remote_sensing_2025_06_01_001"
    if args and args.lat and args.lon and args.radius:
        flow_result = RemoteSensingFlow().kickoff(inputs={
            # "id": flow_id,
            "user_input": {
                "lat": args.lat,
                "lon": args.lon,
                "radius": args.radius,
                "exact": args.exact
            }})
    elif args.ni:
        flow_result = RemoteSensingFlow().kickoff(inputs={
            # "id": flow_id,
            "user_input": {
                "no_input": True
            }
        })
    else:
        flow_result = RemoteSensingFlow().kickoff(
            # inputs={
            #     "id": flow_id,
            # }
        )
    LOGGER.info(flow_result)
    LOGGER.info("\n=== Flow Complete ===")

def plot():
    """Generate a visualization of the flow"""
    flow = RemoteSensingFlow()
    flow.plot("remote_sensing_flow")
    LOGGER.info("Flow visualization saved remote_sensing_flow.html")

if __name__ == "__main__":
    kickoff()
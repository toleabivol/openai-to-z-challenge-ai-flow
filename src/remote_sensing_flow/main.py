import datetime
import os
from typing import List
from litellm import ContentPolicyViolationError
from pydantic import BaseModel, Field
from crewai import Agent
from crewai.flow.flow import Flow, listen, start


from remote_sensing_flow.helpers import get_llm_azure, model_41_mini, model_o4_mini
from remote_sensing_flow.tasks import research_task, validation_task, reporting_task, \
    image_analysis_task
from remote_sensing_flow.tools.search import SearchTool
from remote_sensing_flow.tools.sentinel_hub_png import SentinelS3PngUploader
from remote_sensing_flow.helpers import (RemoteSensingState, get_markdown_potential_site,  PotentialSite,  Image,
                                         ImageAnalysis, create_safe_filename)

class RemoteSensingFlow(Flow[RemoteSensingState]):

    output_root_folder: str = 'output'
    output_folder: str = None

    @start()
    async def research(self):
        print("\n=== Start Research ===\n")

        os.makedirs(self.output_root_folder, exist_ok=True)

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

        result = await researcher.kickoff_async(research_task, response_format=PotentialSite)

        if result.pydantic:
            print("result pydantic", result.pydantic)
            self.state.potential_site = result.pydantic
        else:
            print("result", result)

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
    async def collect_data(self, research_output):

        images = SentinelS3PngUploader()._run(
            self.state.potential_site.lat,
            self.state.potential_site.lon,
            max(self.state.potential_site.radius, 25000),
            self.output_folder
        )
        for label, url in images.items():
            self.state.images.append(Image(label=label,url=url))

        return {"images": images}

    @listen(collect_data)
    def analyze_images(self, images: List[Image]):
        print("Analyzing data...")

        llm = get_llm_azure(model_41_mini)
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
                    "image_url": {"url": image.url}
                }
            )

        print(content)

        messages = [
            {"role": "system", "content": analysis_role},
            {"role": "user", "content": content}
        ]

        response = llm.call(messages=messages)

        print(response)

        self.state.image_analysis = ImageAnalysis.model_validate_json(response)

        image_analysis_file_path = os.path.join(self.output_folder, f"image_analysis.md")
        with open(image_analysis_file_path, "w") as f:
            f.write(str(response))

        return {'image_analysis': response}

    @listen(analyze_images)
    async def cross_verify(self, analysis):
        print("Cross verifying data...")
        validation_file_path = os.path.join(self.output_folder, f"validation.md")
        if not self.state.image_analysis.hotspots:
            print("No hotspots identified. Skipping cross verification.")
            self.state.cross_verification = "No hotspots identified. Skipping cross verification."
        else:
            validator = Agent(
                role="Validation Agent",
                goal="Confirm coordinates through at least two independent methods",
                backstory="Geospatial data integrity expert",
                llm=get_llm_azure(model_o4_mini),
                tools=[SearchTool()],
                verbose=True,
            )
            validation_prompt = f"""{validation_task} . 
                    Potential site: 
                    - lat: {self.state.potential_site.lat};
                    - lon: {self.state.potential_site.lon};
                    - radius: {self.state.potential_site.radius};
                    - rationale: {self.state.potential_site.rationale};
                    - public sources: {self.state.potential_site.sources}.
                    Image Analysis: {self.state.image_analysis}
                    """
            try:
                result = await validator.kickoff_async(validation_prompt)
            except ContentPolicyViolationError as e:
                print("Error in validation", e)
                result = f"No cross verification performed due to prompt content policy violation."
                self.state.cross_verification = result
            else:
                self.state.cross_verification = result.raw

            with open(validation_file_path, "w") as f:
                f.write(f" Prompt: {validation_prompt}.")

        with open(validation_file_path, "a") as f:
            f.write(self.state.cross_verification)

        return {"cross_verification": self.state.cross_verification}

    @listen(cross_verify)
    async def report(self, analysis):
        print("Reporting...")
        reporter = Agent(
            role="Chief Archaeologist",
            goal="Compile findings into verified reports",
            backstory="Senior researcher with publication experience",
            tools=[SearchTool()],
            llm=get_llm_azure(model_o4_mini),  # TODO use model o3 or o4 recommended, keeping mini for testing costs reduction
            verbose=True,
        )
        result = await reporter.kickoff_async(f"{reporting_task} . Potential site: {self.state.potential_site}. "
                                              f"Satellite imagery analysis: {self.state.image_analysis}. "
                                              f"Cross Verification: {self.state.cross_verification}")

        report_file_path = os.path.join(self.output_folder, "report.md")
        with open(report_file_path, "w") as f:
            f.write(result.raw)

        return result

def kickoff():
    """Run the guide creator flow"""
    flow_result = RemoteSensingFlow().kickoff()
    print(flow_result)
    print("\n=== Flow Complete ===")

def plot():
    """Generate a visualization of the flow"""
    flow = RemoteSensingFlow()
    flow.plot("remote_sensing_flow")
    print("Flow visualization saved remote_sensing_flow.html")

if __name__ == "__main__":
    kickoff()
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

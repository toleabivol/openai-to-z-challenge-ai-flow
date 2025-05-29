from crewai import LLM
from litellm import drop_params

# Models. Price per 1M Tokens: Input | Cached Input | Output
model_41 = "gpt-4.1"  # $2.00 $0.50 $8.00
model_41_mini = "gpt-4.1-mini"  # $0.40 $0.10 $1.60
model_41_nano = "gpt-4.1-nano"  # $0.10 $0.025 $0.40
model_o3 = "o3"  # $10.00 $2.50 $40.00
model_o3_mini = "o3-mini"  # $1.10 $0.55 $4.40
model_o4_mini = "o4-mini"  # $1.10 $0.275 $4.40
model_4o = "gpt-4o"  # $2.5 $1.25 $10

llm_provider_azure = "azure"
llm_provider_openai = "openai"
llm_azure_api_version = "2025-04-01-preview"


# llm factory function
def get_llm_azure(model_name: str) -> LLM:
    return LLM(
        model=f"{llm_provider_azure}/{model_name}",
        api_version=llm_azure_api_version,  # only use with azure
        additional_drop_params=["stop"],
        drop_params=True,
        verbose=True,
    )
from dotenv import load_dotenv
import os
from pathlib import Path

from mcp import StdioServerParameters

from InlineAgent import AgentAppConfig

config = AgentAppConfig()

cost_server_params = StdioServerParameters(
    command="docker",
    args=[
        "run",
        "-i",
        "--rm",
        "-e", f"AWS_PROFILE={config.AWS_PROFILE}",
        "-e", f"AWS_REGION={config.AWS_REGION}",
        "-e",
        "BEDROCK_LOG_GROUP_NAME",
        "-v",
        f"{str(Path.home())}/.aws:/root/.aws",
#        f"{str(Path.home())}:/root/.aws/",
        "-e",
        "stdio",
        "aws-cost-explorer-mcp:latest",
    ],
    env={
        "AWS_PROFILE": config.AWS_PROFILE,
        "AWS_REGION": config.AWS_REGION,
        "BEDROCK_LOG_GROUP_NAME": config.BEDROCK_LOG_GROUP_NAME,
    },
)

perplexity_server_params = None
perplexity_key = os.getenv("PERPLEXITY_API_KEY")

if perplexity_key:
    perplexity_server_params = StdioServerParameters(
        command="docker",
        args=["run", "-i", "--rm", "-e", "PERPLEXITY_API_KEY", "mcp/perplexity-ask"],
        env={"PERPLEXITY_API_KEY": perplexity_key},
    )

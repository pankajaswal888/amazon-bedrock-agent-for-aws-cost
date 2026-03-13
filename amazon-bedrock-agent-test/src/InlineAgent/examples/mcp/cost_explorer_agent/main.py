from InlineAgent.tools import MCPStdio
from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent

from config import cost_server_params, perplexity_server_params


async def main():

    cost_explorer_mcp_client = await MCPStdio.create(server_params=cost_server_params)

    perplexity_mcp_client = None

    if perplexity_server_params:
        perplexity_mcp_client = await MCPStdio.create(
            server_params=perplexity_server_params
        )

    try:

        mcp_clients = [cost_explorer_mcp_client]

        if perplexity_mcp_client:
            mcp_clients.append(perplexity_mcp_client)

        cost_action_group = ActionGroup(
            name="CostActionGroup",
            mcp_clients=mcp_clients,
        )

        await InlineAgent(
            foundation_model="anthropic.claude-3-sonnet-20240229-v1:0",
            instruction="""You are an AWS cost analysis assistant.

You have access to AWS Cost Explorer tools.

When a tool returns large tables or detailed data:

Immediately summarize the result.

Extract only the top 5 services by total cost.

Ignore services with zero cost.

Never include full tables in the final response.

Provide a short summary with the top services and their approximate costs.""",
            agent_name="cost_agent",
            action_groups=[
                cost_action_group
            ],
        ).invoke(
            input_text="Using the cost explorer tools, identify the top 5 AWS services by total cost in the last 7 days. Summarize the result."
        )

    finally:

        if perplexity_mcp_client:
            await perplexity_mcp_client.cleanup()

        await cost_explorer_mcp_client.cleanup()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

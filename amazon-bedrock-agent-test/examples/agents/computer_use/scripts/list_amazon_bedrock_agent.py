import argparse
import boto3


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Create an Amazon Bedrock Agent with specified name"
    )
    parser.add_argument(
        "--agent-name",
        type=str,
        default="computeruse",
        help="Name of the Bedrock agent (default: computeruse)",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="computeruse",
        help=f"Name of the AWS CLI Profile (default: computeruse)",
    )
    return parser.parse_args()


def list_agent(agent_name: str, profile: str):

    bedrock_agent = boto3.session.Session(profile_name=profile).client(
        "bedrock-agent", region_name="us-west-2"
    )

    paginator = bedrock_agent.get_paginator("list_agents")

    all_agents = list()

    for page in paginator.paginate(PaginationConfig={"PageSize": 10}):
        all_agents.extend(page["agentSummaries"])

    agent_id = next(
        (agent["agentId"] for agent in all_agents if agent["agentName"] == agent_name),
        None,
    )

    if agent_id:

        try:
            _agent_aliases = bedrock_agent.list_agent_aliases(
                agentId=agent_id, maxResults=100
            )
            for alias in _agent_aliases["agentAliasSummaries"]:
                alias_id = alias["agentAliasId"]
                if alias_id == "TSTALIASID":
                    continue
                print(f"AgentID {agent_id} with alias {alias_id}")
        except Exception as e:
            print(f"Error deleting aliases: {e}")
            pass
    else:
        print(f"No agent with name {agent_name} exsists..")


if __name__ == "__main__":
    args = parse_arguments()
    agent_name = args.agent_name
    profile = args.profile

    list_agent(agent_name=agent_name, profile=profile)

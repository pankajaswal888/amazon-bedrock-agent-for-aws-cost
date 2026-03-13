import argparse
import boto3

import time


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


def delete_agent(agent_name: str, profile: str):

    bedrock_agent = boto3.session.Session(profile_name=profile).client(
        "bedrock-agent", region_name="us-west-2"
    )
    iam_client = boto3.session.Session(profile_name=profile).client(
        "iam", region_name="us-west-2"
    )

    agent_role_name = f"AmazonBedrockExecutionRoleForAgents_{agent_name}"
    agent_bedrock_allow_policy_name = "bedrock_allow_policy"
    try:
        iam_client.delete_role_policy(
            RoleName=agent_role_name, PolicyName=agent_bedrock_allow_policy_name
        )

        # iam_client.delete_policy(
        #     PolicyArn=f"arn:aws:iam::{account_id}:policy/{agent_bedrock_allow_policy_name}"
        # )
        print(f"Deleted IAM role policy: {agent_bedrock_allow_policy_name}...")
    except Exception as e:
        print(e)

    try:
        iam_client.delete_role(RoleName=agent_role_name)
        print(f"Deleted IAM role: {agent_role_name}...")
    except Exception as e:
        print(e)

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
                response = bedrock_agent.delete_agent_alias(
                    agentAliasId=alias_id, agentId=agent_id
                )
                print(f"Deleted alias {alias_id} from agent {agent_id}")
        except Exception as e:
            print(f"Error deleting aliases: {e}")
            pass

        try:
            bedrock_agent.delete_agent(agentId=agent_id)
            time.sleep(5)
        except Exception as e:
            print(e)

        print(f"Deleted agent {agent_id}")
    else:
        print(f"No agent with name {agent_name} exsists")


if __name__ == "__main__":
    args = parse_arguments()
    agent_name = args.agent_name
    profile = args.profile

    delete_agent(agent_name=agent_name, profile=profile)

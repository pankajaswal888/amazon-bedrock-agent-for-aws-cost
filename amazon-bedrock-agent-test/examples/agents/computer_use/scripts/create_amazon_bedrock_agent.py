import boto3

import json
import time
from delete_amazon_bedrock_agent import delete_agent
import argparse


suppored_models = [
    "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
]

DEFAULT_AGENT_IAM_ROLE_NAME = "AmazonBedrockExecutionRoleForAgents_"

tools = {
    "claude-3-7-sonnet-20250219-v1:0": [
        "computer_20250124",
        "text_editor_20250124",
        "bash_20250124",
    ],
    "claude-3-5-sonnet-20241022-v2:0": [
        "computer_20241022",
        "text_editor_20241022",
        "bash_20241022",
    ],
}

DEFAULT_AGENT_IAM_ASSUME_ROLE_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AmazonBedrockAgentModelPolicy",
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }
    ],
}


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Create an Amazon Bedrock Agent with specified name and model"
    )
    parser.add_argument(
        "--agent-name",
        type=str,
        default="computeruse",
        help="Name of the Bedrock agent (default: computeruse)",
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default=suppored_models[0],
        help=f"Name of the Bedrock Model to use (default: {suppored_models[0]})",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="computeruse",
        help=f"Name of the AWS CLI Profile (default: computeruse)",
    )

    return parser.parse_args()


def create_agent_role(
    agent_name: str, model_id: str, profile: str, guardrail_id: str
) -> str:

    iam_client = boto3.session.Session(profile_name=profile).client(
        "iam", region_name="us-west-2"
    )

    sts_client = boto3.session.Session(profile_name=profile).client("sts", region_name="us-west-2")
    identity = sts_client.get_caller_identity()
    account_id = identity["Account"]

    DEFAULT_AGENT_IAM_POLICY = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AmazonBedrockAgentInferenceProfilesCrossRegionPolicyProd",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:GetInferenceProfile",
                    "bedrock:GetFoundationModel",
                    "bedrock:ApplyGuardrail",
                    "bedrock:GetGuardrail",
                ],
                "Resource": [
                    f"arn:aws:bedrock:us-west-2:{account_id}:inference-profile/{model_id}",
                    f"arn:aws:bedrock:*::foundation-model/{model_id.replace("us.", "")}",
                    f"arn:aws:bedrock:us-west-2:*:guardrail/{guardrail_id}",
                ],
            }
        ],
    }

    _agent_role_name = DEFAULT_AGENT_IAM_ROLE_NAME + agent_name

    # try creating the default role, which may already exist
    try:
        # create the default role w/ the proper assume role policy
        _assume_role_policy_document_json = DEFAULT_AGENT_IAM_ASSUME_ROLE_POLICY
        _assume_role_policy_document = json.dumps(_assume_role_policy_document_json)

        _bedrock_agent_bedrock_allow_policy_document_json = DEFAULT_AGENT_IAM_POLICY
        _bedrock_agent_bedrock_allow_policy_document = json.dumps(
            _bedrock_agent_bedrock_allow_policy_document_json
        )

        _agent_role = iam_client.create_role(
            RoleName=_agent_role_name,
            AssumeRolePolicyDocument=_assume_role_policy_document,
        )
    except Exception as e:
        print(
            f"Caught exc when creating default role for role: {_agent_role_name}: {e}"
        )
        print(f"using assume role json: {_assume_role_policy_document}")
    else:
        iam_client.put_role_policy(
            PolicyDocument=_bedrock_agent_bedrock_allow_policy_document,
            PolicyName="bedrock_allow_policy",
            RoleName=_agent_role_name,
        )

    return iam_client.get_role(RoleName=_agent_role_name)["Role"]["Arn"]


def create_agent(agent_name: str, model_id: str, profile: str):
    bedrock_agent = boto3.session.Session(profile_name=profile).client(
        "bedrock-agent", region_name="us-west-2"
    )
    bedrock_client = boto3.session.Session(profile_name=profile).client(
        "bedrock", region_name="us-west-2"
    )

    try:
        # First, list guardrails to get the guardrail ID
        response = bedrock_client.list_guardrails()

        # Find the guardrail ID that matches the name
        guardrail_id = None
        guardrail_version = None
        for guardrail in response["guardrails"]:
            if guardrail["name"] == profile:
                guardrail_id = guardrail["id"]
                guardrail_version = guardrail["version"]
                break

    except Exception as e:
        print(f"Error deleting guardrail: {str(e)}")
        raise

    agent_role_arn = create_agent_role(
        agent_name=agent_name,
        model_id=model_id,
        profile=profile,
        guardrail_id=guardrail_id,
    )

    time.sleep(30)

    print(agent_role_arn)

    create_agent_response = bedrock_agent.create_agent(
        agentResourceRoleArn=agent_role_arn,
        agentName=agent_name,
        description="Example agent for computer use. This agent should only operate on Sandbox environments with limited privileges.",
        foundationModel=model_id,
        guardrailConfiguration={
            "guardrailIdentifier": guardrail_id,
            "guardrailVersion": guardrail_version,
        },
        instruction=f"""
<SYSTEM_CAPABILITY>
* You are utilising an Ubuntu virtual machine using linux arm64 architecture with internet access.
* You can feel free to install Ubuntu applications with your bash tool. Use curl instead of wget.
* To open firefox, please just click on the firefox icon.  Note, firefox-esr is what is installed on your system.
* Using bash tool you can start GUI applications, but you need to set export DISPLAY=:1 and use a subshell. For example "(DISPLAY=:1 xterm &)". GUI apps run with bash tool will appear within your desktop environment, but they may take some time to appear. Take a screenshot to confirm it did.
* When using your bash tool with commands that are expected to output very large quantities of text, redirect into a tmp file and use str_replace_editor or `grep -n -B <lines before> -A <lines after> <query> <filename>` to confirm output.
* When viewing a page it can be helpful to zoom out so that you can see everything on the page.  Either that, or make sure you scroll down to see everything before deciding something isn't available.
* When using your computer function calls, they take a while to run and send back to you.  Where possible/feasible, try to chain multiple of these calls all into one function calls request.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using Firefox, if a startup wizard appears, IGNORE IT.  Do not even click "skip this step".  Instead, click on the address bar where it says "Search or enter address", and enter the appropriate search term or URL there.
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to continue to read the pdf from your screenshots + navigation, determine the URL, use curl to download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your StrReplaceEditTool.
* When viewing a webpage, first use your computer tool to view it and explore it.  But, if there is a lot of text on that page, instead curl the html of that page to a file on disk and then using your StrReplaceEditTool to view the contents in plain text.
</IMPORTANT>
        """,
    )

    while True:
        response = bedrock_agent.get_agent(
            agentId=create_agent_response["agent"]["agentId"]
        )

        current_status = response["agent"]["agentStatus"]
        print(f"Current agent status: {current_status}")

        if current_status == "PREPARED" or current_status == "NOT_PREPARED":
            print("Agent created!")
            break
        elif current_status == "FAILED" or current_status == "DELETING":
            failure_reasons = response["agent"].get("failureReasons", [])
            raise Exception(f"Agent creation failed. Reasons: {failure_reasons}")
        else:
            print(f"Agent is in {current_status} state")

        print("Agent is still being created, waiting...")
        time.sleep(10)  # Wait for 10 seconds before checking again

    valid_tools = list()
    for tool in tools:
        if tool in model_id:
            valid_tools.extend(tools[tool])

    if len(valid_tools) != 3:
        raise Exception("Invalid tools")

    bedrock_agent.create_agent_action_group(
        actionGroupName="ComputerActionGroup",
        actionGroupState="ENABLED",
        agentId=create_agent_response["agent"]["agentId"],
        agentVersion="DRAFT",
        parentActionGroupSignature="ANTHROPIC.Computer",
        parentActionGroupSignatureParams={
            "type": valid_tools[0],
            "display_height_px": "768",
            "display_width_px": "1024",
            "display_number": "1",
        },
    )

    bedrock_agent.create_agent_action_group(
        actionGroupName="BashActionGroup",
        actionGroupState="ENABLED",
        agentId=create_agent_response["agent"]["agentId"],
        agentVersion="DRAFT",
        parentActionGroupSignature="ANTHROPIC.Bash",
        parentActionGroupSignatureParams={
            "type": valid_tools[2],
        },
    )

    bedrock_agent.create_agent_action_group(
        actionGroupName="TextEditorActionGroup",
        actionGroupState="ENABLED",
        agentId=create_agent_response["agent"]["agentId"],
        agentVersion="DRAFT",
        parentActionGroupSignature="ANTHROPIC.TextEditor",
        parentActionGroupSignatureParams={
            "type": valid_tools[1],
        },
    )

    bedrock_agent.create_agent_action_group(
        actionGroupName="WeatherActionGroup",
        agentId=create_agent_response["agent"]["agentId"],
        agentVersion="DRAFT",
        actionGroupExecutor={
            "customControl": "RETURN_CONTROL",
        },
        functionSchema={
            "functions": [
                {
                    "name": "get_current_weather",
                    "description": "Get the current weather in a given location.",
                    "parameters": {
                        "location": {
                            "type": "string",
                            "description": "The city, e.g., San Francisco",
                            "required": True,
                        },
                        "unit": {
                            "type": "string",
                            "description": 'The unit to use, e.g., fahrenheit or celsius. Defaults to "fahrenheit"',
                            "required": False,
                        },
                    },
                    "requireConfirmation": "DISABLED",
                }
            ]
        },
    )

    time.sleep(10)

    bedrock_agent.prepare_agent(agentId=create_agent_response["agent"]["agentId"])

    while True:
        response = bedrock_agent.get_agent(
            agentId=create_agent_response["agent"]["agentId"]
        )

        current_status = response["agent"]["agentStatus"]
        print(f"Current agent status: {current_status}")

        # Check if the agent is no longer in CREATING state
        if current_status == "PREPARED":
            print("Agent is prepared!")
            break
        elif (
            current_status == "FAILED"
            or current_status == "DELETING"
            or current_status == "NOT_PREPARED"
        ):
            failure_reasons = response["agent"].get("failureReasons", [])
            raise Exception(f"Agent preparing failed. Reasons: {failure_reasons}")
        else:
            print(f"Agent is in {current_status} state")

        print("Agent is still being created, waiting...")
        time.sleep(10)  # Wait for 10 seconds before checking again

    dev_agent_alias_response = bedrock_agent.create_agent_alias(
        agentAliasName="dev", agentId=create_agent_response["agent"]["agentId"]
    )

    print(f"Agent Id: {create_agent_response["agent"]["agentId"]}")
    print(f"Agent Alias Id: {dev_agent_alias_response["agentAlias"]["agentAliasId"]}")


if __name__ == "__main__":
    args = parse_arguments()
    agent_name = args.agent_name
    model_id = args.model_id
    profile = args.profile

    if model_id not in suppored_models:
        raise Exception(
            f"Model {model_id} is not supported. Supported models {json.dumps(suppored_models,default=str, indent=2)}"
        )

    try:
        create_agent(agent_name=agent_name, model_id=model_id, profile=profile)
    except Exception as e:
        print(f"Exception encountered: {e}")
        # delete_agent(agent_name=agent_name, profile=profile)

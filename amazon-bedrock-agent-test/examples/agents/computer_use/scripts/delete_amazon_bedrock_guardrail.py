import boto3
import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Create an Amazon Bedrock Agent with specified name and model"
    )
    parser.add_argument(
        "--guardrail-name",
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


def delete_guardrail(guardrail_name: str, profile: str):
    # Initialize the Bedrock client
    bedrock_client = boto3.session.Session(profile_name=profile).client(
        "bedrock", region_name="us-west-2"
    )

    try:
        # First, list guardrails to get the guardrail ID
        response = bedrock_client.list_guardrails()

        # Find the guardrail ID that matches the name
        guardrail_id = None
        for guardrail in response["guardrails"]:
            if guardrail["name"] == guardrail_name:
                guardrail_id = guardrail["id"]
                break

        if guardrail_id:
            # Delete the guardrail using the ID
            bedrock_client.delete_guardrail(guardrailIdentifier=guardrail_id)
            print(f"Successfully deleted guardrail: {guardrail_name}")
        else:
            print(f"No guardrail found with name: {guardrail_name}")

    except Exception as e:
        print(f"Error deleting guardrail: {str(e)}")
        raise


if __name__ == "__main__":
    args = parse_arguments()
    guardrail_name = args.guardrail_name
    profile = args.profile
    delete_guardrail(guardrail_name=guardrail_name, profile=profile)

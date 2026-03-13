import boto3

import boto3
import argparse

from delete_amazon_bedrock_guardrail import delete_guardrail


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


def create_guardrail(guardrail_name: str, profile: str):
    # Initialize the Bedrock client
    bedrock_client = boto3.session.Session(profile_name=profile).client(
        "bedrock", region_name="us-west-2"
    )

    try:
        # Create a guardrail with basic content filters
        response = bedrock_client.create_guardrail(
            name=guardrail_name,
            description="A basic guardrail with content and image filtering",
            # Configure messages shown when content is blocked
            blockedInputMessaging="Your input contains content that is not allowed.",
            blockedOutputsMessaging="The response contains content that is not allowed.",
            # Configure content policy with filters
            contentPolicyConfig={
                "filtersConfig": [
                    {
                        "type": "SEXUAL",
                        "inputStrength": "MEDIUM",
                        "outputStrength": "MEDIUM",
                        "inputModalities": ["TEXT", "IMAGE"],
                        "outputModalities": ["TEXT", "IMAGE"],
                    },
                    {
                        "type": "VIOLENCE",
                        "inputStrength": "MEDIUM",
                        "outputStrength": "MEDIUM",
                        "inputModalities": ["TEXT", "IMAGE"],
                        "outputModalities": ["TEXT", "IMAGE"],
                    },
                    {
                        "type": "HATE",
                        "inputStrength": "MEDIUM",
                        "outputStrength": "MEDIUM",
                        "inputModalities": ["TEXT", "IMAGE"],
                        "outputModalities": ["TEXT", "IMAGE"],
                    },
                    {
                        "type": "INSULTS",
                        "inputStrength": "MEDIUM",
                        "outputStrength": "MEDIUM",
                        "inputModalities": ["TEXT", "IMAGE"],
                        "outputModalities": ["TEXT", "IMAGE"],
                    },
                    {
                        "type": "MISCONDUCT",
                        "inputStrength": "MEDIUM",
                        "outputStrength": "MEDIUM",
                        "inputModalities": ["TEXT"],
                        "outputModalities": ["TEXT"],
                    },
                    {
                        "type": "PROMPT_ATTACK",
                        "inputStrength": "HIGH",
                        "outputStrength": "NONE",
                        "inputModalities": ["TEXT"],
                        "outputModalities": ["TEXT"],
                    },
                ]
            },
        )

        print("Guardrail created successfully!")
        print(f"Guardrail ID: {response['guardrailId']}")
        print(f"Guardrail Version: {response['version']}")
        return response

    except Exception as e:
        print(f"Error creating guardrail: {str(e)}")
        raise


if __name__ == "__main__":
    args = parse_arguments()
    guardrail_name = args.guardrail_name
    profile = args.profile
    try:
        create_guardrail(guardrail_name=guardrail_name, profile=profile)
    except Exception as e:
        print(f"Exception encountered: {e}")
        delete_guardrail(guardrail_name=guardrail_name, profile=profile)

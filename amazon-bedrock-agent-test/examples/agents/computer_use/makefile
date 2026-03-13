# Define default profile name
PROFILE_NAME ?= computeruse
MODEL_ID ?= us.anthropic.claude-3-7-sonnet-20250219-v1:0

.PHONY: create-profile get-urls create-agent delete-agent list-agent create-guardrail delete-guardrail bedrock clean-bedrock

configure: create-profile configure-aws-region

bedrock : create-guardrail create-agent

setup: create-venv bootstrap

clean-bedrock: delete-guardrail delete-agent 


# Configure AWS CLI
configure-aws-region:
	@echo "Defaulting to us-west-2"
	aws configure --profile $(PROFILE_NAME) set region us-west-2

create-profile:
	@echo "Creating AWS CLI profile '$(PROFILE_NAME)'"
	@echo "Please provide your AWS credentials when prompted..."
	@echo "Make sure to use us-west-2"
	aws configure --profile $(PROFILE_NAME)

# Create, setup and activate virtual environment
create-venv:
	pip install virtualenv
	pip install --upgrade virtualenv
	python3 -m venv .venv

# Infrastructure
bootstrap:
	cdk bootstrap --profile $(PROFILE_NAME)

deploy-infrastructure:
	@echo "Using AWS CLI profile '$(PROFILE_NAME)'"
	@if [ -z "$(IP)" ]; then \
		cdk deploy --context deployer_ip=$(shell curl -s https://api.ipify.org) --profile $(PROFILE_NAME); \
		exit 1; \
	fi
	cdk deploy --context deployer_ip=$(IP) --profile $(PROFILE_NAME)

destroy-infrastructure:
	@echo "Using AWS CLI profile '$(PROFILE_NAME)'"
	@if [ -z "$(IP)" ]; then \
		cdk destroy --context deployer_ip=$(shell curl -s https://api.ipify.org) --profile $(PROFILE_NAME); \
		exit 1; \
	fi
	cdk destroy --context deployer_ip=$(IP) --profile $(PROFILE_NAME)

get-urls:
	./scripts/get_urls.sh --profile $(PROFILE_NAME)

# Create Bedrock agent
create-agent:
	python ./scripts/create_amazon_bedrock_agent.py --agent-name="$(PROFILE_NAME)" --model-id="$(MODEL_ID)" --profile $(PROFILE_NAME)

delete-agent:
	python ./scripts/delete_amazon_bedrock_agent.py --agent-name="$(PROFILE_NAME)" --profile $(PROFILE_NAME)

list-agent:
	python ./scripts/list_amazon_bedrock_agent.py --agent-name="$(PROFILE_NAME)" --profile $(PROFILE_NAME)

# Guardrail
create-guardrail:
	python ./scripts/create_amazon_bedrock_guardrail.py --guardrail-name="$(PROFILE_NAME)" --profile $(PROFILE_NAME)

delete-guardrail:
	python ./scripts/delete_amazon_bedrock_guardrail.py --guardrail-name="$(PROFILE_NAME)" --profile $(PROFILE_NAME)

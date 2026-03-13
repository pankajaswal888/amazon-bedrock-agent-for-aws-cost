#!/bin/bash

# Parse command line arguments (same as original)
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile) PROFILE="--profile $2"; shift 2 ;;
        --stack) STACK_NAME="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Stack name determination (same as original)
if [ -z "$STACK_NAME" ]; then
    STACK_NAME=$(aws $PROFILE cloudformation describe-stacks --query 'Stacks[?contains(StackName, `ComputerUseAws`)].StackName' --output text)
    [ -z "$STACK_NAME" ] && { echo "Error: Could not determine stack name. Please provide it using --stack option."; exit 1; }
fi

STACK_NAME_LOWER=$(echo "$STACK_NAME" | tr '[:upper:]' '[:lower:]')

# Get cluster name (with default value)
CLUSTER_NAME=$(aws $PROFILE cloudformation describe-stacks --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`ComputerUseAwsClusterName`].OutputValue' --output text)
CLUSTER_NAME=${CLUSTER_NAME:-"computer-use-aws-cluster"}

ENV_SERVICE="computer-use-aws-environment-service"
ORCH_SERVICE="computer-use-aws-orchestration-service"

echo "Using cluster: $CLUSTER_NAME"
echo "Environment service name: $ENV_SERVICE"
echo "Orchestration service name: $ORCH_SERVICE"

# Parallel service status check
echo -e "\nChecking service status..."
aws $PROFILE ecs describe-services --cluster $CLUSTER_NAME --services $ENV_SERVICE $ORCH_SERVICE \
    --query 'services[*].[serviceName,status,runningCount,desiredCount,events[0].message]' --output table &

# Function to get service details
get_service_details() {
    local service_name=$1
    local port=$2
    local protocol=$3
    
    local TASK=$(aws $PROFILE ecs list-tasks --cluster $CLUSTER_NAME --service-name $service_name --query 'taskArns[0]' --output text)
    
    if [ "$TASK" != "None" ] && [ ! -z "$TASK" ]; then
        local ENI=$(aws $PROFILE ecs describe-tasks --cluster $CLUSTER_NAME --tasks $TASK \
            --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)
        local IP=$(aws $PROFILE ec2 describe-network-interfaces --network-interface-ids $ENI \
            --query 'NetworkInterfaces[0].Association.PublicIp' --output text)
        
        echo "Task ARN: $TASK"
        echo "ENI: $ENI"
        echo "IP Address: $IP"
        echo "${service_name} URL: ${protocol}://$IP:$port"
    else
        echo "No running tasks found for $service_name"
    fi
}

# Parallel execution of service details retrieval
echo -e "\nGetting Orchestration Service IP (Streamlit on port 8501)..."
get_service_details $ORCH_SERVICE 8501 "http" &

echo -e "\nGetting Environment Service IP (DVC on port 8443)..."
get_service_details $ENV_SERVICE 8443 "https" &

# Wait for all background processes to complete
wait

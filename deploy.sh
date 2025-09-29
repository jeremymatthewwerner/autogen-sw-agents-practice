#!/bin/bash

# Multi-Agent System AWS Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${ENVIRONMENT:-dev}
AWS_REGION=${AWS_REGION:-us-east-1}
PROJECT_NAME="multi-agent-system"

echo -e "${GREEN}🚀 Deploying Multi-Agent System to AWS${NC}"
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo "----------------------------------------"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command_exists aws; then
    echo -e "${RED}❌ AWS CLI is required but not installed.${NC}"
    exit 1
fi

if ! command_exists terraform; then
    echo -e "${RED}❌ Terraform is required but not installed.${NC}"
    exit 1
fi

if ! command_exists docker; then
    echo -e "${RED}❌ Docker is required but not installed.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"

# Check AWS credentials
echo -e "${YELLOW}🔐 Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo -e "${RED}❌ AWS credentials not configured or invalid.${NC}"
    echo "Please run: aws configure"
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS credentials valid (Account: $AWS_ACCOUNT_ID)${NC}"

# Prompt for sensitive information
echo -e "${YELLOW}🔑 Setting up secrets...${NC}"

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -n "Enter your Anthropic API key: "
    read -s ANTHROPIC_API_KEY
    echo
fi

if [ -z "$DATABASE_PASSWORD" ]; then
    echo -n "Enter a password for the RDS database (min 8 chars): "
    read -s DATABASE_PASSWORD
    echo
fi

# Validate inputs
if [ ${#ANTHROPIC_API_KEY} -lt 10 ]; then
    echo -e "${RED}❌ Anthropic API key seems too short${NC}"
    exit 1
fi

if [ ${#DATABASE_PASSWORD} -lt 8 ]; then
    echo -e "${RED}❌ Database password must be at least 8 characters${NC}"
    exit 1
fi

# Create Terraform variables file
echo -e "${YELLOW}📝 Creating Terraform configuration...${NC}"
cat > infrastructure/terraform/terraform.tfvars <<EOF
aws_region = "$AWS_REGION"
project_name = "$PROJECT_NAME"
environment = "$ENVIRONMENT"
database_password = "$DATABASE_PASSWORD"
anthropic_api_key = "$ANTHROPIC_API_KEY"
EOF

# Deploy infrastructure
echo -e "${YELLOW}🏗️  Deploying infrastructure with Terraform...${NC}"
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Plan deployment
echo -e "${YELLOW}📋 Planning infrastructure deployment...${NC}"
terraform plan -var-file=terraform.tfvars

# Confirm deployment
echo -n -e "${YELLOW}Do you want to proceed with the deployment? (y/N): ${NC}"
read -r CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏹️  Deployment cancelled${NC}"
    exit 0
fi

# Apply Terraform
echo -e "${GREEN}🚀 Applying infrastructure changes...${NC}"
terraform apply -var-file=terraform.tfvars -auto-approve

# Get outputs
ECS_CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
ALB_DNS_NAME=$(terraform output -raw alb_dns_name)
ECR_REPOSITORY_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME"

echo -e "${GREEN}✅ Infrastructure deployed successfully!${NC}"
echo "ECS Cluster: $ECS_CLUSTER_NAME"
echo "Load Balancer: $ALB_DNS_NAME"

# Return to project root
cd ../..

# Build and push Docker image
echo -e "${YELLOW}🐳 Building and pushing Docker image...${NC}"

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Create ECR repository if it doesn't exist
aws ecr describe-repositories --repository-names $PROJECT_NAME --region $AWS_REGION 2>/dev/null || \
aws ecr create-repository --repository-name $PROJECT_NAME --region $AWS_REGION

# Build and push image
docker build -f Dockerfile.cloud -t $PROJECT_NAME .
docker tag $PROJECT_NAME:latest $ECR_REPOSITORY_URL:latest
docker push $ECR_REPOSITORY_URL:latest

echo -e "${GREEN}✅ Docker image pushed to ECR${NC}"

# Create ECS service
echo -e "${YELLOW}⚙️  Creating ECS service...${NC}"

# Substitute variables in task definition
TASK_DEFINITION_JSON=$(cat infrastructure/ecs-task-definition.json | \
    sed "s/\${account_id}/$AWS_ACCOUNT_ID/g" | \
    sed "s/\${region}/$AWS_REGION/g" | \
    sed "s/\${environment}/$ENVIRONMENT/g" | \
    sed "s/\${database_password}/$DATABASE_PASSWORD/g" | \
    sed "s/\${database_endpoint}/$(terraform -chdir=infrastructure/terraform output -raw database_endpoint)/g" | \
    sed "s/\${redis_endpoint}/$(terraform -chdir=infrastructure/terraform output -raw redis_endpoint)/g" | \
    sed "s/\${redis_port}/$(terraform -chdir=infrastructure/terraform output -raw redis_port)/g" | \
    sed "s/\${s3_bucket_name}/$(terraform -chdir=infrastructure/terraform output -raw s3_bucket_name)/g" | \
    sed "s/\${secrets_manager_arn}/$(terraform -chdir=infrastructure/terraform output -raw secrets_manager_arn)/g" | \
    sed "s/\${ecs_task_execution_role_arn}/$(terraform -chdir=infrastructure/terraform output -raw ecs_task_execution_role_arn)/g" | \
    sed "s/\${ecs_task_role_arn}/$(terraform -chdir=infrastructure/terraform output -raw ecs_task_role_arn)/g")

# Register task definition
echo "$TASK_DEFINITION_JSON" > /tmp/task-definition.json
TASK_DEFINITION_ARN=$(aws ecs register-task-definition --cli-input-json file:///tmp/task-definition.json --query 'taskDefinition.taskDefinitionArn' --output text)

echo -e "${GREEN}✅ Task definition registered: $TASK_DEFINITION_ARN${NC}"

# Create ECS service
SERVICE_NAME="$PROJECT_NAME-service"
TARGET_GROUP_ARN=$(terraform -chdir=infrastructure/terraform output -raw target_group_arn)
SECURITY_GROUP_ID=$(terraform -chdir=infrastructure/terraform output -raw ecs_security_group_id)
SUBNET_IDS=$(terraform -chdir=infrastructure/terraform output -json private_subnet_ids | jq -r '.[]' | tr '\n' ',' | sed 's/,$//')

aws ecs create-service \
    --cluster $ECS_CLUSTER_NAME \
    --service-name $SERVICE_NAME \
    --task-definition $TASK_DEFINITION_ARN \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=$TARGET_GROUP_ARN,containerName=multi-agent-orchestrator,containerPort=8000" \
    --health-check-grace-period-seconds 120 \
    --enable-logging

echo -e "${GREEN}✅ ECS service created: $SERVICE_NAME${NC}"

# Wait for service to stabilize
echo -e "${YELLOW}⏳ Waiting for service to stabilize (this may take a few minutes)...${NC}"
aws ecs wait services-stable --cluster $ECS_CLUSTER_NAME --services $SERVICE_NAME

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo "🌐 Your Multi-Agent System is now running at:"
echo "   http://$ALB_DNS_NAME"
echo ""
echo "📚 API Documentation available at:"
echo "   http://$ALB_DNS_NAME/docs"
echo ""
echo "📊 To monitor the service:"
echo "   aws ecs describe-services --cluster $ECS_CLUSTER_NAME --services $SERVICE_NAME"
echo ""
echo "🔧 To view logs:"
echo "   aws logs tail /ecs/$PROJECT_NAME --follow"
echo ""

# Clean up temporary files
rm -f infrastructure/terraform/terraform.tfvars
rm -f /tmp/task-definition.json

echo -e "${GREEN}✅ Multi-Agent System is ready to develop software in the cloud!${NC}"
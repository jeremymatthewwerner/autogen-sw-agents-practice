# AWS Cloud Deployment Guide

This guide will help you deploy the Multi-Agent Software Development System to AWS and configure it to deploy generated applications.

## 🎯 What This Deployment Provides

After deployment, you'll have:

1. **Multi-Agent System running in AWS ECS** - Your intelligent software development team in the cloud
2. **REST API** - Accessible via Application Load Balancer with automatic scaling
3. **Database & Caching** - PostgreSQL RDS and Redis ElastiCache for persistence
4. **Artifact Storage** - S3 bucket for storing generated code and project files
5. **Auto-Deployment** - Generated applications automatically deployed to AWS
6. **Monitoring & Logging** - CloudWatch integration for observability

## 📋 Prerequisites

### Required Tools
- [AWS CLI](https://aws.amazon.com/cli/) (v2.0+)
- [Terraform](https://terraform.io/) (v1.0+)
- [Docker](https://docker.com/) (v20.0+)
- Git

### AWS Requirements
- AWS Account with appropriate permissions
- AWS CLI configured with credentials
- Permissions for: ECS, RDS, S3, ECR, IAM, VPC, CloudWatch, Secrets Manager

### API Keys
- **Anthropic API Key** - For Claude AI integration
  - Get from: [console.anthropic.com](https://console.anthropic.com)
  - Ensure you have sufficient credits/quota

## 🚀 Quick Start Deployment

### Option 1: Automated Script (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd sw-agents

# Run the automated deployment script
./deploy.sh
```

The script will:
- ✅ Check all prerequisites
- ✅ Deploy AWS infrastructure with Terraform
- ✅ Build and push Docker image to ECR
- ✅ Create ECS service with load balancer
- ✅ Configure monitoring and logging

### Option 2: Manual Step-by-Step

#### Step 1: Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key, Secret Key, Region, and Output format
```

#### Step 2: Set Environment Variables

```bash
export AWS_REGION=us-east-1
export ENVIRONMENT=dev  # or staging, prod
export ANTHROPIC_API_KEY=your_anthropic_key_here
export DATABASE_PASSWORD=your_secure_password_here
```

#### Step 3: Deploy Infrastructure

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Create variables file
cat > terraform.tfvars <<EOF
aws_region = "us-east-1"
project_name = "multi-agent-system"
environment = "dev"
database_password = "$DATABASE_PASSWORD"
anthropic_api_key = "$ANTHROPIC_API_KEY"
EOF

# Deploy infrastructure
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

#### Step 4: Build and Deploy Application

```bash
# Return to project root
cd ../..

# Build Docker image
docker build -f Dockerfile.cloud -t multi-agent-system .

# Push to ECR (script handles ECR login and push)
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/multi-agent-system"

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

docker tag multi-agent-system:latest $ECR_URI:latest
docker push $ECR_URI:latest
```

#### Step 5: Create ECS Service

```bash
# Register task definition and create service
# (This is handled automatically by deploy.sh)
```

## 🌐 Accessing Your Deployed System

After successful deployment:

### API Endpoints

```bash
# Your system will be available at:
http://your-alb-dns-name.region.elb.amazonaws.com

# Key endpoints:
GET  /health                           # Health check
GET  /docs                            # API documentation
POST /api/v1/projects                 # Create new project
GET  /api/v1/projects/{id}/status     # Check project status
GET  /api/v1/projects                 # List all projects
```

### Example Usage

```bash
# Create a new project
curl -X POST "http://your-alb-dns-name/api/v1/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "Todo App",
    "requirements": "Build a simple todo application with user authentication, CRUD operations, and a web interface",
    "deployment_target": "ecs"
  }'

# Check project status
curl "http://your-alb-dns-name/api/v1/projects/PROJECT_ID/status"
```

## 📊 Monitoring Your Deployment

### CloudWatch Logs

```bash
# View application logs
aws logs tail /ecs/multi-agent-system --follow

# View specific log streams
aws logs describe-log-streams --log-group-name /ecs/multi-agent-system
```

### ECS Service Status

```bash
# Check service health
aws ecs describe-services \
  --cluster multi-agent-system-cluster \
  --services multi-agent-system-service
```

### Database Connection

```bash
# Get database endpoint
terraform output -raw database_endpoint

# Connect to database (from within VPC)
psql -h database-endpoint -U postgres -d multiagent
```

## 🏗️ Generated Application Deployment

The system automatically deploys generated applications using these targets:

### ECS Deployment (Default)
- Generated apps deployed as Fargate tasks
- Automatic load balancer configuration
- Health checks and auto-scaling
- Logs in CloudWatch

### Lambda Deployment
- Serverless functions for APIs
- API Gateway integration
- Environment variable configuration
- Cold start optimization

### Configuration

Generated apps are deployed with:
```json
{
  "deployment_target": "ecs",
  "environment_variables": {
    "DATABASE_URL": "auto-configured",
    "REDIS_URL": "auto-configured"
  },
  "resource_limits": {
    "cpu": "512",
    "memory": "1024"
  }
}
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS deployment region | `us-east-1` |
| `ENVIRONMENT` | Environment (dev/staging/prod) | `dev` |
| `ANTHROPIC_API_KEY` | Claude API key | Required |
| `DATABASE_PASSWORD` | RDS password | Required |

### Terraform Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `db_instance_class` | RDS instance size | `db.t3.micro` |
| `project_name` | Project prefix | `multi-agent-system` |

## 💰 Cost Estimation

### Development Environment (~$125-210/month)
- ECS Fargate: ~$50-100
- RDS Aurora Serverless: ~$25-50
- ElastiCache: ~$15
- Load Balancer: ~$20
- S3 & CloudWatch: ~$15-25

### Production Environment (~$380-680/month)
- ECS Fargate: ~$200-400
- RDS Multi-AZ: ~$100-200
- ElastiCache: ~$50
- Additional monitoring & backup: ~$30-30

### Generated Applications
- Each generated app: ~$20-50/month (depending on usage)
- Lambda apps: Pay-per-use (typically $5-20/month)

## 🛠️ Troubleshooting

### Common Issues

#### 1. ECS Service Won't Start
```bash
# Check service events
aws ecs describe-services --cluster multi-agent-system-cluster --services multi-agent-system-service

# Check task logs
aws logs tail /ecs/multi-agent-system --follow
```

#### 2. Database Connection Issues
```bash
# Check security groups
aws ec2 describe-security-groups --group-names multi-agent-system-rds-sg

# Verify database is running
aws rds describe-db-instances --db-instance-identifier multi-agent-system-database
```

#### 3. Load Balancer Health Checks Failing
```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn TARGET_GROUP_ARN

# Verify health check endpoint
curl http://your-alb-dns/health
```

### Debugging Commands

```bash
# View all resources
terraform show

# ECS troubleshooting
aws ecs describe-clusters --clusters multi-agent-system-cluster
aws ecs list-tasks --cluster multi-agent-system-cluster

# Secrets verification
aws secretsmanager get-secret-value --secret-id multi-agent-system-api-keys
```

## 🧹 Cleanup/Teardown

To remove all resources and stop billing:

```bash
# Delete ECS service first
aws ecs update-service \
  --cluster multi-agent-system-cluster \
  --service multi-agent-system-service \
  --desired-count 0

aws ecs delete-service \
  --cluster multi-agent-system-cluster \
  --service multi-agent-system-service \
  --force

# Destroy infrastructure
cd infrastructure/terraform
terraform destroy -var-file=terraform.tfvars
```

**⚠️ Warning**: This will permanently delete all data including databases and S3 artifacts.

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review CloudWatch logs for error messages
3. Verify AWS permissions and quotas
4. Check AWS service health dashboard

## 🔐 Security Best Practices

### Production Deployment Checklist

- [ ] Use strong database passwords (stored in Secrets Manager)
- [ ] Configure VPC with private subnets for databases
- [ ] Enable encryption at rest for RDS and S3
- [ ] Set up CloudTrail for audit logging
- [ ] Configure security groups with minimal required access
- [ ] Enable GuardDuty for threat detection
- [ ] Set up billing alerts and cost monitoring
- [ ] Use IAM roles with least-privilege access
- [ ] Enable container image scanning in ECR
- [ ] Configure SSL/TLS termination at load balancer

### Secrets Management

- API keys stored in AWS Secrets Manager
- Database passwords rotated automatically
- No secrets in code or logs
- Environment-specific secret isolation

## 🚀 Ready to Deploy!

Your multi-agent system will be running in AWS, ready to:

1. **Accept project requests** via REST API
2. **Develop applications** using AI agents
3. **Deploy automatically** to AWS infrastructure
4. **Scale based on demand**
5. **Provide monitoring** and observability

Run `./deploy.sh` to get started! 🎉
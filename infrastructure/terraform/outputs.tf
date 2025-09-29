# Outputs for Multi-Agent System Infrastructure

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.multi_agent_vpc.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.multi_agent.id
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.multi_agent.name
}

output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.multi_agent_alb.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.multi_agent_alb.zone_id
}

output "target_group_arn" {
  description = "ARN of the target group"
  value       = aws_lb_target_group.multi_agent.arn
}

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.multi_agent.endpoint
  sensitive   = true
}

output "database_port" {
  description = "RDS instance port"
  value       = aws_db_instance.multi_agent.port
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_cluster.multi_agent.cache_nodes[0].address
}

output "redis_port" {
  description = "ElastiCache Redis port"
  value       = aws_elasticache_cluster.multi_agent.port
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket for artifacts"
  value       = aws_s3_bucket.artifacts.bucket
}

output "secrets_manager_arn" {
  description = "ARN of the secrets manager secret"
  value       = aws_secretsmanager_secret.api_keys.arn
}

output "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution_role.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task_role.arn
}

output "ecs_security_group_id" {
  description = "ID of the ECS security group"
  value       = aws_security_group.ecs_tasks.id
}

output "cloudwatch_log_group" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.multi_agent.name
}
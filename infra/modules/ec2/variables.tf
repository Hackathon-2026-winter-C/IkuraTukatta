variable "project_name" {
  description = "Project name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "ALB security group ID"
  type        = string
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix"
  type        = string
}

variable "target_group_arn" {
  description = "Target group ARN"
  type        = string
}

variable "target_group_arn_suffix" {
  description = "Target group ARN suffix"
  type        = string
}

variable "ami_id" {
  description = "AMI ID for EC2 instances"
  type        = string
  default     = "ami-02b4f6eadfdba2924" # Docker,Docker compose , nginx-1.27-alpineをインストール済み
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "asg_min_size" {
  description = "Auto Scaling Group minimum size"
  type        = number
  default     = 2
}

variable "asg_max_size" {
  description = "Auto Scaling Group maximum size"
  type        = number
  default     = 6
}

variable "asg_desired_capacity" {
  description = "Auto Scaling Group desired capacity"
  type        = number
  default     = 2
}

variable "asg_default_instance_warmup" {
  description = "Default instance warmup for Auto Scaling policies"
  type        = number
  default     = 300
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed EC2 monitoring"
  type        = bool
  default     = true
}

variable "scale_out_cpu_target" {
  description = "Target CPU utilization percentage for target tracking"
  type        = number
  default     = 55
}

variable "scale_out_requests_per_target" {
  description = "Target ALB request count per target for target tracking"
  type        = number
  default     = 100
}

variable "ecr_repository_url" {
  description = "ECR repository URL"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "db_host" {
  description = "RDS endpoint"
  type        = string
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "db_user" {
  description = "Database user"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "alb_dns_name" {
  description = "ALB DNS name"
  type        = string
}

variable "s3_bucket_arn" {
  description = "S3 bucket ARN"
  type        = string
}

variable "aws_s3_bucket" {
  description = "S3 bucket name"
  type        = string
}

variable "aws_access_key" {
  description = "AWS access key"
  type        = string
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS secret key"
  type        = string
  sensitive   = true
}

variable "rds_security_group_id" {
  type = string
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "django_setup_revision" {
  description = "Bump this value to re-run initial Django setup command"
  type        = string
  default     = "v1"
}

variable "debug" {
  type    = bool
  default = false
}

variable "bedrock_region_name" {
  description = "AWS Bedrock region name"
  type        = string
}

variable "bedrock_model_id" {
  description = "AWS Bedrock model ID (or inference profile ID/ARN)"
  type        = string
}

variable "bedrock_receipt_max_bytes" {
  description = "Maximum receipt image size (bytes) sent to Bedrock"
  type        = number
}

variable "google_oauth_client_id" {
  description = "Google OAuth client ID for web sign-in"
  type        = string
  default     = ""
}

variable "django_secret_key" {
  description = "Django SECRET_KEY for production runtime"
  type        = string
  sensitive   = true
}

variable "app_allowed_hosts" {
  type = string
}

variable "app_csrf_trusted_origins" {
  type = string
}

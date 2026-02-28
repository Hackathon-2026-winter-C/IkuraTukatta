variable "aws_region" {
  type    = string
  default = "ap-northeast-1"
}
variable "environment" {
  type = string
}

variable "vpc_cidr_block" {
  type = string
}

variable "availability_zones" {
  type = list(string)
}

variable "public_subnet_cidrs" {
  type = list(string)
}

variable "private_subnet_cidrs" {
  type = list(string)
}

variable "enable_nat_gateway" {
  type    = bool
  default = false
}

variable "ecr_repository_name" {
  type = string
}

variable "rds_instance_class" {
  type = string
}

variable "rds_allocated_storage" {
  type    = number
  default = 20
}

variable "rds_max_allocated_storage" {
  type    = number
  default = 100
}

variable "rds_database_name" {
  type = string
}

variable "rds_master_username" {
  type = string
}

variable "rds_master_password_param_name" {
  type = string
}

variable "rds_multi_az" {
  type    = bool
  default = false
}

variable "rds_backup_retention_period" {
  type    = number
  default = 7
}

variable "rds_skip_final_snapshot" {
  type    = bool
  default = false
}

variable "ec2_instance_type" {
  type = string
}

variable "ec2_asg_min_size" {
  type    = number
  default = 1
}

variable "ec2_asg_max_size" {
  type    = number
  default = 6
}

variable "ec2_asg_desired_capacity" {
  type    = number
  default = 2
}

variable "ec2_asg_default_instance_warmup" {
  type    = number
  default = 300
}

variable "ec2_enable_detailed_monitoring" {
  type    = bool
  default = true
}

variable "ec2_scale_out_cpu_target" {
  type    = number
  default = 55
}

variable "ec2_scale_out_requests_per_target" {
  type    = number
  default = 100
}

variable "ec2_django_setup_revision" {
  type    = string
  default = "v1"
}

variable "aws_s3_bucket" {
  type = string

}

variable "aws_access_key" {
  type      = string
  sensitive = true
}

variable "aws_secret_key" {
  type      = string
  sensitive = true
}

variable "bedrock_region_name" {
  type    = string
  default = "ap-northeast-1"
}

variable "bedrock_model_id" {
  type    = string
  default = "jp.anthropic.claude-haiku-4-5-20251001-v1:0"
}

variable "bedrock_receipt_max_bytes" {
  type    = number
  default = 1000000
}

variable "google_oauth_client_id" {
  type    = string
  default = "794076670847-6mfhuj5lufrkimsdfqubdolpeaii534q.apps.googleusercontent.com"
}

variable "django_secret_key_param_name" {
  type = string
}

variable "domain_name" {
  type = string

}

variable "enable_www" {
  type    = bool
  default = true
}

variable "route53_zone_id" {
  type = string
}

variable "acm_certificate_arn" {
  type = string
}

variable "mattermost_webhook_param_name" {
  type = string
}

variable "notify_autoscaling_group_name" {
  type = string
}

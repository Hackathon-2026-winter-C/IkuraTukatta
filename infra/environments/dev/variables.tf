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

variable "rds_master_password" {
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
  default = 1
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

terraform {
  required_version = ">=1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "hackathon-winter-c-terraform-bucket-20260207"
    key            = "dev/terraform.tfstate"
    region         = "ap-northeast-1"
    dynamodb_table = "Terraform-state-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}

# VPCモジュールの呼び出し
module "vpc" {
  source = "../../modules/vpc"

  environment          = var.environment
  vpc_cidr_block       = var.vpc_cidr_block
  availability_zones   = var.availability_zones
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs

  tags = local.common_tags
}

# ALBモジュールの呼び出し
module "alb" {
  source = "../../modules/alb"

  project_name      = "${var.environment}-app"
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
}

# EC2モジュールの呼び出し
module "ec2" {
  source = "../../modules/ec2"

  project_name          = "${var.environment}-app"
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  alb_security_group_id = module.alb.alb_security_group_id
  target_group_arn      = module.alb.target_group_arn

  instance_type         = var.ec2_instance_type
  asg_min_size          = var.ec2_asg_min_size
  asg_max_size          = var.ec2_asg_max_size
  asg_desired_capacity  = var.ec2_asg_desired_capacity
  django_setup_revision = var.ec2_django_setup_revision

  ecr_repository_url    = module.ecr.repository_url
  region                = var.aws_region
  db_host               = module.rds.address
  db_name               = var.rds_database_name
  db_user               = var.rds_master_username
  db_password           = var.rds_master_password
  rds_security_group_id = module.rds.security_group_id
  alb_dns_name          = module.alb.alb_dns_name

  s3_bucket_arn  = "arn:aws:s3:::${var.aws_s3_bucket}"
  aws_s3_bucket  = var.aws_s3_bucket
  aws_access_key = var.aws_access_key
  aws_secret_key = var.aws_secret_key
}

# ECRモジュールの呼び出し
module "ecr" {
  source = "../../modules/ecr"

  environment     = var.environment
  repository_name = var.ecr_repository_name

  tags = local.common_tags
}

# RDSモジュールの呼び出し
module "rds" {
  source = "../../modules/rds"

  environment = var.environment
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnet_ids

  instance_class          = var.rds_instance_class
  allocated_storage       = var.rds_allocated_storage
  max_allocated_storage   = var.rds_max_allocated_storage
  database_name           = var.rds_database_name
  master_username         = var.rds_master_username
  master_password         = var.rds_master_password
  multi_az                = var.rds_multi_az
  backup_retention_period = var.rds_backup_retention_period
  skip_final_snapshot     = var.rds_skip_final_snapshot

  allowed_security_group = [module.ec2.ec2_security_group_id]
  tags                   = local.common_tags
}



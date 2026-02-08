terraform {
  required_version = ">=1.0"
  required_providers {
    aws = {
        source = "hashicorp/aws"
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

  environment = var.environment
  vpc_cidr_block = var.vpc_cidr_block
  availability_zones = var.availability_zones
  public_subnet_cidrs = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs

  tags = local.common_tags
}

# ECRモジュールの呼び出し
module "ecr" {
  source = "../../modules/ecr"

  environment = var.environment
  repository_name = var.ecr_repository_name

  tags = local.common_tags
}

# RDSモジュールの呼び出し
module "rds" {
  source = "../../modules/rds"

  environment = var.environment
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids

  instance_class = var.rds_instance_class
  allocated_storage = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage
  database_name = var.rds_database_name
  master_username = var.rds_master_username
  master_password = var.rds_master_password
  multi_az = var.rds_multi_az
  backup_retention_period = var.rds_backup_retention_period
  skip_final_snapshot = var.rds_skip_final_snapshot

  allowed_security_group = []

  tags = local.common_tags
}


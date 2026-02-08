aws_region = "ap-northeast-1"
environment = "dev"

vpc_cidr_block = "10.0.0.0/16"
availability_zones = ["ap-northeast-1a","ap-northeast-1c"]
public_subnet_cidrs = ["10.0.1.0/24","10.0.2.0/24"]
private_subnet_cidrs = ["10.0.100.0/24","10.0.200.0/24"]

ecr_repository_name = "hachathon-winter-c-app"

rds_instance_class = "db.t3.micro"
rds_allocated_storage = 20
rds_max_allocated_storage = 100
rds_database_name = "ikuratukatta_rds"
rds_master_username = "admin"
rds_master_password = "admin1234"
rds_multi_az = false # prodでtrue
rds_backup_retention_period = 0 # prodで7
rds_skip_final_snapshot = true # prodでfalse


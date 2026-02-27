aws_region  = "ap-northeast-1"
environment = "dev"

vpc_cidr_block       = "10.0.0.0/16"
availability_zones   = ["ap-northeast-1a", "ap-northeast-1c"]
public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.100.0/24", "10.0.200.0/24"]
enable_nat_gateway   = true

ecr_repository_name = "hachathon-winter-c-app"

rds_instance_class             = "db.t3.micro"
rds_allocated_storage          = 20
rds_max_allocated_storage      = 100
rds_database_name              = "ikuratukatta_rds"
rds_master_username            = "admin"
rds_master_password_param_name = "/hackathon/dev/rds/master-password"
rds_multi_az                   = false # prodでtrue
rds_backup_retention_period    = 0     # prodで7
rds_skip_final_snapshot        = true  # prodでfalse

# domain
domain_name         = "ikuratukatta.click"
enable_www          = true
route53_zone_id     = "Z05807932ZUV0W0H0GJ68"
acm_certificate_arn = "arn:aws:acm:ap-northeast-1:048588986880:certificate/2e574c36-cb67-4ac1-b41e-1acefefff518"


# ec2
ec2_instance_type                 = "t3.micro"
ec2_asg_min_size                  = 1
ec2_asg_max_size                  = 6
ec2_asg_desired_capacity          = 2
ec2_asg_default_instance_warmup   = 300
ec2_enable_detailed_monitoring    = true
ec2_scale_out_cpu_target          = 55
ec2_scale_out_requests_per_target = 100
aws_s3_bucket                     = "hackathon-media-s3-bucket-20260207"

# app runtime envs
django_secret_key_param_name = "/hackathon/dev/app/django/secret-key"

# notify
mattermost_webhook_param_name = "/hackathon/dev/mattermost/webhook-url"
notify_autoscaling_group_name = "dev-app-asg"

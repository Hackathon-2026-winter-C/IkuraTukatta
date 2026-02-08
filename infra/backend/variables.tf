variable "aws_region" {
  description = "AWS Region"
  type = string
  default = "ap-northeast-1"
}

variable "s3_media_bucket_name" {
  description = "Django media files"
  default = "hackathon-media-s3-bucket-20260207"
  type = string
}

variable "state_bucket_name" {
  description = "S3 bucket name for terraform state"
  type = string
  default = "hackathon-winter-c-terraform-bucket-20260207"
}

variable "lock_table_name" {
  description = "DynamoDB table name for state locking"
  type = string
  default = "Terraform-state-lock"
}
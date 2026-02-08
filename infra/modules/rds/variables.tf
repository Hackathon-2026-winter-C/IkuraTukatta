variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "allowed_security_group" {
  type = list(string)
  default = [ ]
}

variable "engine_version" {
  type = string
  default = "8.0"
}

variable "instance_class" {
  type = string
}

variable "allocated_storage" {
  type = number
  default = 20
}

variable "max_allocated_storage" {
  type = number
  default = 100
}

variable "database_name" {
  type = string
}

variable "master_username" {
  type = string
}

variable "master_password" {
  type = string
}

variable "multi_az" {
  type = bool
  default = false
}

variable "backup_retention_period" {
  type = number
  default = 7
}

variable "skip_final_snapshot" {
  type = bool
  default = false
}

variable "tags" {
  type = map(string)
  default = {}
}
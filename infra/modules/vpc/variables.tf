variable "environment" {
  description = "Environment name dev/prod"
  type        = string
}

variable "vpc_cidr_block" {
  description = "CIDR block for vpc"
  type        = string
}

variable "availability_zones" {
  description = "list availability zones"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
}

variable "tags" {
  description = "common tags for all resources"
  type        = map(string)
  default     = {}
}

variable "enable_nat_gateway" {
  description = "Whether to create a NAT gateway and route private subnet internet egress via NAT"
  type        = bool
  default     = false
}

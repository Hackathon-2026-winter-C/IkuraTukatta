output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "vpc cidr block"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "list of public subnet ids"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "list of private subnet ids"
  value       = aws_subnet.private[*].id
}

output "internet_gateway_id" {
  description = "internet gateway id"
  value       = aws_internet_gateway.main.id
}

output "s3_endpoint_id" {
  value = aws_vpc_endpoint.s3.id
}

output "interface_endpoint_ids" {
  description = "Map of interface endpoint IDs by service name"
  value       = { for service, endpoint in aws_vpc_endpoint.interface : service => endpoint.id }
}

output "interface_endpoint_sg_id" {
  description = "Security group ID attached to interface endpoints"
  value       = aws_security_group.interface_endpoint.id
}

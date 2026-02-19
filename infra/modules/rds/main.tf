resource "aws_db_subnet_group" "main" {
  name = "${var.environment}-db-subnet-group"
  subnet_ids = var.subnet_ids

  tags = merge(var.tags,{
    Name = "${var.environment}-db-subnet-group"
  })
}

resource "aws_security_group" "rds" {
  name = "${var.environment}-rds-sg"
  description = "security group for rds"
  vpc_id = var.vpc_id

  ingress {
    from_port = 3306
    to_port = 3306
    protocol = "tcp"
    security_groups = var.allowed_security_group
    description = "allow mysql from application"
  }

  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
     }

     tags = merge(var.tags,{
        Name = "${var.environment}-rds-sg"
     })
}

resource "aws_db_instance" "main" {
    identifier = "${var.environment}-mysql"
    engine = "mysql"
    engine_version = var.engine_version
    instance_class = var.instance_class

    allocated_storage = var.allocated_storage
    max_allocated_storage = var.max_allocated_storage
    storage_type = "gp3"
    storage_encrypted = true

    db_name = var.database_name
    username = var.master_username
    password = var.master_password
    
    db_subnet_group_name = aws_db_subnet_group.main.name
    vpc_security_group_ids = [aws_security_group.rds.id]

    multi_az = var.multi_az
    publicly_accessible = false

    backup_retention_period = var.backup_retention_period
    # backup_window = "03:00-04:00"
    # maintenance_window = "mon:04:00-mon:05:00"
    
    skip_final_snapshot = var.skip_final_snapshot
    final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.environment}-mysql-final-snapshot"

    enabled_cloudwatch_logs_exports = [ "error", "general", "slowquery" ]

    tags = merge(var.tags, {
        Name = "${var.environment}-mysql"
    })


}
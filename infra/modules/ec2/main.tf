# EC2 Security Group
resource "aws_security_group" "ec2" {
  name        = "${var.project_name}-ec2-sg"
  description = "Security group for EC2"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [var.alb_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-ec2-sg"
  }
}

# IAM Role for EC2
resource "aws_iam_role" "ec2" {
  name = "${var.project_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecr_read" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "ssm_managed" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "s3_access" {
  name = "${var.project_name}-s3-access"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ]
      Resource = "${var.s3_bucket_arn}/*"
    }]
  })
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.project_name}-ec2-profile"
  role = aws_iam_role.ec2.name
}

# Launch Template
resource "aws_launch_template" "app" {
  name_prefix   = "${var.project_name}-lt-"
  image_id      = var.ami_id
  instance_type = var.instance_type

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2.name
  }

  vpc_security_group_ids = [aws_security_group.ec2.id]

  user_data = base64encode(templatefile("${path.module}/userdata.sh", {
    ecr_repository_url = var.ecr_repository_url
    image_tag          = var.image_tag
    debug              = var.debug
    region             = var.region
    db_host            = var.db_host
    db_name            = var.db_name
    db_user            = var.db_user
    db_password        = var.db_password
    alb_dns_name       = var.alb_dns_name
    aws_s3_bucket      = var.aws_s3_bucket
    aws_access_key     = var.aws_access_key
    aws_secret_key     = var.aws_secret_key
  }))

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project_name}-instance"
    }
  }
}

# Auto Scaling Group
resource "aws_autoscaling_group" "app" {
  name                      = "${var.project_name}-asg"
  vpc_zone_identifier       = var.private_subnet_ids
  target_group_arns         = [var.target_group_arn]
  health_check_type         = "ELB"
  health_check_grace_period = 300
  min_size                  = var.asg_min_size
  max_size                  = var.asg_max_size
  desired_capacity          = var.asg_desired_capacity

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.project_name}-asg-instance"
    propagate_at_launch = true
  }
}

# SSM Run Command用のIAMポリシー追加（既存のssm_managedに加えて）
resource "aws_iam_role_policy" "ssm_send_command" {
  name = "${var.project_name}-ssm-send-command"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ssm:SendCommand",
        "ssm:GetCommandInvocation"
      ]
      Resource = "*"
    }]
  })
}

# RDS起動完了を待つ
resource "null_resource" "wait_for_rds" {
  provisioner "local-exec" {
    command = <<-EOT
      echo "Waiting for RDS to be available..."
      aws rds wait db-instance-available \
        --db-instance-identifier $(aws rds describe-db-instances \
          --query "DBInstances[?Endpoint.Address=='${var.db_host}'].DBInstanceIdentifier" \
          --output text \
          --region ${var.region})
    EOT
  }
}


# Auto Scaling Groupの起動完了を待つ
resource "null_resource" "wait_for_asg" {
  depends_on = [aws_autoscaling_group.app, null_resource.wait_for_rds]

  provisioner "local-exec" {
    command = "sleep 180" # EC2起動とDocker起動を待つ
  }
}

# SSM Run Commandでマイグレーション実行
resource "aws_ssm_document" "django_setup" {
  name          = "${var.project_name}-django-setup"
  document_type = "Command"

  content = jsonencode({
    schemaVersion = "2.2"
    description   = "Run Django migrations and seed data"
    mainSteps = [{
      action = "aws:runShellScript"
      name   = "runDjangoSetup"
      inputs = {
        runCommand = [
          "if [ -f /app/.django_setup_done ]; then echo 'Django setup already completed'; exit 0; fi",
          "cd /app",
          "docker compose -f docker-compose.prod.yml --env-file .env exec -T backend python manage.py migrate",
          "docker compose -f docker-compose.prod.yml --env-file .env exec -T backend python manage.py shell -c 'from web.seed_dummy import seed; seed()'",
          "touch /app/.django_setup_done"
        ]
      }
    }]
  })
}


# SSM Run Command実行
resource "null_resource" "run_django_setup" {
  depends_on = [null_resource.wait_for_asg, aws_ssm_document.django_setup]

  triggers = {
    django_setup_revision = var.django_setup_revision
  }

  provisioner "local-exec" {
    command = <<-EOT
      INSTANCE_ID=$(aws ec2 describe-instances \
        --filters "Name=tag:aws:autoscaling:groupName,Values=${aws_autoscaling_group.app.name}" \
                  "Name=instance-state-name,Values=running" \
        --query "Reservations[0].Instances[0].InstanceId" \
        --output text \
        --region ${var.region})
      
      COMMAND_ID=$(aws ssm send-command \
        --document-name "${aws_ssm_document.django_setup.name}" \
        --instance-ids "$INSTANCE_ID" \
        --query "Command.CommandId" \
        --output text \
        --region ${var.region})

      aws ssm wait command-executed \
        --command-id "$COMMAND_ID" \
        --instance-id "$INSTANCE_ID" \
        --region ${var.region}

      STATUS=$(aws ssm get-command-invocation \
        --command-id "$COMMAND_ID" \
        --instance-id "$INSTANCE_ID" \
        --query "Status" \
        --output text \
        --region ${var.region})

      if [ "$STATUS" != "Success" ]; then
        echo "Django setup failed with status: $STATUS" >&2
        exit 1
      fi
    EOT
  }
}

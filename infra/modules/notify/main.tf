terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
    archive = {
      source = "hashicorp/archive"
    }
  }
}

data "archive_file" "notify_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/lambda/notify.zip"
}

resource "aws_sns_topic" "ec2_ready" {
  name = "${var.environment}-ec2-ready-topic"
}

resource "aws_cloudwatch_event_rule" "ec2_ready" {
  name        = "${var.environment}-ec2-ready-rule"
  description = "Notify when EC2 launch succeeds in target ASG"

  event_pattern = jsonencode({
    source      = ["aws.autoscaling"]
    detail-type = ["EC2 Instance Launch Successful"]
    detail = {
      AutoScalingGroupName = [var.autoscaling_group_name]
    }
  })
}

resource "aws_cloudwatch_event_target" "ec2_ready_to_sns" {
  rule      = aws_cloudwatch_event_rule.ec2_ready.name
  target_id = "Ec2ReadyToSns"
  arn       = aws_sns_topic.ec2_ready.arn
}

resource "aws_cloudwatch_event_rule" "ec2_error" {
  name        = "${var.environment}-ec2-error-rule"
  description = "Notify when EC2 launch/terminate fails in target ASG"

  event_pattern = jsonencode({
    source = ["aws.autoscaling"]
    detail-type = [
      "EC2 Instance Launch Unsuccessful",
      "EC2 Instance Terminate Unsuccessful",
    ]
    detail = {
      AutoScalingGroupName = [var.autoscaling_group_name]
    }
  })
}

resource "aws_cloudwatch_event_target" "ec2_error_to_sns" {
  rule      = aws_cloudwatch_event_rule.ec2_error.name
  target_id = "Ec2ErrorToSns"
  arn       = aws_sns_topic.ec2_ready.arn
}

data "aws_iam_policy_document" "sns_topic_policy" {
  statement {
    sid       = "AllowEventBridgePublish"
    effect    = "Allow"
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.ec2_ready.arn]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values = [
        aws_cloudwatch_event_rule.ec2_ready.arn,
        aws_cloudwatch_event_rule.ec2_error.arn,
      ]
    }
  }
}

resource "aws_sns_topic_policy" "ec2_ready" {
  arn    = aws_sns_topic.ec2_ready.arn
  policy = data.aws_iam_policy_document.sns_topic_policy.json
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "notify_lambda" {
  name               = "${var.environment}-ec2-ready-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy" "notify_lambda" {
  name = "${var.environment}-ec2-ready-lambda-policy"
  role = aws_iam_role.notify_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "notify_lambda" {
  name              = "/aws/lambda/${var.environment}-ec2-ready-notify"
  retention_in_days = 30
}

resource "aws_lambda_function" "notify" {
  function_name    = "${var.environment}-ec2-ready-notify"
  role             = aws_iam_role.notify_lambda.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.notify_zip.output_path
  source_code_hash = data.archive_file.notify_zip.output_base64sha256
  timeout          = 15

  environment {
    variables = {
      ENVIRONMENT                   = var.environment
      APP_URL                       = var.app_url
      MATTERMOST_WEBHOOK_PARAM_NAME = var.mattermost_webhook_param_name
    }
  }

  depends_on = [aws_cloudwatch_log_group.notify_lambda]
}

resource "aws_sns_topic_subscription" "notify_lambda" {
  topic_arn = aws_sns_topic.ec2_ready.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.notify.arn
}

resource "aws_lambda_permission" "allow_sns" {
  statement_id  = "AllowExecutionFromSns"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.notify.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.ec2_ready.arn
}

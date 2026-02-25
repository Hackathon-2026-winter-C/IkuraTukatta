output "sns_topic_arn" {
  value = aws_sns_topic.ec2_ready.arn
}

output "event_rule_name" {
  value = aws_cloudwatch_event_rule.ec2_ready.name
}

output "lambda_function_name" {
  value = aws_lambda_function.notify.function_name
}

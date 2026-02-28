import json
import os
import urllib.request

import boto3

ssm_client = boto3.client("ssm")
cached_webhook_url = None


def get_webhook_url():
    global cached_webhook_url
    if cached_webhook_url:
        return cached_webhook_url

    param_name = os.environ["MATTERMOST_WEBHOOK_PARAM_NAME"]
    response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
    cached_webhook_url = response["Parameter"]["Value"]
    return cached_webhook_url


def parse_sns_message(event):
    records = event.get("Records", [])
    if not records:
        return event

    sns_message = records[0].get("Sns", {}).get("Message")
    if not sns_message:
        return event

    try:
        return json.loads(sns_message)
    except json.JSONDecodeError:
        return {"raw_message": sns_message}


def clean(value):
    return str(value).strip() if value is not None else ""


def get_detail(payload):
    detail = payload.get("detail", {})
    return detail if isinstance(detail, dict) else {}


def build_mattermost_text(payload):
    detail_type = clean(payload.get("detail-type"))
    detail = get_detail(payload)
    asg_name = clean(detail.get("AutoScalingGroupName"))
    instance_id = clean(detail.get("EC2InstanceId"))
    app_url = os.environ.get("APP_URL", "https://ikuratukatta.click")

    if detail_type == "EC2 Instance Launch Successful":
        lines = [
            ":rocket:",
            "AWSにデプロイが完了しました",
            app_url,
        ]
        if asg_name:
            lines.append(f"ASG: {asg_name}")
        if instance_id:
            lines.append(f"Instance: {instance_id}")
        return "\n".join(lines)

    if detail_type in {
        "EC2 Instance Launch Unsuccessful",
        "EC2 Instance Terminate Unsuccessful",
    }:
        status_code = clean(detail.get("StatusCode"))
        status_message = clean(detail.get("StatusMessage"))
        cause = clean(detail.get("Cause"))
        activity_id = clean(detail.get("ActivityId"))
        details = detail.get("Details")

        lines = [
            ":rotating_light:",
            f"EC2エラーを検知しました ({detail_type})",
        ]
        if app_url:
            lines.append(app_url)
        if asg_name:
            lines.append(f"ASG: {asg_name}")
        if instance_id:
            lines.append(f"Instance: {instance_id}")
        if status_code:
            lines.append(f"ErrorCode: {status_code}")
        if status_message:
            lines.append(f"Message: {status_message}")
        if cause:
            lines.append(f"Cause: {cause}")
        if activity_id:
            lines.append(f"ActivityId: {activity_id}")
        if details:
            lines.append(f"Details: {json.dumps(details, ensure_ascii=False)}")
        return "\n".join(lines)

    return "\n".join(
        [
            ":information_source:",
            "Auto Scaling イベントを受信しました",
            json.dumps(payload, ensure_ascii=False),
        ]
    )


def post_to_mattermost(text):
    body = json.dumps({"text": text}).encode("utf-8")
    request = urllib.request.Request(
        url=get_webhook_url(),
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status


def lambda_handler(event, context):
    del context
    payload = parse_sns_message(event)
    text = build_mattermost_text(payload)
    status = post_to_mattermost(text)
    return {"statusCode": status}

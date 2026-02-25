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


def build_mattermost_text(payload):
    del payload
    return "\n".join(
        [
            ":rocket:",
            "AWSにデプロイが完了しました",
            os.environ.get("APP_URL", "https://ikuratukatta.click"),
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

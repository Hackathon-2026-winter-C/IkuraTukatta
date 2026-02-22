# backend/web/receipt_bedrock_service.py
import json
import re
import boto3
from django.conf import settings


def _extract_json(text: str):
    text = text.strip()
    text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.IGNORECASE)
    return json.loads(text)


def _image_format_from_media_type(media_type: str) -> str:
    media = (media_type or "").lower().strip()
    mapping = {
        "image/jpeg": "jpeg",
        "image/jpg": "jpeg",
        "image/png": "png",
        "image/webp": "webp",
    }
    if media not in mapping:
        raise ValueError("unsupported_image_type")
    return mapping[media]


def _extract_text_from_converse_response(response: dict) -> str:
    message = (response.get("output") or {}).get("message") or {}
    blocks = message.get("content") or []
    parts = []
    for block in blocks:
        text = block.get("text")
        if isinstance(text, str):
            parts.append(text)
    return "".join(parts).strip()


def _print_token_usage(response: dict) -> None:
    usage = response.get("usage") or {}
    input_tokens = usage.get("inputTokens", usage.get("input_tokens", 0))
    output_tokens = usage.get("outputTokens", usage.get("output_tokens", 0))
    total_tokens = usage.get("totalTokens", usage.get("total_tokens", 0))

    print("--- トークン使用量 ---")
    print(f"入力: {input_tokens}")
    print(f"出力: {output_tokens}")
    print(f"合計: {total_tokens}")


def analyze_receipt_with_bedrock(image_bytes: bytes, media_type: str = "image/jpeg"):
    image_format = _image_format_from_media_type(media_type)
    client = boto3.client("bedrock-runtime", region_name=settings.BEDROCK_REGION_NAME)

    prompt = (
        "レシート画像から日付と合計金額を抽出してください。"
        "合計は税込金額で正確に抽出してください。（合計金額横の金額）"
        "お預かりとかお釣りは抜きにしてください。"
        "JSONのみ返してください。"
        '{"date":"YYYY-MM-DD or null","total_amount":12345 or null}'
    )

    response = client.converse(
        modelId=settings.BEDROCK_MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {"text": prompt},
                    {
                        "image": {
                            "format": image_format,
                            "source": {"bytes": image_bytes},
                        }
                    },
                ],
            }
        ],
        inferenceConfig={"maxTokens": 300, "temperature": 0},
    )
    _print_token_usage(response)

    text = _extract_text_from_converse_response(response)
    if not text:
        raise RuntimeError("empty_bedrock_response")

    return _extract_json(text)

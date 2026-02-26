# from datetime import date, datetime
# import calendar
# import json
# import re

# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.decorators import login_required
# from django.db.models import Q
# from django.http import JsonResponse
# from django.shortcuts import redirect, render
# from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
# from django.views.decorators.http import require_GET, require_POST
# from collections import defaultdict

# from PIL import Image 
# import easyocr
# import cv2
# import numpy as np

# from .forms import EmailUserCreationForm, UserUpdateForm
# from .models import Category, MoneyFlow, User

# reader = easyocr.Reader(['ja', 'en'], gpu=False)

# # ===== OCRをカード, キャッシュレス対応にする =====
# def extract_total_amount(text):
#     lines = text.splitlines()

#     exclude_words = [
#         "お預かり", "お釣り", "釣",
#         "クレジット", "カード", "VISA", "MASTER", "JCB",
#         "PayPay", "Suica", "PASMO", "ICOCA", "ID", "QUICPay"
#     ]

#     amount_pattern = r"(\d{1,3}(?:,\d{3})+|\d+)"

#     # ① 合計キーワード優先
#     for i, line in enumerate(lines):
#         if re.search(r"(合計|総計|税込|お会計)", line):
#             m = re.search(amount_pattern, line)
#             if m:
#                 return int(m.group(1).replace(",", "")), None, 0.95
#             elif i + 1 < len(lines):
#                 m2 = re.search(amount_pattern, lines[i+1])
#                 if m2:
#                     return int(m2.group(1).replace(",", "")), None, 0.9

#     # ② 最大フォールバック
#     candidates = []                
#     for line in lines:
#         if any (word in line for word in exclude_words):
#             continue

#         for m in re.finditer(amount_pattern, line):
#             val = int(m.group(1).replace(",", ""))
#             if 50 <= val <= 100000:
#                 candidates.append(val)

#     if candidates:
#         return max(candidates), "合計行が取得できなかったため金額から推定しました", 0.6

#     # ③ 失敗
#     return None, "金額を取得できませんでした", 0.0


# # ===== レシートアップロードAPI(解析のみ) =====
# @login_required(login_url="login")
# @require_POST
# @csrf_protect
# def receipt_upload_api(request):
#     image = request.FILES.get("image")
#     if not image:
#         return JsonResponse({"ok": False, "error": "image is required"}, status=400)

#     img = Image.open(image).convert("RGB")

#     # OpenCVで前処理をする
#     img_np = np.array(img)

#     # サイズ補正
#     h, w = img_np.shape[:2]
#     if w < 500:
#         scale = 500 / w
#         img_np = cv2.resize(img_np, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

#     # グレースケール
#     gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

#     # 自動二値化(Adaptive)
#     gray = cv2.adaptiveThreshold(
#         gray,
#         255,
#         cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#         cv2.THRESH_BINARY,
#         15,
#         5
#     )

#     # EasyOCR
#     results = reader.readtext(
#         gray,
#         detail=1,
#         paragraph=False,
#         text_threshold=0.6,
#         low_text=0.3
#     )

#     print("===== EASYOCR RESULTS =====")
#     print(results)
#     print("===========================")

#     text = "\n".join([r[1] for r in results])

#     print("===== OCR TEXT =====")
#     print(text)
#     print("====================")

#     print("IMG SHAPE:", img_np.shape)
#     print("IMG DTYPE:", img_np.dtype)

#     # 合計金額抽出
#     total, amount_warning, confidence = extract_total_amount(text)

#     if total is None:
#         expense_date = datetime.today().date()
#         return JsonResponse({
#             "ok":True,
#             "amount": 0,
#             "date": expense_date.strftime("%Y-%m-%d"),
#             "warning": amount_warning,
#             "confidence": confidence
#         })

#     # 日付抽出(OCR誤認補正あり)
#     date_warning = None
#     text_for_date = text.replace("村", "月").replace('"', "日").replace("'", "日")

#     date_match = re.search(
#         r"(\d{2,4}年\d{1,2}月\d{1,2}日)",
#         text_for_date
#     )

#     if not date_match:
#         print("⚠️ 日付がOCRから取得できませんでした。今日の日付を使用します。")
#         expense_date = datetime.today().date()
#         date_warning = "日付は自動取得できなかったため今日の日付を設定しました"
#     else:
#         date_raw = date_match.group()

#         date_str = date_raw.replace("年", "/").replace("月", "/").replace("日", "")
#         parts = date_str.split("/")

#         if len(parts[0]) == 2: # 26年　→　2026年
#             parts[0] = "20" + parts[0]

#         try:
#             expense_date = datetime.strptime("/".join(parts), "%Y/%m/%d").date()
#             date_warning= None
#         except ValueError:
#             expense_date = datetime.today().date()
#             date_warning = "日付の解析に失敗したため今日の日付を設定しました"


#     return JsonResponse({
#         "ok": True, 
#         "amount": total, 
#         "date": expense_date.strftime("%Y-%m-%d"),
#         "warning": date_warning,
#         "warning": amount_warning or date_warning,
#         "confidence": confidence,
#     })

# # ===== 保存用API =====
# @login_required(login_url="login")
# @require_POST
# @csrf_protect
# def receipt_save_api(request):
#     data = json.loads(request.body.decode("utf-8"))

#     try:
#         amount = int(data.get("amount"))
#         if amount <= 0:
#             return JsonResponse({"ok": False, "error": "金額が不正です"}, status=400)

#         date_str = data.get("date")
#         if not date_str:
#             return JsonResponse({"ok": False, "error": "日付がありません"}, status=400)

#         expense_date = datetime.strptime(date_str, "%Y-%m-%d").date()
#     except Exception:
#         return JsonResponse({"ok": False, "error": "入力値が不正です"}, status=400)

#     category = Category.objects.filter(user=request.user, is_in_type=False).order_by("id").first()
#     if not category:
#         return JsonResponse({"ok": False, "error": "カテゴリが存在しません"}, status=400)
#     category_name = data.get("category")
#     if not category_name:
#         return JsonResponse({"ok": False, "error": "カテゴリがありません"}, status=400)
    
#     category, _ = Category.objects.get_or_create(
#         user=request.user,
#         is_in_type=False,
#         name=category_name
#     )

#     mf = MoneyFlow.objects.create(
#         category=category,
#         amount=amount,
#         expense_date=expense_date,
#         memo="レシートから自動登録"
#     )

#     return JsonResponse({"ok": True, "id": mf.id})
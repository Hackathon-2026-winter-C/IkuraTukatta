# backend/web/ledger_utils.py

from django.contrib.auth import get_user_model
from .models import ShareGroupMember

User = get_user_model()

# 現在選択中の共有グループIDを保存するためのセッションキー
GROUP_SESSION_KEY = "current_share_group_id"

# 共有グループの利用可否を判定する
def can_use_group(group_id: int, user) -> bool:

    # 未ログインユーザーは利用不可
    if not user or not getattr(user, "is_authenticated", False):
        return False

    # group_id と user.id の組み合わせが存在するか確認
    return ShareGroupMember.objects.filter(
        share_group_id=group_id,
        user_id=user.id,
    ).exists()

# セッションから現在のグループIDを取得する
def get_current_group_id(request):

    user = request.user

    # セッションから現在のグループIDを取得
    gid = request.session.get(GROUP_SESSION_KEY)
    if not gid:
        return None

    # int に変換できない場合は破棄
    try:
        gid = int(gid)
    except Exception:
        request.session.pop(GROUP_SESSION_KEY, None)
        return None

    # ユーザーがそのグループを利用できるか確認
    if not can_use_group(gid, user):
        # 不正な値なのでセッションから削除
        request.session.pop(GROUP_SESSION_KEY, None)
        return None

    return gid

# 現在の表示対象となる user_id のリストを返す
def get_scope_user_ids(request):

    user = request.user

    # 現在有効なグループIDを取得
    gid = get_current_group_id(request)

    # グループ未選択の場合は自分のみ
    if not gid:
        return [user.id]

    # グループメンバーの user_id 一覧を取得
    member_ids = list(
        ShareGroupMember.objects
        .filter(share_group_id=gid)
        .values_list("user_id", flat=True)
    )

    # 何らかの理由で空配列になった場合の保険
    return member_ids or [user.id]

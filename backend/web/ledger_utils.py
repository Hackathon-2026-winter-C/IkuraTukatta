# backend/web/ledger_utils.py
from django.contrib.auth import get_user_model

from .models import LedgerShare

User = get_user_model()

SESSION_KEY = "ledger_owner_id"


def can_view(owner_id: int, viewer) -> bool:
    """
    viewer(ログイン中ユーザー)が owner_id の家計簿を閲覧できるか
    - 自分自身の家計簿はOK
    - LedgerShare(owner=owner_id, viewer=viewer) があればOK
    """
    if not viewer or not getattr(viewer, "is_authenticated", False):
        return False

    if int(owner_id) == int(viewer.id):
        return True

    return LedgerShare.objects.filter(owner_id=owner_id, viewer_id=viewer.id).exists()


def get_ledger_owner(request):
    """
    セッションに選択中の家計簿ownerが入っていればそれを返す。
    不正/権限なし/存在しない場合は自分に戻す。
    """
    viewer = request.user
    owner_id = request.session.get(SESSION_KEY)

    if not owner_id:
        return viewer

    try:
        owner_id = int(owner_id)
    except Exception:
        request.session.pop(SESSION_KEY, None)
        return viewer

    if not can_view(owner_id, viewer):
        request.session.pop(SESSION_KEY, None)
        return viewer

    owner = User.objects.filter(id=owner_id).first()
    if not owner:
        request.session.pop(SESSION_KEY, None)
        return viewer

    return owner

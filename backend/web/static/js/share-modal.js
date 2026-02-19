// backend/web/static/js/share-modal.js
// 共有モーダル UI 制御（グループ一覧 / メンバー一覧 / メンバー編集 / メンバー削除確認 / グループ削除確認）

(function () {
  // =========================
  // Utils（DOM操作・エスケープ・Cookie・API）
  // =========================

  // 表示/非表示（Tailwindの hidden を付け外し）
  function show(el) {
    el?.classList.remove("hidden");
  }
  function hide(el) {
    el?.classList.add("hidden");
  }

  // innerHTML に入れる前に最低限のエスケープ（XSS対策）
  function escapeHtml(s) {
    return String(s ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  // DjangoのCSRF用 cookie を読む
  function getCookie(name) {
    const m = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]+)"));
    return m ? decodeURIComponent(m[2]) : "";
  }

  // GET: JSON を取得。失敗時は {status, data} を throw
  async function apiGet(url) {
    const res = await fetch(url, { credentials: "same-origin" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw { status: res.status, data };
    return data;
  }

  // POST: CSRF付きで JSON を送信。失敗時は {status, data} を throw
  async function apiPost(url, body) {
    const csrftoken = getCookie("csrftoken");
    const res = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
      body: JSON.stringify(body || {}),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw { status: res.status, data };
    return data;
  }

  // DOM準備ができたら初期化
  function onReady(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  // =========================
  // 初期化（DOM取得・状態管理・イベント登録）
  // =========================
  onReady(() => {
    // テンプレ（account.html）側で window.__CURRENT_USER_ID__ をセットしている想定
    // これを使って「自分を一覧に表示しない」フィルタに使う
    const MY_ID = window.__CURRENT_USER_ID__;

    // -------------------------
    // DOM参照：グループ一覧（作成含む）
    // -------------------------
    const openBtn = document.getElementById("open-share-modal");
    const groupsModal = document.getElementById("share-modal");
    const modal1Bg = document.getElementById("share-modal-bg");
    const okEl = document.getElementById("share-ok");
    const errEl = document.getElementById("share-error");
    const groupListEl = document.getElementById("group-list");
    const groupNameEl = document.getElementById("group-name");
    const groupCreateBtn = document.getElementById("group-create");
    const shareCancelBtn = document.getElementById("share-cancel");

    // -------------------------
    // DOM参照：メンバー一覧（追加含む）
    // -------------------------
    const membersModal = document.getElementById("share-members-modal");
    const modal2Bg = document.getElementById("share-members-bg");
    const membersGroupNameEl = document.getElementById("members-group-name");
    const memberListEl = document.getElementById("member-list");
    const memberEmailEl = document.getElementById("member-email");
    const memberAddBtn = document.getElementById("member-add");
    const membersBackBtn = document.getElementById("members-back");
    const groupDeleteBtn = document.getElementById("group-delete");

    // -------------------------
    // DOM参照：メンバー編集（※今の仕様では基本使ってないが残している）
    // -------------------------
    const memberEditModal = document.getElementById("share-member-edit-modal");
    const modal3Bg = document.getElementById("share-member-edit-bg");
    const editEmailEl = document.getElementById("edit-member-email");
    const memberUpdateBtn = document.getElementById("member-update");
    const memberDeleteBtn = document.getElementById("member-delete");
    const memberEditCancelBtn = document.getElementById("member-edit-cancel");

    // -------------------------
    // DOM参照：メンバー削除確認
    // -------------------------
    const memberRemoveModal = document.getElementById("share-remove-modal");
    const modal4Bg = document.getElementById("share-remove-bg");
    const removeTitleEl = document.getElementById("share-remove-title");
    const removeConfirmBtn = document.getElementById("share-remove-confirm");
    const removeCancelBtn = document.getElementById("share-remove-cancel");
    const removeGroupNameEl = document.getElementById("share-remove-group-name");

    // -------------------------
    // DOM参照：グループ削除確認
    // -------------------------
    const groupRemoveModal = document.getElementById("group-remove-modal");
    const groupRemoveBg = document.getElementById("group-remove-bg");
    const groupRemoveTitleEl = document.getElementById("group-remove-title");
    const groupRemoveConfirmBtn = document.getElementById("group-remove-confirm");
    const groupRemoveCancelBtn = document.getElementById("group-remove-cancel");

    // このページに共有UIが無いなら何もしない（別ページでもこのJSが読み込まれる想定）
    if (!openBtn || !groupsModal) return;

    // =========================
    // 状態（選択中のグループ / 削除対象のメンバー）
    // =========================
    let currentGroupId = null;
    let currentGroupName = "";

    // 「削除対象」として選んだメンバー情報
    let currentMemberId = null;
    let currentMemberEmail = "";
    let currentMemberLabel = "";

    // =========================
    // グループ一覧モーダル内のメッセージ（成功/エラー）
    // =========================
    function clearMsg() {
      if (okEl) {
        okEl.textContent = "";
        hide(okEl);
      }
      if (errEl) {
        errEl.textContent = "";
        hide(errEl);
      }
    }
    function showErr(msg) {
      if (!errEl) return;
      errEl.textContent = msg || "";
      show(errEl);
      if (okEl) hide(okEl);
    }
    function showOk(msg) {
      if (!okEl) return;
      okEl.textContent = msg || "";
      show(okEl);
      if (errEl) hide(errEl);
    }

    // =========================
    // モーダル切り替え（表示状態の制御）
    // =========================
    function closeAll() {
      // すべて閉じる（戻り先を考えなくていい“完全クローズ”）
      hide(groupsModal);
      hide(membersModal);
      hide(memberEditModal);
      hide(memberRemoveModal);
      hide(groupRemoveModal);
      clearMsg();
    }

    function openGroupsModal() {
      // グループ一覧を開く（開くたびに最新の一覧を取得）
      clearMsg();

      show(groupsModal);
      hide(membersModal);
      hide(memberEditModal);
      hide(memberRemoveModal);
      hide(groupRemoveModal);

      refreshGroups().catch(() => {
        if (groupListEl) groupListEl.innerHTML = `<p class="text-xs text-red-500">取得失敗</p>`;
      });

      setTimeout(() => groupNameEl?.focus?.(), 50);
    }

    function openMembersModal(gid, gname) {
      // グループを選択 → メンバー一覧を開く
      currentGroupId = gid;
      currentGroupName = gname || "グループ";
      if (membersGroupNameEl) membersGroupNameEl.textContent = currentGroupName;

      hide(groupsModal);
      show(membersModal);
      hide(memberEditModal);
      hide(memberRemoveModal);
      hide(groupRemoveModal);

      if (memberEmailEl) memberEmailEl.value = "";

      refreshMembers(gid).catch(() => {
        if (memberListEl) memberListEl.innerHTML = `<p class="text-xs text-red-500">取得失敗</p>`;
      });

      setTimeout(() => memberEmailEl?.focus?.(), 50);
    }

    function openMemberEditModal(member) {
      // メンバー編集（update APIがある場合の想定。今は基本使ってない）
      currentMemberId = member.id;
      currentMemberEmail = member.email || "";
      currentMemberLabel = member.username || member.email || "メンバー";

      if (editEmailEl) editEmailEl.value = currentMemberEmail;

      hide(membersModal);
      show(memberEditModal);
      hide(memberRemoveModal);

      setTimeout(() => editEmailEl?.focus?.(), 50);
    }

    function openRemoveModal() {
      // メンバー削除確認を開く
      if (removeTitleEl) removeTitleEl.textContent = `${currentMemberLabel}を削除しますか？`;
      if (removeGroupNameEl) removeGroupNameEl.textContent = currentGroupName || "このグループ";

      // 今の仕様：メンバー一覧 → 直接 削除確認へ
      hide(membersModal);
      hide(memberEditModal);
      show(memberRemoveModal);
    }

    function openGroupRemoveModal() {
      // グループ削除確認を開く
      if (!currentGroupId) return;
      if (groupRemoveTitleEl) groupRemoveTitleEl.textContent = `${currentGroupName || "このグループ"}を削除しますか？`;

      hide(membersModal);
      hide(memberEditModal);
      hide(memberRemoveModal);
      show(groupRemoveModal);
    }

    // =========================
    // 描画（APIの配列 → ボタン一覧HTML）
    // =========================
    function renderGroups(items) {
      if (!groupListEl) return;

      if (!items || items.length === 0) {
        groupListEl.innerHTML = `<p class="text-xs text-black/50">グループがありません</p>`;
        return;
      }

      // グループ一覧をボタンとして描画
      groupListEl.innerHTML = items
        .map((it) => {
          const activeCls = "bg-white/70";
          const sub = it.desc ? `<span class="text-[11px] text-black/50">${escapeHtml(it.desc)}</span>` : "";
          return `
            <button type="button"
              class="w-full rounded-2xl px-4 py-3 flex items-center justify-between ${activeCls}"
              style="box-shadow: var(--app-mainbutton-shadow);"
              data-gid="${it.id}"
              data-gname="${escapeHtml(it.name)}">
              <span class="text-sm font-semibold text-[#111]">${escapeHtml(it.name)}</span>
              ${sub}
            </button>
          `;
        })
        .join("");

      // 押されたグループを開く（メンバー一覧へ）
      groupListEl.querySelectorAll("button[data-gid]").forEach((b) => {
        b.addEventListener("click", () => {
          const gid = parseInt(b.dataset.gid, 10);
          const gname = b.dataset.gname || "グループ";
          openMembersModal(gid, gname);
        });
      });
    }

    function renderMembers(members) {
      if (!memberListEl) return;

      // 自分を除外しているので、空表示は普通に起きる
      if (!members || members.length === 0) {
        memberListEl.innerHTML = `<p class="text-xs text-black/50">他のメンバーはいないよ</p>`;
        return;
      }

      // メンバー一覧をボタンとして描画（押したら削除確認へ）
      memberListEl.innerHTML = members
        .map((m) => {
          const label = m.username || m.email || "";
          return `
            <button type="button"
              class="w-full rounded-2xl px-4 py-3 bg-white/70 flex flex-col items-start gap-1"
              style="box-shadow: var(--app-mainbutton-shadow);"
              data-mid="${m.id}"
              data-email="${escapeHtml(m.email || "")}"
              data-username="${escapeHtml(m.username || "")}">
              <span class="text-sm font-semibold text-[#111]">${escapeHtml(label)}</span>
              <span class="text-[11px] text-black/50">${escapeHtml(m.email || "")}</span>
            </button>
          `;
        })
        .join("");

      // 押されたメンバーを「削除対象」として保持し、削除確認へ
      memberListEl.querySelectorAll("button[data-mid]").forEach((b) => {
        b.addEventListener("click", () => {
          const id = parseInt(b.dataset.mid, 10);
          const email = b.dataset.email || "";
          const username = b.dataset.username || "";

          currentMemberId = id;
          currentMemberEmail = email;
          currentMemberLabel = username || email || "メンバー";

          openRemoveModal();
        });
      });
    }

    // =========================
    // データ取得（取得 → render）
    // =========================
    async function refreshGroups() {
      if (groupListEl) groupListEl.innerHTML = `<p class="text-xs text-black/50">読み込み中…</p>`;

      // 自分が参加できるグループ一覧
      const data = await apiGet("/api/groups/available/");
      const groups = data.groups || [];

      // 表示に必要な形に整える
      const items = groups.map((g) => ({
        id: g.id,
        name: g.name,
      }));

      renderGroups(items);
    }

    async function refreshMembers(groupId) {
      if (memberListEl) memberListEl.innerHTML = `<p class="text-xs text-black/50">読み込み中…</p>`;

      // グループのメンバー一覧
      const data = await apiGet(`/api/groups/${groupId}/members/`);

      // 仕様：自分は一覧に出さない（UI側で除外）
      const members = (data.members || []).filter((m) => m.id !== MY_ID);

      renderMembers(members);
    }

    // =========================
    // イベント：開く/閉じる/戻る
    // =========================

    // 共有モーダルを開く（最初はグループ一覧）
    openBtn.addEventListener("click", openGroupsModal);

    // 背景を押したら閉じる（どのモーダルでも closeAll）
    modal1Bg?.addEventListener("click", closeAll);
    modal2Bg?.addEventListener("click", closeAll);
    modal3Bg?.addEventListener("click", closeAll);
    modal4Bg?.addEventListener("click", closeAll);
    groupRemoveBg?.addEventListener("click", closeAll);

    // グループ一覧の「閉じる」
    shareCancelBtn?.addEventListener("click", closeAll);

    // メンバー一覧 → グループ一覧へ戻る
    membersBackBtn?.addEventListener("click", openGroupsModal);

    // メンバー編集 → メンバー一覧へ戻る
    memberEditCancelBtn?.addEventListener("click", () => {
      hide(memberEditModal);
      show(membersModal);
    });

    // メンバー削除確認 → メンバー一覧へ戻る
    removeCancelBtn?.addEventListener("click", () => {
      hide(memberRemoveModal);
      show(membersModal);
    });

    // グループ削除確認 → メンバー一覧へ戻る
    groupRemoveCancelBtn?.addEventListener("click", () => {
      hide(groupRemoveModal);
      show(membersModal);
    });

    // =========================
    // グループ作成（作成→選択→メンバー一覧へ）
    // =========================
    groupCreateBtn?.addEventListener("click", async () => {
      clearMsg();

      const name = (groupNameEl?.value || "").trim();
      if (!name) {
        showErr("グループ名を入れてね");
        return;
      }

      try {
        // create API（{id,name} または {group:{id,name}} を想定）
        const created = await apiPost("/api/groups/create/", { name });

        const gid = created?.id ?? created?.group?.id;
        const gname = created?.name ?? created?.group?.name ?? name;

        if (!gid) {
          showErr("作成に失敗したよ");
          return;
        }

        // 作ったグループを「選択中」にする（失敗しても進む）
        try {
          await apiPost("/api/groups/select/", { group_id: gid });
        } catch (_) {}

        if (groupNameEl) groupNameEl.value = "";
        openMembersModal(gid, gname);
      } catch (e) {
        showErr(e?.data?.message || "作成に失敗したよ");
      }
    });

    // =========================
    // メンバー追加（追加→一覧を再取得）
    // =========================
    memberAddBtn?.addEventListener("click", async () => {
      if (!currentGroupId) return;

      const email = (memberEmailEl?.value || "").trim();
      if (!email) return;

      try {
        await apiPost(`/api/groups/${currentGroupId}/members/add/`, { email });
        if (memberEmailEl) memberEmailEl.value = "";
        await refreshMembers(currentGroupId);
      } catch (e) {
        // メッセージ欄が無いので暫定で alert
        alert(e?.data?.message || "追加に失敗したよ");
      }
    });

    // =========================
    // メンバー更新（update APIがある場合）
    // =========================
    memberUpdateBtn?.addEventListener("click", async () => {
      if (!currentGroupId || !currentMemberId) return;

      const email = (editEmailEl?.value || "").trim();
      if (!email) return;

      try {
        await apiPost(`/api/groups/${currentGroupId}/members/update/`, {
          user_id: currentMemberId,
          email,
        });

        hide(memberEditModal);
        show(membersModal);
        await refreshMembers(currentGroupId);
      } catch (e) {
        alert(e?.data?.message || "変更に失敗したよ（update APIが無いならこの機能はオフでOK）");
      }
    });

    // =========================
    // 削除：入口（確認モーダルを開くだけ）
    // =========================

    // （メンバー編集モーダル側から削除確認に行く想定）
    memberDeleteBtn?.addEventListener("click", () => {
      if (!currentMemberId) return;
      openRemoveModal();
    });

    // メンバー一覧で「グループ削除」を押したら削除確認へ
    groupDeleteBtn?.addEventListener("click", () => {
      openGroupRemoveModal();
    });

    // =========================
    // 削除：確定（API叩く）
    // =========================

    // メンバー削除を確定 → メンバー一覧を更新
    removeConfirmBtn?.addEventListener("click", async () => {
      if (!currentGroupId || !currentMemberId) return;

      try {
        await apiPost(`/api/groups/${currentGroupId}/members/remove/`, { user_id: currentMemberId });

        hide(memberRemoveModal);
        show(membersModal);
        await refreshMembers(currentGroupId);
      } catch (e) {
        alert(e?.data?.message || "削除に失敗したよ");
      }
    });

    // グループ削除を確定 → グループ一覧に戻す
    groupRemoveConfirmBtn?.addEventListener("click", async () => {
      if (!currentGroupId) return;

      try {
        await apiPost(`/api/groups/${currentGroupId}/delete/`, {});

        hide(groupRemoveModal);

        // 選択中グループをクリア
        currentGroupId = null;
        currentGroupName = "";

        openGroupsModal();
      } catch (e) {
        const code = e?.data?.error;
        if (code === "forbidden") alert("オーナーのみ削除できます");
        else alert(e?.data?.message || "グループ削除に失敗したよ");
      }
    });
  });
})();

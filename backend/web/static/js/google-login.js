window.document.addEventListener("DOMContentLoaded", () => {
  const loginButton = document.getElementById("google-login-btn");
  const hiddenContainer = document.getElementById("google-signin-hidden");
  const errorElement = document.getElementById("google-login-error");
  const clientId = String(window.GOOGLE_CLIENT_ID || "").trim();

  if (!loginButton || !hiddenContainer) {
    return;
  }

  const showError = (message) => {
    if (!errorElement) {
      return;
    }
    errorElement.textContent = message;
    errorElement.classList.remove("hidden");
  };

  const clearError = () => {
    if (!errorElement) {
      return;
    }
    errorElement.textContent = "";
    errorElement.classList.add("hidden");
  };

  const setLoading = (loading) => {
    loginButton.disabled = loading;
    loginButton.classList.toggle("opacity-60", loading);
    loginButton.classList.toggle("cursor-not-allowed", loading);
  };

  const getCsrfToken = () => {
    if (window.appUtils && typeof window.appUtils.getCookie === "function") {
      return window.appUtils.getCookie("csrftoken");
    }
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  };

  const errorMessageByCode = (code) => {
    switch (code) {
      case "credential_required":
        return "Googleの認証情報が取得できませんでした。";
      case "invalid_google_token":
      case "invalid_google_payload":
        return "Google認証に失敗しました。もう一度お試しください。";
      case "google_uid_conflict":
        return "このGoogleアカウントは別ユーザーに連携済みです。";
      case "google_client_id_not_configured":
        return "Googleログインの設定が未完了です。";
      default:
        return "Googleログインに失敗しました。";
    }
  };

  const postCredential = async (credential) => {
    const csrfToken = getCsrfToken();
    const headers = {
      "Content-Type": "application/json",
      "X-Requested-With": "XMLHttpRequest",
    };
    if (csrfToken) {
      headers["X-CSRFToken"] = csrfToken;
    }

    try {
      const response = await fetch("/auth/google/", {
        method: "POST",
        headers,
        credentials: "same-origin",
        body: JSON.stringify({ credential }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok || !payload.ok) {
        showError(errorMessageByCode(payload.error));
        setLoading(false);
        return;
      }
      window.location.href = payload.redirect_to || "/dashboard/";
    } catch (error) {
      showError("通信に失敗しました。時間をおいて再度お試しください。");
      setLoading(false);
    }
  };

  let initialized = false;
  const initGoogleIdentity = () => {
    if (initialized) {
      return true;
    }
    if (!clientId) {
      showError("Googleログインの Client ID が未設定です。");
      return false;
    }
    if (
      !(window.google && window.google.accounts && window.google.accounts.id)
    ) {
      return false;
    }

    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: (response) => {
        const credential =
          response && response.credential ? response.credential : "";
        if (!credential) {
          showError("Googleの認証情報が取得できませんでした。");
          setLoading(false);
          return;
        }
        void postCredential(credential);
      },
    });

    window.google.accounts.id.renderButton(hiddenContainer, {
      theme: "outline",
      size: "large",
      text: "continue_with",
      shape: "pill",
      width: 260,
    });

    initialized = true;
    return true;
  };

  const waitForGoogleIdentity = () =>
    new Promise((resolve) => {
      if (initGoogleIdentity()) {
        resolve(true);
        return;
      }
      let retries = 0;
      const timer = setInterval(() => {
        retries += 1;
        if (initGoogleIdentity()) {
          clearInterval(timer);
          resolve(true);
          return;
        }
        if (retries >= 30) {
          clearInterval(timer);
          resolve(false);
        }
      }, 200);
    });

  const clickHiddenGoogleButton = () => {
    const hiddenButton = hiddenContainer.querySelector('div[role="button"]');
    if (!hiddenButton) {
      return false;
    }
    hiddenButton.click();
    return true;
  };

  let fallbackTimer = null;
  loginButton.addEventListener("click", async () => {
    clearError();
    setLoading(true);

    const ready = await waitForGoogleIdentity();
    if (!ready) {
      showError(
        "Googleログインの読み込みに失敗しました。ページを再読み込みしてください。",
      );
      setLoading(false);
      return;
    }

    const launched = clickHiddenGoogleButton();
    if (!launched) {
      showError("Googleログインの起動に失敗しました。");
      setLoading(false);
      return;
    }

    if (fallbackTimer) {
      clearTimeout(fallbackTimer);
    }
    fallbackTimer = setTimeout(() => {
      setLoading(false);
    }, 12000);
  });
});

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("web.urls")),
    path("accounts/", include("allauth.urls")),

]

# エラーページ
handler403 = "web.views.error_403"
handler404 = "web.views.error_404"
handler500 = "web.views.error_500"


# ホットリロードできるようにする
if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
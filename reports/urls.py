from rest_framework.routers import DefaultRouter

from reports.views import SessionReportViewSet


router = DefaultRouter()
router.register("reports", SessionReportViewSet, basename="session-report")

urlpatterns = router.urls
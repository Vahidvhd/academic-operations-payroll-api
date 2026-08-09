from rest_framework.routers import DefaultRouter

from .views import SchoolViewSet, TermViewSet

router = DefaultRouter()

router.register("schools", SchoolViewSet, basename="school")
router.register("terms", TermViewSet, basename="term")

urlpatterns = router.urls
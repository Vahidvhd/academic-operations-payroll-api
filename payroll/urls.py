from rest_framework.routers import DefaultRouter

from payroll.views import TeacherTermWageViewSet


router = DefaultRouter()
router.register("teacher-term-wages", TeacherTermWageViewSet, basename="teacher-term-wage")

urlpatterns = router.urls
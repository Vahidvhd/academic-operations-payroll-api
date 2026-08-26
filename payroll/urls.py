from rest_framework.routers import DefaultRouter

from payroll.views import MonthlySalaryViewSet, TeacherTermWageViewSet

router = DefaultRouter()

router.register("teacher-term-wages", TeacherTermWageViewSet, basename="teacher-term-wage")
router.register("monthly-salaries", MonthlySalaryViewSet, basename="monthly-salary")

urlpatterns = router.urls
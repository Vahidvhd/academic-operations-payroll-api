from rest_framework.routers import DefaultRouter

from .views import (
    CourseClassViewSet,
    SchoolViewSet,
    TeacherClassAssignmentViewSet,
    TermViewSet,
)

router = DefaultRouter()

router.register("schools", SchoolViewSet, basename="school")
router.register("terms", TermViewSet, basename="term")
router.register("course-classes", CourseClassViewSet, basename="course-class")
router.register("teacher-class-assignments", TeacherClassAssignmentViewSet, basename="teacher-class-assignment")
urlpatterns = router.urls
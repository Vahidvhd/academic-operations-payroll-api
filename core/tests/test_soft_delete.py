from django.test import TestCase

from academics.models import School


class SoftDeleteTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="Test School",
            address="Test Address",
        )

    def test_instance_delete_does_not_remove_record_from_database(self):
        school_id = self.school.id

        self.school.delete()

        self.assertTrue(
            School.all_objects.filter(id=school_id).exists()
        )

    def test_default_manager_hides_soft_deleted_record(self):
        self.school.delete()

        self.assertFalse(
            School.objects.filter(id=self.school.id).exists()
        )

    def test_all_objects_manager_includes_soft_deleted_record(self):
        self.school.delete()

        deleted_school = School.all_objects.get(id=self.school.id)

        self.assertTrue(deleted_school.is_deleted)
        self.assertIsNotNone(deleted_school.deleted_at)

    def test_queryset_delete_performs_soft_delete(self):
        second_school = School.objects.create(
            name="Second School",
            address="Second Address",
        )

        school_ids = [self.school.id, second_school.id]

        School.objects.filter(id__in=school_ids).delete()

        self.assertFalse(
            School.objects.filter(id__in=school_ids).exists()
        )

        self.assertEqual(
            School.all_objects.filter(
                id__in=school_ids,
                is_deleted=True,
            ).count(),
            2,
        )
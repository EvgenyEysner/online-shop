from django.conf import settings
from django.test import TestCase

from apps.core.services.allocation import NumberAllocationService


class CustomerNumberServiceTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.first = NumberAllocationService.allocate_customer_number()

    def test_allocate_first_customer_number(self):
        self.assertEqual(self.first, f"K39-{settings.CUSTOMER_NUMBER_START}")

    def test_allocate_increments_sequence(self):
        second = NumberAllocationService.allocate_customer_number()
        self.assertEqual(self.first, f"K39-{settings.CUSTOMER_NUMBER_START}")
        self.assertEqual(second, f"K39-{settings.CUSTOMER_NUMBER_START + 1}")

from django.test import TestCase

from core.services.allocation import GlobalIdentifier


class GlobalIdentifierTests(TestCase):
    def test_next_returns_default_on_first_call(self):
        value = GlobalIdentifier.next("test_key", default=200000)
        self.assertEqual(value, 200000)

    def test_next_increments_on_subsequent_calls(self):
        first = GlobalIdentifier.next("increment_key", default=10)
        second = GlobalIdentifier.next("increment_key")
        self.assertEqual(first, 10)
        self.assertEqual(second, 11)

    def test_next_n_returns_range(self):
        values = list(GlobalIdentifier.next_n("batch_key", count=3, default=100))
        self.assertEqual(values, [100, 101, 102])

from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.utils import timezone
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Item, Order, OrderItem, Review
from apps.orders.services.review import ReviewService

User = get_user_model()

REVIEWS_URL = "/api/v1/orders/reviews/"


class ReviewServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.buyer = baker.make(
            User, email="buyer@example.com", first_name="Max", last_name="Kauf"
        )
        cls.stranger = baker.make(User, email="stranger@example.com")
        cls.item = baker.make(
            Item,
            name="Solarmodul",
            price=Decimal("100.00"),
            on_stock=5,
            rating=Decimal("0.0"),
            reviews=0,
        )
        order = baker.make(
            Order,
            customer=cls.buyer,
            email=cls.buyer.email,
            order_number="K39-TEST-rev1",
            stripe_session_id="cs_review_buyer",
            payment_status=Order.PaymentStatus.PAID,
            paid_at=timezone.now(),
        )
        baker.make(
            OrderItem,
            order=order,
            item=cls.item,
            item_name=cls.item.name,
            unit_price=cls.item.price,
            quantity=1,
        )

    def test_can_review_only_verified_purchasers(self):
        self.assertTrue(ReviewService.can_review(self.buyer, self.item))
        self.assertFalse(ReviewService.can_review(self.stranger, self.item))

    def test_upsert_rejects_non_buyer(self):
        with self.assertRaises(PermissionDenied):
            ReviewService.upsert_review(
                self.stranger, self.item, rating=5, comment="nein"
            )

    def test_upsert_updates_instead_of_duplicating(self):
        first = ReviewService.upsert_review(
            self.buyer, self.item, rating=4, comment="gut"
        )
        second = ReviewService.upsert_review(
            self.buyer, self.item, rating=5, comment="sehr gut"
        )

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Review.objects.filter(item=self.item).count(), 1)
        self.item.refresh_from_db()
        self.assertEqual(self.item.reviews, 1)
        self.assertEqual(self.item.rating, Decimal("5.0"))

    def test_delete_recalculates_aggregate(self):
        other_buyer = baker.make(User, email="second@example.com")
        other_order = baker.make(
            Order,
            customer=other_buyer,
            email=other_buyer.email,
            order_number=f"K39-TEST-{uuid4().hex[:8]}",
            stripe_session_id=f"cs_{uuid4().hex}",
            payment_status=Order.PaymentStatus.PAID,
            paid_at=timezone.now(),
        )
        baker.make(
            OrderItem,
            order=other_order,
            item=self.item,
            item_name=self.item.name,
            unit_price=self.item.price,
            quantity=1,
        )
        ReviewService.upsert_review(self.buyer, self.item, rating=5, comment="a")
        ReviewService.upsert_review(other_buyer, self.item, rating=3, comment="b")
        self.item.refresh_from_db()
        self.assertEqual(self.item.reviews, 2)
        self.assertEqual(self.item.rating, Decimal("4.0"))

        ReviewService.delete_review(self.buyer, self.item)
        self.item.refresh_from_db()
        self.assertEqual(self.item.reviews, 1)
        self.assertEqual(self.item.rating, Decimal("3.0"))


class ReviewViewSetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.buyer = baker.make(
            User, email="buyer@example.com", first_name="Max", last_name="Kauf"
        )
        cls.stranger = baker.make(User, email="stranger@example.com")
        cls.item = baker.make(
            Item, name="Solarmodul", price=Decimal("100.00"), on_stock=5
        )
        order = baker.make(
            Order,
            customer=cls.buyer,
            email=cls.buyer.email,
            order_number="K39-TEST-rev2",
            stripe_session_id="cs_review_api",
            payment_status=Order.PaymentStatus.PAID,
            paid_at=timezone.now(),
        )
        baker.make(
            OrderItem,
            order=order,
            item=cls.item,
            item_name=cls.item.name,
            unit_price=cls.item.price,
            quantity=1,
        )

    def setUp(self):
        self.client = APIClient()

    def test_list_is_public(self):
        ReviewService.upsert_review(self.buyer, self.item, rating=5, comment="top")

        response = self.client.get(f"{REVIEWS_URL}?item={self.item.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_create_by_non_buyer_is_forbidden(self):
        self.client.force_authenticate(user=self.stranger)

        response = self.client.post(
            REVIEWS_URL,
            {"item": self.item.id, "rating": 5, "comment": "fake"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_buyer_can_create_and_stranger_cannot_delete(self):
        self.client.force_authenticate(user=self.buyer)
        created = self.client.post(
            REVIEWS_URL,
            {"item": self.item.id, "rating": 4, "comment": "gut"},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.stranger)
        deleted = self.client.delete(f"{REVIEWS_URL}{created.data['id']}/")
        self.assertEqual(deleted.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Review.objects.filter(pk=created.data["id"]).exists())

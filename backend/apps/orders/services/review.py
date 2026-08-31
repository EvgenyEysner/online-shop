from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Avg, Count

from apps.orders.models import Item, Order, OrderItem, Review


class ReviewService:
    @staticmethod
    def can_review(user, item: Item) -> bool:
        """
        Nur verifizierte Käufer dürfen bewerten, reine
        DB-Abfrage gegen OrderItem, ob der Nutzer diesen Artikel bereits
        in einer bezahlten Bestellung hatte.
        """
        return OrderItem.objects.filter(
            order__customer=user,
            order__payment_status=Order.PaymentStatus.PAID,
            item=item,
        ).exists()

    @staticmethod
    @transaction.atomic
    def upsert_review(user, item: Item, *, rating: int, comment: str) -> Review:
        if not ReviewService.can_review(user, item):
            raise PermissionDenied("Nur Käufer dieses Artikels können ihn bewerten.")
        review, _ = Review.objects.update_or_create(
            item=item,
            customer=user,
            defaults={"rating": rating, "comment": comment},
        )
        ReviewService._recalculate_aggregate(item)
        return review

    @staticmethod
    @transaction.atomic
    def delete_review(user, item: Item) -> None:
        Review.objects.filter(item=item, customer=user).delete()
        ReviewService._recalculate_aggregate(item)

    @staticmethod
    def _recalculate_aggregate(item: Item) -> None:
        stats = Review.objects.filter(item=item).aggregate(
            avg=Avg("rating"), count=Count("id")
        )
        item.rating = round(stats["avg"] or 0, 1)
        item.reviews = stats["count"]
        item.save(update_fields=["rating", "reviews"])

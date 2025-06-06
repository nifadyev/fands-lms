import random
from decimal import Decimal
from typing import Any

from apps.orders.models import Order, Refund
from apps.products.models import Product
from apps.users.models import User
from core.helpers import random_string
from core.test.factory import FixtureFactory, register


@register
def order(
    self: FixtureFactory,
    slug: str | None = None,
    is_paid: bool = False,
    item: Product | None = None,
    user: User | None = None,
    author: User | None = None,
    price: Decimal | None = None,
    bank_id: str | None = "tinkoff_bank",
    **kwargs: dict[str, Any],
) -> Order:
    user = user if user else self.mixer.blend("users.User")
    price = price if price is not None else self.price()
    course = item if item else self.course(price=price)

    order = self.mixer.blend(
        "orders.Order",
        slug=slug if slug else random_string(32),
        course=course,
        price=price,
        bank_id=bank_id,
        user=user,
        author=author if author else user,
        **kwargs,
    )

    if is_paid:
        order.set_paid(silent=True)

    return order


@register
def refund(self: FixtureFactory, **kwargs: dict[str, Any]) -> Refund:
    return self.mixer.blend("orders.Refund", **kwargs)


@register
def price(self: FixtureFactory) -> Decimal:  # NOQA: ARG001
    return Decimal(str(random.randint(100_000, 100500)))

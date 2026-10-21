from typing import cast
from unittest.mock import Mock

import pytest

from shop.cart import Cart, RateProvider


def test_most_expensive_empty() -> None:
    cart = Cart()
    assert cart.most_expensive() is None


def test_most_expensive_with_items(
    cart_with_items: Cart,
) -> None:
    item = cart_with_items.most_expensive()
    assert item is not None
    assert item.name == "book"
    assert item.price == 200.0


def test_empty_cart_count() -> None:
    cart = Cart()
    assert cart.items_count() == 0


@pytest.mark.parametrize(
    ("price", "qty"),
    [(0.0, 1), (100.0, 1), (100.0, 3)],
)
def test_add_valid_item(price: float, qty: int) -> None:
    cart = Cart()
    cart.add("book", price=price, qty=qty)
    assert cart.items_count() == qty


def test_add_duplicate_item() -> None:
    cart = Cart()
    cart.add("book", price=100.0, qty=2)
    cart.add("book", price=200.0, qty=3)
    assert cart.items_count() == 5
    assert cart.total() == 500.0


@pytest.mark.parametrize("price", [-1.0, -100.0])
def test_add_negative_price(price: float) -> None:
    cart = Cart()
    with pytest.raises(ValueError, match="price"):
        cart.add("book", price=price)


@pytest.mark.parametrize("qty", [0, -1])
def test_add_invalid_quantity(qty: int) -> None:
    cart = Cart()
    with pytest.raises(ValueError, match="qty"):
        cart.add("book", price=100.0, qty=qty)


def test_remove_existing_item(cart_with_items: Cart) -> None:
    cart_with_items.remove("book")
    assert cart_with_items.items_count() == 4


def test_remove_missing_item() -> None:
    cart = Cart()
    with pytest.raises(KeyError):
        cart.remove("unknown")


def test_items_count(cart_with_items: Cart) -> None:
    assert cart_with_items.items_count() == 6


def test_total_without_discount(cart_with_items: Cart) -> None:
    assert cart_with_items.total() == 460.0


@pytest.mark.parametrize(
    ("discount", "expected"),
    [
        (0, 460.0),
        (10, 414.0),
        (50, 230.0),
        (100, 0.0),
    ],
)
def test_total_with_discount(cart_with_items: Cart, discount: int, expected: float) -> None:
    assert cart_with_items.total(discount) == pytest.approx(expected)


@pytest.mark.parametrize("discount", [-1, 101])
def test_invalid_discount(discount: int) -> None:
    cart = Cart()
    with pytest.raises(ValueError, match="discount_percent"):
        cart.total(discount)


def test_total_empty_cart() -> None:
    cart = Cart()
    assert cart.total() == 0.0


def test_total_in_usd(cart_with_items: Cart) -> None:
    rates = Mock(spec=RateProvider)
    rates.get_rate.return_value = 40.0

    result = cart_with_items.total_in("USD", cast(RateProvider, rates))

    assert result == pytest.approx(11.5)
    rates.get_rate.assert_called_once_with("USD")


@pytest.mark.parametrize("rate", [0.0, -10.0])
def test_total_in_invalid_rate(rate: float) -> None:
    rates = Mock(spec=RateProvider)
    rates.get_rate.return_value = rate
    cart = Cart()

    with pytest.raises(ValueError, match="rate"):
        cart.total_in("USD", cast(RateProvider, rates))

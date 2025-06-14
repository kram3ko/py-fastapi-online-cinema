class CartError(Exception):
    """Base exception for cart-related errors."""

    pass


class MovieNotFoundError(CartError):
    """Raised when movie doesn't exist."""

    pass


class MovieAlreadyInCartError(CartError):
    """Raised when movie is already in cart."""

    pass


class MovieAlreadyPurchasedError(CartError):
    """Raised when movie was already purchased by user."""

    pass


class CartNotFoundError(CartError):
    """Raised when cart doesn't exist."""

    pass


class MovieNotInCartError(CartError):
    """Raised when trying to remove a movie that's not in the cart."""

    pass

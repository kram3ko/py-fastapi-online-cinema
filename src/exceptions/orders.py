from fastapi import HTTPException, status


class EmptyCartException(HTTPException):
    """
    Raised when a user attempts to place an order but their cart is empty.
    """
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your cart is empty. Cannot place an order."
        )


class UnavailableMovieException(HTTPException):
    """
    Raised when none of the movies in the user's cart are available for purchase.
    This can happen if the movies were deleted or already purchased.
    """
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid movies available for purchase."
        )

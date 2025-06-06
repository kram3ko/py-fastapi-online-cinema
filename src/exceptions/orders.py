class BaseOrderException(Exception):
    """Base exception for order-related errors."""
    pass


class MovieNotFoundError(BaseOrderException):
    """Exception raised when a requested movie is not found."""
    def __init__(self, movie_id: int):
        self.detail = f"Movie with ID {movie_id} not found."
        self.status_code = 404


class MovieNotAvailableError(BaseOrderException):
    """Exception raised when a movie is not available for purchase."""
    def __init__(self, movie_name: str, movie_id: int):
        self.detail = f"Movie '{movie_name}' (ID: {movie_id}) is unavailable."
        self.status_code = 400


class MovieAlreadyPurchasedError(BaseOrderException):
    """Exception raised when a user attempts to order an already purchased movie."""
    def __init__(self, movie_name: str, movie_id: int):
        self.detail = f"Movie '{movie_name}' (ID: {movie_id}) has already been purchased by the user."
        self.status_code = 400


class CartEmptyError(BaseOrderException):
    """Exception raised when an order attempt is made with an empty or invalid cart."""
    def __init__(self, message: str = "Cannot place an order with an empty cart or no eligible movies."):
        self.detail = message
        self.status_code = 400


class OrderCancellationError(BaseOrderException):
    """Exception raised when an order cannot be canceled due to its status."""
    def __init__(self, message: str):
        self.detail = message
        self.status_code = 400


class DuplicatePendingOrderError(BaseOrderException):
    """Exception raised when a duplicate pending order for the same movies exists."""
    def __init__(self, message: str = "An order with this set of movies is already pending."):
        self.detail = message
        self.status_code = 400


class OrderNotFoundException(BaseOrderException):
    """Exception raised when a requested order is not found."""
    def __init__(self, order_id: int):
        self.detail = f"Order with ID {order_id} not found."
        self.status_code = 404


class UnauthorizedOrderAccess(BaseOrderException):
    """Exception raised when a user attempts to access an order they don't own."""
    def __init__(self):
        self.detail = "Unauthorized access to order."
        self.status_code = 403

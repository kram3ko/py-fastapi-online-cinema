from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

jwt_security = HTTPBearer()


def get_token(credentials: HTTPAuthorizationCredentials = Depends(jwt_security)) -> str:
    """
    Extracts the Bearer token from the Authorization header using Depends(HTTPBearer()).

    :param credentials: Parsed Authorization credentials from HTTPBearer.
    :return: The token string.
    """
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Expected 'Bearer'."
        )
    return credentials.credentials


def get_token_from_request(request: Request) -> str:
    """
    Manually extracts the Bearer token from the Authorization header (e.g., for middleware or utilities).

    :param request: HTTP request object.
    :return: The token string.
    """
    try:
        authorization: str = request.headers["Authorization"]
    except KeyError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header is missing")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
        )
    return token

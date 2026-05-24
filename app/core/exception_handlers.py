"""
Application exception handlers.

This module maps domain exceptions to HTTP responses for FastAPI.
"""

from fastapi             import FastAPI, Request
from fastapi.responses   import JSONResponse
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InsufficientFundsError,
    InvalidAllocationError,
    MarketDataError,
    ResourceNotFoundError,
    SellValidationError,
    TradequityError,
    ValidationError,
    WithdrawalValidationError,
)


async def handle_authentication_error(
    request: Request,
    exc: AuthenticationError,
) -> JSONResponse:
    """
    Handle authentication failures.
    """
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
    )


async def handle_authorization_error(
    request: Request,
    exc: AuthorizationError,
) -> JSONResponse:
    """
    Handle authorization failures.
    """
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc)},
    )


async def handle_resource_not_found_error(
    request: Request,
    exc: ResourceNotFoundError,
) -> JSONResponse:
    """
    Handle missing resource failures.
    """
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


async def handle_validation_error(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    """
    Handle business validation failures.
    """
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


async def handle_insufficient_funds_error(
    request: Request,
    exc: InsufficientFundsError,
) -> JSONResponse:
    """
    Handle insufficient balance failures.
    """
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


async def handle_sell_validation_error(
    request: Request,
    exc: SellValidationError,
) -> JSONResponse:
    """
    Handle sell workflow validation failures.
    """
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


async def handle_withdrawal_validation_error(
    request: Request,
    exc: WithdrawalValidationError,
) -> JSONResponse:
    """
    Handle withdrawal workflow validation failures.
    """
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


async def handle_market_data_error(
    request: Request,
    exc: MarketDataError,
) -> JSONResponse:
    """
    Handle market data failures.
    """
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register application exception handlers.

    Args:
        app:
            FastAPI application instance.
    """
    app.add_exception_handler(
        AuthenticationError,
        handle_authentication_error,
    )

    app.add_exception_handler(
        AuthorizationError,
        handle_authorization_error,
    )

    app.add_exception_handler(
        ResourceNotFoundError,
        handle_resource_not_found_error,
    )

    app.add_exception_handler(
        ValidationError,
        handle_validation_error,
    )

    app.add_exception_handler(
        InvalidAllocationError,
        handle_validation_error,
    )

    app.add_exception_handler(
        InsufficientFundsError,
        handle_insufficient_funds_error,
    )

    app.add_exception_handler(
        SellValidationError,
        handle_sell_validation_error,
    )

    app.add_exception_handler(
        WithdrawalValidationError,
        handle_withdrawal_validation_error,
    )

    app.add_exception_handler(
        MarketDataError,
        handle_market_data_error,
    )
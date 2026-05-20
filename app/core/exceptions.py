"""
Application domain exceptions.

This module defines structured exception types used throughout the
Tradequity backend domain and service layers.

Design principles:
    - Explicit domain failures.
    - Clear business semantics.
    - Framework agnostic exception types.
    - Easy mapping to HTTP responses.
"""


class TradequityError(Exception):
    """
    Base application exception.

    All domain-specific exceptions should inherit from this class
    """
    pass

class AuthenticationError(TradequityError):
    """
    Raised when authentication validation fails.
    """
    pass

class AuthorizationError(TradequityError):
    """
    Raised when an authenticated user lacks required permissions.
    """
    pass

class ResourceNotFoundError(TradequityError):
    """
    Raised when a requested domain resource cannot be found.
    """
    pass

class ValidationError(TradequityError):
    """
    Raised when business validation rules fail.
    """
    pass

class InsufficientFundsError(TradequityError):
    """
    Raised when a user lacks sufficient liquid funds for an operation.
    """
    pass

class InvalidAllocationError(TradequityError):
    """
    Raised when allocation inputs violate investment allocation rules.
    """
    pass

class PositionClosedError(TradequityError):
    """
    Raised when an operation targets a closed investment position.
    """
    pass

class SellValidationError(TradequityError):
    """
    Raised when a sell execution violates sell-side constraints.
    """
    pass

class WithdrawalValidationError(TradequityError):
    """
    Raised when a withdrawal request fails business validation
    """
    pass


class MarketDataError(TradequityError):
    """
    Raised when market pricing data cannot be retrieved or validated
    """
    pass

class LedgerIntegrityError(TradequityError):
    """
    Raised when ledger invariants are violated
    """
    pass
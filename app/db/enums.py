"""
Database enum definitions.

This module defines strongly typed Python enum representations for all
native PostgreSQL enums used by the Tradequity persistence layer.

Design principles:
    - Single source of truth for enum definitions.
    - Exact alignment with PostgreSQL enum values.
    - Strong typing across ORM and service layers.
"""

from enum import Enum


class AccountType(str, Enum):
    """
    Supported financial account types.

    User accounts:
        user_cash:
            Liquid funds available to an individual user.

    Platform accounts:
        platform_treasury:
            Platform-held pooled investment capital.

        platform_revenue:
            Platform-earned fees and revenue.
    """

    USER_CASH         = "user_cash"
    PLATFORM_TREASURY = "platform_treasury"
    PLATFORM_REVENUE  = "platform_revenue"


class TransactionReferenceType(str, Enum):
    """
    Supported ledger transaction reference classifications.
    """

    DEPOSIT     = "deposit"
    WITHDRAWAL  = "withdrawal"
    ALLOCATION  = "allocation"
    REALIZATION = "profit_realization"
    FEE         = "performance_fee"
    ADJUSTMENT  = "adjustment"
    PENALTY     = "redemption_penalty"

class AssetType(str, Enum):
    """
    Supported investment asset classifications.
    """

    EQUITY = "equity"
    ETF    = "etf"

class TradeType(str, Enum):
    """
    Supported trade execution directions.
    """

    BUY  = "buy"
    SELL = "sell"

class PositionStatus(str, Enum):
    """
    Master position lifecycle states.
    """
    OPEN   = "open"
    CLOSED = "closed"

"""
SQLAlchemy declarative base definitions.

This module defines the shared declarative base used across all ORM models
in the Tradequity backend.
"""

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Shared SQLAlchemy declarative base class.

    All ORM models must inherit from this class.
    """
    pass

stoxcircle-backend/
│
├── app/
│   ├── api/
│   │   ├── deps/
│   │   │   ├── auth.py
│   │   │   ├── db.py
│   │   │   └── permissions.py
│   │   │
│   │   ├── v1/
│   │   │   ├── admin/
│   │   │   │   ├── trades.py
│   │   │   │   ├── allocations.py
│   │   │   │   ├── withdrawals.py
│   │   │   │   ├── users.py
│   │   │   │   └── market.py
│   │   │   │
│   │   │   ├── user/
│   │   │   │   ├── portfolio.py
│   │   │   │   ├── withdrawals.py
│   │   │   │   └── profile.py
│   │   │   │
│   │   │   └── health.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   └── models/
│   │       ├── profile.py
│   │       ├── account.py
│   │       ├── ledger.py
│   │       ├── trade.py
│   │       ├── position.py
│   │       ├── allocation.py
│   │       ├── realization.py
│   │       ├── market_price.py
│   │       └── withdrawal.py
│   │
│   ├── schemas/
│   │   ├── common/
│   │   │   ├── pagination.py
│   │   │   └── responses.py
│   │   │
│   │   ├── admin/
│   │   │   ├── trade.py
│   │   │   ├── allocation.py
│   │   │   ├── withdrawal.py
│   │   │   └── user.py
│   │   │
│   │   └── user/
│   │       ├── portfolio.py
│   │       ├── withdrawal.py
│   │       └── profile.py
│   │
│   ├── repositories/
│   │   ├── profile_repository.py
│   │   ├── account_repository.py
│   │   ├── ledger_repository.py
│   │   ├── trade_repository.py
│   │   ├── position_repository.py
│   │   ├── allocation_repository.py
│   │   ├── realization_repository.py
│   │   ├── market_repository.py
│   │   └── withdrawal_repository.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── buy_service.py
│   │   ├── sell_service.py
│   │   ├── withdrawal_service.py
│   │   ├── portfolio_service.py
│   │   ├── market_price_service.py
│   │   └── ledger_service.py
│   │
│   ├── workers/
│   │   ├── scheduler.py
│   │   └── market_price_worker.py
│   │
│   ├── utils/
│   │   ├── money.py
│   │   ├── allocation.py
│   │   ├── rounding.py
│   │   └── datetime.py
│   │
│   └── main.py
│
├── migrations/
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── unit/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── utils/
│   │
│   ├── integration/
│   │   ├── api/
│   │   └── workflows/
│   │
│   └── conftest.py
│
├── .env
├── .env.example
├── alembic.ini
├── requirements.txt
├── docker-compose.yml
└── README.md
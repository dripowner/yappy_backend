import uuid
from datetime import datetime
from typing import Any, AsyncGenerator
import enum
from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from pydantic import field_validator
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Float,
    Integer,
    String,
    UUID,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.ext.declarative import declarative_base
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from fastapi_users import schemas

# Base definition
Base = declarative_base()

# Asynchronous DB URL for PostgreSQL
DATABASE_URL = "postgresql+asyncpg://analyze_document:analyze_document@postgres/analyze_document"

engine = create_async_engine(
    DATABASE_URL,
    future=True,
    pool_size=2,
)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

# Enum definitions


class TransactionStatusEnum(enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

# User Model


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"
    balance = Column(Float, default=0)

    __table_args__ = (
        CheckConstraint(
            "balance >= 0", name="check_positive_balance"
        ),  # Check that balance is positive
    )

# Transaction History Model


class TransactionHistory(Base):
    __tablename__ = "transaction_history"

    job_id = Column(UUID, primary_key=True, index=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    req_id = Column(UUID, ForeignKey("shedule_path_requests.id"))
    amount = Column(Integer)
    model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=True)
    result = Column(JSON, nullable=True)
    status = Column(
        Enum(TransactionStatusEnum), default=TransactionStatusEnum.IN_PROGRESS
    )
    err_reason = Column(String(512), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# ML Model


class MLModel(Base):
    __tablename__ = "ml_models"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_name = Column(String(64), unique=True)
    model_cost = Column(Float)

# User schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    balance: float


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass

# Coordinates Model


class Coords(Base):
    __tablename__ = 'coords'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lon_float = Column(Float, nullable=False)
    lat_float = Column(Float, nullable=False)

# Request Model


class ShedulePathRequest(Base):
    __tablename__ = 'shedule_path_requests'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    start_coords_id = Column(
        UUID(as_uuid=True), ForeignKey('coords.id'), nullable=False)
    end_coords_id = Column(
        UUID(as_uuid=True), ForeignKey('coords.id'), nullable=False)
    max_vel = Column(Integer, nullable=False)
    arc = Column(String, nullable=False)
    name = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False)

# User To Request Model


class UsersToRequest(Base):
    __tablename__ = 'users_to_request'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    requests_id = Column(UUID, ForeignKey("shedule_path_requests.id"))


class RequestToTransaction(Base):
    __tablename__ = 'request_to_transaction'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requests_id = Column(UUID, ForeignKey("shedule_path_requests.id"))
    transaction_history_id = Column(
        UUID, ForeignKey("transaction_history.job_id"))


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def add_default_values():
    async for session in get_session():
        models_to_add = [
            MLModel(model_name="docs_model", model_cost=0)
        ]

        for model in models_to_add:
            existing_model = (
                await session.execute(
                    select(MLModel).where(
                        MLModel.model_name == model.model_name)
                )
            ).scalar()

            if not existing_model:
                session.add(model)

        await session.commit()


async def get_session() -> AsyncGenerator[AsyncSession, Any]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_session)):
    yield SQLAlchemyUserDatabase(session, User)

# Tables
# User Table
# | Column    | Type                  | Default | Constraint                      |
# |-----------|-----------------------|---------|---------------------------------|
# | id        | UUID                  | None    | Primary Key                     |
# | email     | String                | None    | Unique, Not Null                |
# | hashed_password | String          | None    | Not Null                        |
# | is_active | Boolean               | True    |                                 |
# | is_superuser | Boolean            | False   |                                 |
# | balance   | Float                 | 0       | Check: balance >= 0             |

# TransactionHistory Table
# | Column        | Type                          | Default       | Constraint              |
# |---------------|-------------------------------|---------------|-------------------------|
# | job_id        | UUID                          | None          | Primary Key, Indexed    |
# | user_id       | UUID                          | None          | Foreign Key (users.id)  |
# | amount        | Integer                       | None          |                         |
# | model_id      | Integer                       | None          | Foreign Key (ml_models.id), Nullable |
# | result        | JSON                          | None          | Nullable                |
# | status        | Enum (TransactionStatusEnum)  | IN_PROGRESS   |                         |
# | err_reason    | String(512)                   | None          | Nullable                |
# | timestamp     | DateTime (timezone=True)      | func.now()    | Server Default          |

# MLModel Table
# | Column      | Type         | Default | Constraint      |
# |-------------|--------------|---------|-----------------|
# | id          | Integer      | None    | Primary Key, Indexed, Autoincrement |
# | model_name  | String(64)   | None    | Unique          |
# | model_cost  | Float        | None    |                 |

# ShedulePathRequest Table
# | Column           | Type                     | Default     | Constraint                 |
# |------------------|--------------------------|-------------|----------------------------|
# | id               | UUID                     | uuid.uuid4  | Primary Key                |
# | start_coords_id  | UUID                     | None        | Foreign Key (coords.id)    |
# | end_coords_id    | UUID                     | None        | Foreign Key (coords.id)    |
# | max_vel          | Integer                  | None        | Not Null                   |
# | arc              | String                   | None        | Not Null                   |
# | name             | String                   | None        | Not Null                   |
# | date             | DateTime                 | None        | Not Null                   |

# Coords Table
# | Column           | Type                     | Default     | Constraint                 |
# |------------------|--------------------------|-------------|----------------------------|
# | id               | UUID                     | uuid.uuid4  | Primary Key                |
# | lon_float        | Float                    | None        | Not Null                   |
# | lat_float        | Float                    | None        | Not Null                   |

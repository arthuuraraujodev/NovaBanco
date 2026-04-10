from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class AccountType(str, enum.Enum):
    corrente = "corrente"
    poupanca = "poupanca"

class TransactionType(str, enum.Enum):
    credito = "credito"
    debito  = "debito"

class PaymentStatus(str, enum.Enum):
    pendente   = "pendente"
    confirmado = "confirmado"
    cancelado  = "cancelado"

class TransferModalidade(str, enum.Enum):
    TED = "TED"
    DOC = "DOC"

class PixKeyType(str, enum.Enum):
    cpf       = "cpf"
    email     = "email"
    telefone  = "telefone"
    aleatoria = "aleatoria"

class LoanType(str, enum.Enum):
    pessoal    = "pessoal"
    consignado = "consignado"
    auto       = "auto"

class LoanStatus(str, enum.Enum):
    em_analise = "em_analise"
    aprovado   = "aprovado"
    reprovado  = "reprovado"
    quitado    = "quitado"


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    nome            = Column(String(80),  nullable=False)
    sobrenome       = Column(String(80),  nullable=False)
    cpf             = Column(String(14),  unique=True, nullable=False, index=True)
    email           = Column(String(120), unique=True, nullable=False, index=True)
    telefone        = Column(String(20),  nullable=True)
    data_nascimento = Column(String(10),  nullable=True)
    hashed_password = Column(String(128), nullable=False)
    ativo           = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("Account", back_populates="user", uselist=False)


class Account(Base):
    __tablename__ = "accounts"

    id      = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    agencia = Column(String(10), default="0001")
    numero  = Column(String(20), nullable=False, unique=True)
    tipo    = Column(Enum(AccountType), default=AccountType.corrente)
    saldo   = Column(Float, default=0.0)

    user         = relationship("User", back_populates="account")
    transactions = relationship("Transaction", back_populates="account")
    payments     = relationship("Payment",     back_populates="account")
    transfers    = relationship("Transfer",    back_populates="account")
    pix_keys     = relationship("PixKey",      back_populates="account")
    pix_sent     = relationship("PixTransaction", back_populates="account")
    loans        = relationship("Loan",        back_populates="account")


class Transaction(Base):
    """Registro geral de todas as movimentações da conta."""
    __tablename__ = "transactions"

    id         = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    tipo       = Column(Enum(TransactionType), nullable=False)
    valor      = Column(Float, nullable=False)
    descricao  = Column(String(200), nullable=True)
    categoria  = Column(String(50),  nullable=True)   # pix, ted, boleto, emprestimo...
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("Account", back_populates="transactions")


class Payment(Base):
    __tablename__ = "payments"

    id             = Column(Integer, primary_key=True, index=True)
    account_id     = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    tipo           = Column(String(30), nullable=False)   # boleto, conta, cartao, tributo
    codigo_barras  = Column(String(60), nullable=False)
    valor          = Column(Float,      nullable=False)
    data_pagamento = Column(String(10), nullable=False)
    descricao      = Column(String(200), nullable=True)
    status         = Column(Enum(PaymentStatus), default=PaymentStatus.confirmado)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("Account", back_populates="payments")


class Transfer(Base):
    __tablename__ = "transfers"

    id              = Column(Integer, primary_key=True, index=True)
    account_id      = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    banco           = Column(String(80),  nullable=False)
    agencia         = Column(String(10),  nullable=False)
    conta           = Column(String(20),  nullable=False)
    tipo_conta      = Column(String(20),  nullable=False)   # corrente | poupanca
    cpf_favorecido  = Column(String(14),  nullable=True)
    nome_favorecido = Column(String(120), nullable=False)
    valor           = Column(Float,       nullable=False)
    modalidade      = Column(Enum(TransferModalidade), default=TransferModalidade.TED)
    mensagem        = Column(String(200), nullable=True)
    status          = Column(Enum(PaymentStatus), default=PaymentStatus.confirmado)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("Account", back_populates="transfers")


class PixKey(Base):
    __tablename__ = "pix_keys"

    id         = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    tipo       = Column(Enum(PixKeyType), nullable=False)
    chave      = Column(String(200), nullable=False, unique=True)
    ativo      = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("Account", back_populates="pix_keys")


class PixTransaction(Base):
    __tablename__ = "pix_transactions"

    id         = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    chave_tipo = Column(String(20),  nullable=False)
    chave      = Column(String(200), nullable=False)
    valor      = Column(Float,       nullable=False)
    mensagem   = Column(String(200), nullable=True)
    status     = Column(Enum(PaymentStatus), default=PaymentStatus.confirmado)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("Account", back_populates="pix_sent")


class Loan(Base):
    __tablename__ = "loans"

    id          = Column(Integer, primary_key=True, index=True)
    account_id  = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    tipo        = Column(Enum(LoanType), nullable=False)
    valor       = Column(Float,      nullable=False)
    parcelas    = Column(Integer,    nullable=False)
    taxa_mensal = Column(Float,      nullable=False)   # ex: 0.0149
    valor_parcela = Column(Float,    nullable=False)
    valor_total = Column(Float,      nullable=False)
    finalidade  = Column(String(80), nullable=True)
    status      = Column(Enum(LoanStatus), default=LoanStatus.em_analise)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("Account", back_populates="loans")

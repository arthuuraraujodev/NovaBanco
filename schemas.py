from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from models import (
    AccountType, TransactionType, PaymentStatus,
    TransferModalidade, PixKeyType, LoanType, LoanStatus
)


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────

class RegisterRequest(BaseModel):
    nome:            str
    sobrenome:       str
    cpf:             str
    email:           EmailStr
    telefone:        Optional[str] = None
    data_nascimento: Optional[str] = None
    password:        str

    @field_validator("cpf")
    @classmethod
    def cpf_valido(cls, v):
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) != 11:
            raise ValueError("CPF deve conter 11 dígitos")
        return v

    @field_validator("password")
    @classmethod
    def senha_minima(cls, v):
        if len(v) < 8:
            raise ValueError("Senha deve ter no mínimo 8 caracteres")
        return v


class LoginRequest(BaseModel):
    login:    str   # CPF ou e-mail
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"


# ─────────────────────────────────────────────
# User / Account
# ─────────────────────────────────────────────

class UserOut(BaseModel):
    id:              int
    nome:            str
    sobrenome:       str
    cpf:             str
    email:           str
    telefone:        Optional[str]
    data_nascimento: Optional[str]
    created_at:      datetime

    model_config = {"from_attributes": True}


class AccountOut(BaseModel):
    id:      int
    agencia: str
    numero:  str
    tipo:    AccountType
    saldo:   float
    user:    UserOut

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# Transactions
# ─────────────────────────────────────────────

class TransactionOut(BaseModel):
    id:         int
    tipo:       TransactionType
    valor:      float
    descricao:  Optional[str]
    categoria:  Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# Payments
# ─────────────────────────────────────────────

class PaymentRequest(BaseModel):
    tipo:           str
    codigo_barras:  str
    valor:          float
    data_pagamento: str
    descricao:      Optional[str] = None

    @field_validator("valor")
    @classmethod
    def valor_positivo(cls, v):
        if v <= 0:
            raise ValueError("Valor deve ser maior que zero")
        return v


class PaymentOut(BaseModel):
    id:             int
    tipo:           str
    codigo_barras:  str
    valor:          float
    data_pagamento: str
    descricao:      Optional[str]
    status:         PaymentStatus
    created_at:     datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# Transfers
# ─────────────────────────────────────────────

class TransferRequest(BaseModel):
    banco:           str
    agencia:         str
    conta:           str
    tipo_conta:      str
    cpf_favorecido:  Optional[str] = None
    nome_favorecido: str
    valor:           float
    modalidade:      TransferModalidade = TransferModalidade.TED
    mensagem:        Optional[str] = None

    @field_validator("valor")
    @classmethod
    def valor_positivo(cls, v):
        if v <= 0:
            raise ValueError("Valor deve ser maior que zero")
        return v


class TransferOut(BaseModel):
    id:              int
    banco:           str
    agencia:         str
    conta:           str
    nome_favorecido: str
    valor:           float
    modalidade:      TransferModalidade
    status:          PaymentStatus
    created_at:      datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# Pix
# ─────────────────────────────────────────────

class PixKeyOut(BaseModel):
    id:    int
    tipo:  PixKeyType
    chave: str
    ativo: bool

    model_config = {"from_attributes": True}


class PixSendRequest(BaseModel):
    chave_tipo: str
    chave:      str
    valor:      float
    mensagem:   Optional[str] = None

    @field_validator("valor")
    @classmethod
    def valor_positivo(cls, v):
        if v <= 0:
            raise ValueError("Valor deve ser maior que zero")
        return v


class PixTransactionOut(BaseModel):
    id:         int
    chave_tipo: str
    chave:      str
    valor:      float
    mensagem:   Optional[str]
    status:     PaymentStatus
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# Loans
# ─────────────────────────────────────────────

class LoanRequest(BaseModel):
    tipo:       LoanType
    valor:      float
    parcelas:   int
    finalidade: Optional[str] = None

    @field_validator("valor")
    @classmethod
    def valor_valido(cls, v):
        if v < 500 or v > 50000:
            raise ValueError("Valor deve estar entre R$500 e R$50.000")
        return v

    @field_validator("parcelas")
    @classmethod
    def parcelas_validas(cls, v):
        if v not in [12, 24, 36, 48, 60]:
            raise ValueError("Parcelas: 12, 24, 36, 48 ou 60")
        return v


class LoanOut(BaseModel):
    id:            int
    tipo:          LoanType
    valor:         float
    parcelas:      int
    taxa_mensal:   float
    valor_parcela: float
    valor_total:   float
    finalidade:    Optional[str]
    status:        LoanStatus
    created_at:    datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# Respostas genéricas
# ─────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    detail:  Optional[str] = None

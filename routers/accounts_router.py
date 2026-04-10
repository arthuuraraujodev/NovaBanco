from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_account
import models
import schemas

router = APIRouter(prefix="/accounts", tags=["Conta"])


@router.get("/me", response_model=schemas.AccountOut)
def get_my_account(account: models.Account = Depends(get_current_account)):
    """Retorna dados completos da conta + saldo do usuário autenticado."""
    return account


@router.get("/transactions", response_model=List[schemas.TransactionOut])
def get_transactions(
    limit:   int = Query(default=20, le=100),
    offset:  int = Query(default=0,  ge=0),
    account: models.Account = Depends(get_current_account),
    db:      Session = Depends(get_db),
):
    """Retorna histórico de movimentações da conta (mais recentes primeiro)."""
    txns = (
        db.query(models.Transaction)
        .filter(models.Transaction.account_id == account.id)
        .order_by(models.Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return txns


@router.get("/summary")
def get_summary(
    account: models.Account = Depends(get_current_account),
    db:      Session = Depends(get_db),
):
    """Retorna resumo financeiro: entradas, saídas e saldo do mês."""
    from sqlalchemy import func, extract
    from datetime import datetime

    mes_atual = datetime.utcnow().month
    ano_atual = datetime.utcnow().year

    entradas = (
        db.query(func.sum(models.Transaction.valor))
        .filter(
            models.Transaction.account_id == account.id,
            models.Transaction.tipo == models.TransactionType.credito,
            extract("month", models.Transaction.created_at) == mes_atual,
            extract("year",  models.Transaction.created_at) == ano_atual,
        )
        .scalar() or 0.0
    )

    saidas = (
        db.query(func.sum(models.Transaction.valor))
        .filter(
            models.Transaction.account_id == account.id,
            models.Transaction.tipo == models.TransactionType.debito,
            extract("month", models.Transaction.created_at) == mes_atual,
            extract("year",  models.Transaction.created_at) == ano_atual,
        )
        .scalar() or 0.0
    )

    return {
        "saldo":    round(account.saldo, 2),
        "entradas": round(entradas, 2),
        "saidas":   round(saidas, 2),
        "mes":      mes_atual,
        "ano":      ano_atual,
    }
from schemas import MessageResponse

@router.post("/balance")
def adjust_balance(
    payload: dict,
    account: models.Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Ajusta o saldo da conta (apenas para testes)."""
    valor = float(payload.get("valor", 0))
    operacao = payload.get("operacao", "adicionar")

    if operacao == "adicionar":
        account.saldo = round(account.saldo + valor, 2)
        db.add(models.Transaction(
            account_id=account.id,
            tipo=models.TransactionType.credito,
            valor=valor,
            descricao="Ajuste manual de saldo",
            categoria="bonus",
        ))
    elif operacao == "subtrair":
        if account.saldo < valor:
            raise HTTPException(status_code=422, detail="Saldo insuficiente")
        account.saldo = round(account.saldo - valor, 2)
        db.add(models.Transaction(
            account_id=account.id,
            tipo=models.TransactionType.debito,
            valor=valor,
            descricao="Ajuste manual de saldo",
            categoria="bonus",
        ))
    else:
        raise HTTPException(status_code=400, detail="Operação inválida")

    db.commit()
    db.refresh(account)
    return { "saldo": account.saldo, "operacao": operacao, "valor": valor }

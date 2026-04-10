from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_account
import models
import schemas

router = APIRouter(prefix="/loans", tags=["Empréstimos"])

# Taxas mensais por tipo
TAXAS = {
    models.LoanType.pessoal:    0.0149,
    models.LoanType.consignado: 0.0089,
    models.LoanType.auto:       0.0119,
}


def calcular_parcela_price(valor: float, taxa: float, n: int) -> float:
    """
    Fórmula Price (Sistema Francês de Amortização):
    PMT = PV * [r(1+r)^n] / [(1+r)^n - 1]
    """
    fator = (1 + taxa) ** n
    return round(valor * (taxa * fator) / (fator - 1), 2)


@router.post("", response_model=schemas.LoanOut, status_code=status.HTTP_201_CREATED)
def request_loan(
    payload: schemas.LoanRequest,
    account: models.Account = Depends(get_current_account),
    db:      Session = Depends(get_db),
):
    """
    Solicita um empréstimo.
    Calcula a parcela pela Tabela Price e inicia a análise de crédito.
    Ao ser aprovado, o valor é creditado na conta (status em_analise → aprovado).
    Para fins de demo, aprovamos automaticamente.
    """
    taxa = TAXAS[payload.tipo]
    valor_parcela = calcular_parcela_price(payload.valor, taxa, payload.parcelas)
    valor_total   = round(valor_parcela * payload.parcelas, 2)

    loan = models.Loan(
        account_id=account.id,
        tipo=payload.tipo,
        valor=payload.valor,
        parcelas=payload.parcelas,
        taxa_mensal=taxa,
        valor_parcela=valor_parcela,
        valor_total=valor_total,
        finalidade=payload.finalidade,
        status=models.LoanStatus.aprovado,   # auto-aprovação na demo
    )
    db.add(loan)
    db.flush()

    # Crédito automático do valor solicitado (demo)
    account.saldo = round(account.saldo + payload.valor, 2)

    db.add(models.Transaction(
        account_id=account.id,
        tipo=models.TransactionType.credito,
        valor=payload.valor,
        descricao=f"Empréstimo {payload.tipo.value} aprovado — {payload.parcelas}x",
        categoria="emprestimo",
    ))

    db.commit()
    db.refresh(loan)
    return loan


@router.get("", response_model=List[schemas.LoanOut])
def list_loans(
    account: models.Account = Depends(get_current_account),
    db:      Session = Depends(get_db),
):
    """Lista todos os empréstimos do usuário."""
    return (
        db.query(models.Loan)
        .filter(models.Loan.account_id == account.id)
        .order_by(models.Loan.created_at.desc())
        .all()
    )


@router.get("/simulate")
def simulate_loan(
    tipo:     str   = "pessoal",
    valor:    float = 5000.0,
    parcelas: int   = 24,
):
    """
    Simula parcelas sem autenticação.
    Útil para exibir o preview no frontend antes do login.
    """
    try:
        loan_type = models.LoanType(tipo)
    except ValueError:
        raise HTTPException(status_code=400, detail="Tipo inválido. Use: pessoal, consignado ou auto")

    if parcelas not in [12, 24, 36, 48, 60]:
        raise HTTPException(status_code=400, detail="Parcelas: 12, 24, 36, 48 ou 60")

    taxa = TAXAS[loan_type]
    parcela = calcular_parcela_price(valor, taxa, parcelas)
    return {
        "tipo":          tipo,
        "valor":         valor,
        "parcelas":      parcelas,
        "taxa_mensal":   taxa,
        "valor_parcela": parcela,
        "valor_total":   round(parcela * parcelas, 2),
    }


@router.get("/{loan_id}", response_model=schemas.LoanOut)
def get_loan(
    loan_id: int,
    account: models.Account = Depends(get_current_account),
    db:      Session = Depends(get_db),
):
    """Detalha um empréstimo específico."""
    loan = db.query(models.Loan).filter(
        models.Loan.id == loan_id,
        models.Loan.account_id == account.id,
    ).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    return loan

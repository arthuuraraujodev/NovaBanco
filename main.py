from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from database import engine, Base
import models  # noqa: F401 — garante que os models são registrados antes do create_all

from routers.auth_router      import router as auth_router
from routers.accounts_router  import router as accounts_router
from routers.payments_router  import router as payments_router
from routers.transfers_router import router as transfers_router
from routers.pix_router       import router as pix_router
from routers.loans_router     import router as loans_router

# ─────────────────────────────────────────────
# Criação das tabelas no SQLite
# ─────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────
# Aplicação FastAPI
# ─────────────────────────────────────────────
app = FastAPI(
    title="NovaBanco API",
    description="Back-end completo do sistema bancário NovaBanco",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─────────────────────────────────────────────
# CORS — permite chamadas do front-end
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # em produção, restrinja ao domínio do front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(payments_router)
app.include_router(transfers_router)
app.include_router(pix_router)
app.include_router(loans_router)

# ─────────────────────────────────────────────
# Serve o front-end estático (opcional)
# ─────────────────────────────────────────────
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse("static/index.html")


# ─────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────
@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok", "service": "NovaBanco API v1.0"}


# ─────────────────────────────────────────────
# Execução direta
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

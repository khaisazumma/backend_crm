from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import connect_db, disconnect_db
from app.routers import auth, cart, commissions, customers, invoices, products


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()


app = FastAPI(
    title="Venambak CRM API",
    description="Backend CRM Venambak — customers, products, invoices, cart, commissions.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(invoices.router)
app.include_router(commissions.router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

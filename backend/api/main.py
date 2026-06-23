from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import portfolio, risk
import uvicorn

app = FastAPI(
    title="Multi-Asset Portfolio Stress Tester & Scenario Engine API",
    description="Backend risk engine for calculating portfolio VaR/CVaR, historical crisis replay, factor shocks, and generating risk reports.",
    version="1.0.0"
)

# Configure CORS for frontend access (Vercel deployment + localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local & deployed testing. Can narrow in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(portfolio.router)
app.include_router(risk.router)

@app.get("/")
@app.get("/health")
def health_check():
    """
    Simple health check endpoint returning server status.
    """
    from risk_engine.report import WEASYPRINT_AVAILABLE
    return {
        "status": "healthy",
        "service": "portfolio-stress-tester-api",
        "weasyprint_installed": WEASYPRINT_AVAILABLE
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

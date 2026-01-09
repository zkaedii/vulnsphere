"""
VulnSphere PRIME - Main Application Entry Point
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
from typing import Dict, List
import logging

from backend.core.zkaedi_prime import ZKAEDIPrimeFractalEngine
from backend.suppression.mdm_engine import MirageDelayMirage
from backend.suppression.zero_trust_moat import ZeroTrustMoat
from backend.api.routes import router
from backend.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="VulnSphere PRIME API",
    description="Fractal Security Intelligence Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class VulnSphereState:
    def __init__(self):
        self.zkaedi_engine = ZKAEDIPrimeFractalEngine(
            alpha=settings.FRACTAL_ALPHA,
            eta=settings.ETA,
            gamma=settings.GAMMA,
            beta=settings.BETA,
            sigma=settings.SIGMA,
            phi=settings.PHI
        )
        self.mdm_engine = MirageDelayMirage()
        self.zero_trust = ZeroTrustMoat()
        self.active_scans: Dict[str, asyncio.Task] = {}
        self.websocket_connections: List[WebSocket] = []

state = VulnSphereState()

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "VulnSphere PRIME",
        "version": "1.0.0",
        "status": "operational",
        "engine": "ZKAEDI PRIME",
        "fractal_order": state.zkaedi_engine.alpha
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_scans": len(state.active_scans),
        "websocket_connections": len(state.websocket_connections)
    }

@app.post("/api/v1/scan/network")
async def scan_network(network_config: Dict):
    """
    Initiate network vulnerability scan with ZKAEDI PRIME
    """
    try:
        logger.info(f"Starting ZKAEDI PRIME scan for {len(network_config)} nodes")
        
        result = await state.zkaedi_engine.solve_vuln_detection_fdde(
            network_graph=network_config,
            max_iterations=50000
        )
        
        return {
            "status": "success",
            "scan_id": result.get("scan_id"),
            "converged": result.get("converged"),
            "iterations": result.get("iterations"),
            "phase": result.get("stability_log", [{}])[-1].get("phase", "unknown") if result.get("stability_log") else "unknown",
            "vulnerabilities_detected": len(result.get("vulnerabilities", []))
        }
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates
    """
    await websocket.accept()
    state.websocket_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "subscribe_scan":
                scan_id = data.get("scan_id")
                # Send updates for this scan
                
            elif data.get("type") == "mdm_suppression":
                probe = data.get("probe")
                result = await state.mdm_engine.process_probe_with_mdm(probe, 0)
                await websocket.send_json(result)
                
    except WebSocketDisconnect:
        state.websocket_connections.remove(websocket)
        logger.info("WebSocket disconnected")

@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("🔱 VulnSphere PRIME starting up...")
    logger.info(f"   Fractal order (α): {state.zkaedi_engine.alpha}")
    logger.info(f"   Golden ratio (φ): {state.zkaedi_engine.phi}")
    logger.info("   Energy field: ACTIVE")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("VulnSphere PRIME shutting down...")
    
    # Cancel active scans
    for scan_id, task in state.active_scans.items():
        task.cancel()
    
    # Close websocket connections
    for ws in state.websocket_connections:
        await ws.close()

def cli():
    """CLI entry point"""
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

if __name__ == "__main__":
    cli()

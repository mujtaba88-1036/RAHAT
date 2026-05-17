from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from services.gemini_services import run_full_pipeline
from services.news_scanner import scan_latest_crises

# Global State Tracking
SYSTEM_STATE = {
    "last_scan_timestamp": None,
    "active_crises_count": 0
}

pipeline_running = False

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RAHAT Agentic Backend",
    description="FastAPI backend for RAHAT crisis response pipeline.",
    version="1.0.0"
)

# Enable CORS for Flutter Web testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    inputs: List[Dict[str, Any]]
    mode: str = "manual"

@app.get("/health", tags=["System"])
async def health_check():
    """Returns the health status of the API."""
    return {"status": "ok", "service": "RAHAT Backend Pipeline"}

@app.post("/analyze", tags=["Pipeline"])
async def analyze_pipeline(request: AnalyzeRequest):
    """
    Runs the full analysis pipeline sequentially using Gemini API:
    1. Signal Collection
    2. Crisis Detection
    3. Response Planning
    4. Action Execution
    """
    global pipeline_running
    if pipeline_running:
        raise HTTPException(status_code=429, detail="Pipeline already running. Please wait for current scan to complete.")
    
    pipeline_running = True
    try:
        result = await run_full_pipeline(request.inputs)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")
    finally:
        pipeline_running = False

@app.post("/auto-scan", tags=["System"])
async def trigger_auto_scan():
    """
    Scans configured RSS news feeds for local crisis signals.
    Automatically triggers the full analysis pipeline if matches are found.
    """
    global pipeline_running
    if pipeline_running:
        raise HTTPException(status_code=429, detail="Pipeline already running. Please wait for current scan to complete.")
        
    pipeline_running = True
    try:
        scan_results = await scan_latest_crises()
        SYSTEM_STATE["last_scan_timestamp"] = datetime.now().isoformat()
        
        signals = scan_results.get("signals", [])
        
        if len(signals) > 0:
            pipeline_result = await run_full_pipeline(signals)
            
            # Check if a crisis was actually detected
            crisis_event = pipeline_result.get("pipeline_results", {}).get("crisis_detector", {}).get("crisis_event", {})
            severity = crisis_event.get("severity")
            if severity and severity.upper() in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                SYSTEM_STATE["active_crises_count"] += 1
                
            return {
                "status": "crisis_detected_and_processed",
                "scan_summary": scan_results,
                "pipeline_result": pipeline_result
            }
        else:
            return {
                "status": "no_crisis_found",
                "scan_summary": scan_results
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-scan failed: {str(e)}")
    finally:
        pipeline_running = False

@app.get("/status", tags=["System"])
async def get_system_status():
    """Returns the current system state."""
    return {
        "last_scan_timestamp": SYSTEM_STATE["last_scan_timestamp"],
        "active_crises": SYSTEM_STATE["active_crises_count"],
        "system_health": "operational"
    }

@app.get("/pipeline-status", tags=["System"])
async def get_pipeline_status():
    """Returns the current running status of the pipeline."""
    global pipeline_running
    return {
        "is_running": pipeline_running,
        "model": "gemini-1.5-flash"
    }

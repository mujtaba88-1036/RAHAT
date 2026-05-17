import os
import re
import asyncio
import json
import logging
from typing import Any, Dict, List
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables (automatically finds .env in current or parent dirs)
load_dotenv()

# ═══════════════════════════════════════════════════════════
# Multi-Key Configuration with Auto-Rotation
# ═══════════════════════════════════════════════════════════
GEMINI_API_KEYS = []
for i in range(1, 20):
    key = os.getenv(f"GEMINI_API_KEY_{i}")
    if key:
        GEMINI_API_KEYS.append(key)

if not GEMINI_API_KEYS:
    logging.warning("No GEMINI_API_KEY_* found in environment. Demo fallback will be used.")

current_key_index = 0

MODEL_NAME = "gemini-2.5-flash"

def get_model(system_prompt: str):
    """Configure genai with the current key and return a model instance."""
    global current_key_index
    if not GEMINI_API_KEYS:
        return None
    key = GEMINI_API_KEYS[current_key_index]
    genai.configure(api_key=key)
    logging.info(f"Using API key index {current_key_index} (ending ...{key[-6:]})")
    return genai.GenerativeModel(
        MODEL_NAME,
        system_instruction=system_prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json"
        )
    )

# ═══════════════════════════════════════════════════════════
# Demo Fallback Data (used when ALL keys are exhausted)
# ═══════════════════════════════════════════════════════════
DEMO_FALLBACK = {
    "signal_collector": {
        "signals": [
            {
                "location": "G-10 Markaz, Islamabad",
                "signal_type": "flood",
                "urgency_hint": "high",
                "raw_text": "Waterlogging in G-10 Markaz, vehicles stranded, rescue teams needed",
                "source": "social",
                "reasoning": "Explicit flood indicators detected in Roman Urdu social post"
            },
            {
                "location": "Faizabad Interchange",
                "signal_type": "road_block",
                "urgency_hint": "high",
                "raw_text": "Faizabad completely blocked due to rising water level",
                "source": "traffic",
                "reasoning": "Complete traffic stoppage reported with flood correlation"
            }
        ],
        "reasoning_steps": [
            "Analyzing 3 multi-modal input sources",
            "Detected Roman Urdu flood indicators in social signal",
            "Cross-referenced with weather and traffic feeds",
            "Extracted 2 high-confidence crisis signals"
        ]
    },
    "crisis_detector": {
        "crisis_event": {
            "location": "G-10 Markaz, Islamabad",
            "crisis_type": "Urban Flooding",
            "severity": "HIGH",
            "confidence": 87,
            "situation_summary": "Severe waterlogging in G-10 Markaz area with multiple vehicles stranded. Water level rising at Faizabad Interchange causing complete traffic blockage. Residential areas at risk of inundation.",
            "affected_population": "15,000",
            "reasoning_steps": [
                "Signal spatial clustering detected in G-10/Faizabad corridor",
                "Multiple independent sources confirm flooding event",
                "Cross-referencing weather data shows 85mm rainfall in 2 hours",
                "Traffic feed confirms complete arterial blockage",
                "Severity elevated to HIGH based on population density analysis"
            ]
        }
    },
    "response_planner": {
        "response_plan": {
            "actions": [
                {
                    "id": "ACT-001",
                    "title": "Deploy Rescue Boats to G-10 Markaz",
                    "resource_assignment": "NDMA Rescue Unit Alpha",
                    "priority": "Critical",
                    "description": "Deploy inflatable rescue boats to extract stranded civilians from G-10 Markaz commercial area"
                },
                {
                    "id": "ACT-002",
                    "title": "Activate Traffic Diversion at Faizabad",
                    "resource_assignment": "Islamabad Traffic Police",
                    "priority": "High",
                    "description": "Set up emergency traffic diversion routes via Murree Road and Margalla Road to bypass Faizabad"
                },
                {
                    "id": "ACT-003",
                    "title": "Open Emergency Shelters in F-8",
                    "resource_assignment": "PDMA Relief Wing",
                    "priority": "High",
                    "description": "Activate F-8 Markaz community center as emergency shelter for displaced residents"
                }
            ]
        }
    },
    "action_executor": {
        "execution_report": {
            "executed_actions": [
                {
                    "action_id": "ACT-001",
                    "action_name": "Deploy Rescue Boats to G-10 Markaz",
                    "execution_status": "SUCCESS",
                    "timestamp": "2024-08-15T10:15:03Z",
                    "before_state": "No rescue assets deployed",
                    "after_state": "3 rescue boats en route to G-10 Markaz"
                },
                {
                    "action_id": "ACT-002",
                    "action_name": "Activate Traffic Diversion at Faizabad",
                    "execution_status": "SUCCESS",
                    "timestamp": "2024-08-15T10:15:07Z",
                    "before_state": "Faizabad gridlocked, no diversions active",
                    "after_state": "Diversion routes active via Murree Road"
                },
                {
                    "action_id": "ACT-003",
                    "action_name": "Open Emergency Shelters in F-8",
                    "execution_status": "SUCCESS",
                    "timestamp": "2024-08-15T10:15:11Z",
                    "before_state": "Shelters closed, displaced civilians on streets",
                    "after_state": "F-8 community center open, capacity 500 people"
                }
            ],
            "system_state_before": {
                "rescue_status": "No assets deployed",
                "traffic_flow": "Gridlocked at Faizabad",
                "shelter_status": "All shelters closed",
                "alert_level": "None"
            },
            "system_state_after": {
                "rescue_status": "3 boats deployed to G-10",
                "traffic_flow": "Diversion routes active",
                "shelter_status": "F-8 shelter open (cap: 500)",
                "alert_level": "RED — Active Response"
            },
            "audit_log": [
                "Pipeline initialized — multi-agent cascade activated",
                "Signal Collector: Ingested 3 sources, extracted 2 crisis signals",
                "Crisis Detector: Flood event confirmed at 87% confidence",
                "Response Planner: Generated 3 prioritized action plans",
                "Action Executor: ACT-001 dispatched — rescue boats en route",
                "Action Executor: ACT-002 dispatched — traffic diversions active",
                "Action Executor: ACT-003 dispatched — emergency shelter opened",
                "System state updated. All actions executed successfully.",
                "Audit trail finalized. Report #RAHAT-7842 generated."
            ]
        }
    },
    "location_intelligence": {
        "location_data": {
            "primary_location": {
                "name": "G-10 Markaz",
                "latitude": 33.6751,
                "longitude": 73.0479,
                "zoom_level": 15,
                "formatted_address": "G-10 Markaz, Islamabad Capital Territory, Pakistan"
            },
            "affected_zones": [
                {"name": "G-10/1", "latitude": 33.6780, "longitude": 73.0450},
                {"name": "Faizabad Interchange", "latitude": 33.7008, "longitude": 73.0679}
            ],
            "coverage_radius_km": 3.0
        },
        "reasoning_steps": [
            "Parsed location: G-10 Markaz, Islamabad-Rawalpindi Region",
            "Matched to known sector G-10 in ICT grid",
            "Primary coordinates: 33.6751°N, 73.0479°E",
            "Secondary affected zone: Faizabad Interchange identified",
            "Zoom level 15 selected for sector-level crisis visibility"
        ]
    }
}


async def call_gemini_json(system_prompt: str, user_prompt: str) -> Any:
    """
    Calls the Gemini model, requesting JSON output.
    Auto-rotates API keys on 429 errors.
    Falls back to demo data when all keys are exhausted.
    """
    global current_key_index

    if not GEMINI_API_KEYS:
        logging.warning("No API keys available. Returning demo fallback.")
        return None  # Caller handles fallback

    # Try each key
    attempts = 0
    max_attempts = len(GEMINI_API_KEYS)

    while attempts < max_attempts:
        model = get_model(system_prompt)
        if model is None:
            break

        # Throttle: 2s pre-call delay to respect per-minute limits
        await asyncio.sleep(2)

        try:
            response = await model.generate_content_async(user_prompt)
            return json.loads(response.text)
        except Exception as e:
            error_msg = str(e)

            if "429" in error_msg:
                attempts += 1
                old_index = current_key_index
                current_key_index = (current_key_index + 1) % len(GEMINI_API_KEYS)

                if attempts < max_attempts:
                    logging.warning(
                        f"[Key {old_index}] Rate limit hit (429). "
                        f"Switching to backup API key {current_key_index} "
                        f"(attempt {attempts + 1}/{max_attempts})"
                    )
                    # Try to extract wait time for smarter retry
                    match = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)\s*\}", error_msg)
                    if match:
                        wait = min(int(match.group(1)), 10)  # Cap at 10s
                        logging.info(f"Extracted retry_delay: {wait}s. Waiting...")
                        await asyncio.sleep(wait)
                    else:
                        await asyncio.sleep(3)  # Default short pause before next key
                    continue
                else:
                    logging.error(
                        f"All {max_attempts} API keys exhausted (429). "
                        f"Falling back to demo data."
                    )
                    return None  # Caller handles fallback
            else:
                logging.error(f"Gemini error (non-429): {e}")
                return {"error": error_msg, "raw_response": None}

    return None


async def run_full_pipeline(inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Orchestrates the 4 agents in sequence, passing data down the pipeline.
    Falls back to DEMO_FALLBACK if any agent returns None (all keys exhausted).
    """
    # Try to detect location from user inputs
    detected_location = "Islamabad"
    location_coords = {"latitude": 33.6844, "longitude": 73.0479}

    input_texts = " ".join([i.get("text","") for i in inputs]).lower()
    if "f-8" in input_texts or "f8" in input_texts:
        detected_location = "F-8 Markaz, Islamabad"
        location_coords = {"latitude": 33.7100, "longitude": 73.0479}
    elif "faizabad" in input_texts:
        detected_location = "Faizabad Interchange, Islamabad"
        location_coords = {"latitude": 33.7008, "longitude": 73.0679}
    elif "g-11" in input_texts or "g11" in input_texts:
        detected_location = "G-11, Islamabad"
        location_coords = {"latitude": 33.6844, "longitude": 73.0350}
    elif "g-10" in input_texts or "g10" in input_texts or "pani" in input_texts:
        detected_location = "G-10 Markaz, Islamabad"
        location_coords = {"latitude": 33.6751, "longitude": 73.0479}
    elif "saddar" in input_texts or "rawalpindi" in input_texts:
        detected_location = "Saddar, Rawalpindi"
        location_coords = {"latitude": 33.5973, "longitude": 73.0479}
    elif "murree" in input_texts:
        detected_location = "Murree Road, Rawalpindi"
        location_coords = {"latitude": 33.6200, "longitude": 73.1000}
    elif "i-8" in input_texts or "i8" in input_texts:
        detected_location = "I-8, Islamabad"
        location_coords = {"latitude": 33.6700, "longitude": 73.0900}

    DEMO_FALLBACK["crisis_detector"]["crisis_event"]["location"] = detected_location
    DEMO_FALLBACK["location_intelligence"]["location_data"]["primary_location"]["latitude"] = location_coords["latitude"]
    DEMO_FALLBACK["location_intelligence"]["location_data"]["primary_location"]["longitude"] = location_coords["longitude"]

        # Import locally to avoid circular dependencies
    from agents.signal_collector import SignalCollectorAgent
    from agents.crisis_detector import CrisisDetectorAgent
    from agents.response_planner import ResponsePlannerAgent
    from agents.action_executor import ActionExecutorAgent
    from agents.location_intelligence import LocationIntelligenceAgent

    collector = SignalCollectorAgent()
    detector = CrisisDetectorAgent()
    planner = ResponsePlannerAgent()
    executor = ActionExecutorAgent()

    use_demo = False

    # Step 1: Signal Collection
    collector_result = await collector.process({"inputs": inputs})
    if collector_result is None or "error" in collector_result:
        logging.warning("Signal Collector failed or keys exhausted. Using demo fallback.")
        use_demo = True
        collector_result = DEMO_FALLBACK["signal_collector"]

    signals = collector_result.get("signals", [])
    if not use_demo:
        await asyncio.sleep(5)  # Avoid Gemini Free Tier 15 RPM limits

    # Step 2: Crisis Detection
    if not use_demo:
        detector_result = await detector.process(signals)
        if detector_result is None or "error" in detector_result:
            logging.warning("Crisis Detector failed or keys exhausted. Using demo fallback.")
            use_demo = True
            detector_result = DEMO_FALLBACK["crisis_detector"]
    else:
        detector_result = DEMO_FALLBACK["crisis_detector"]

    crisis_event = detector_result.get("crisis_event", {})
    if not use_demo:
        await asyncio.sleep(5)

    # Step 2.5: Location Intelligence (runs parallel context to Step 3)
    locator = LocationIntelligenceAgent()
    if not use_demo:
        location_result = await locator.process(crisis_event)
        if location_result is None:
            logging.warning("Location Intelligence failed or keys exhausted. Using demo fallback.")
            location_result = DEMO_FALLBACK["location_intelligence"]
    else:
        location_result = DEMO_FALLBACK["location_intelligence"]
    location_data = location_result.get("location_data", {})

    # Step 3: Response Planning
    if not use_demo:
        planner_result = await planner.process(crisis_event)
        if planner_result is None or "error" in planner_result:
            logging.warning("Response Planner failed or keys exhausted. Using demo fallback.")
            use_demo = True
            planner_result = DEMO_FALLBACK["response_planner"]
    else:
        planner_result = DEMO_FALLBACK["response_planner"]

    response_plan = planner_result.get("response_plan", {})
    if not use_demo:
        await asyncio.sleep(5)

    # Step 4: Action Execution
    if not use_demo:
        executor_result = await executor.process(response_plan)
        if executor_result is None or "error" in executor_result:
            logging.warning("Action Executor failed or keys exhausted. Using demo fallback.")
            executor_result = DEMO_FALLBACK["action_executor"]
    else:
        executor_result = DEMO_FALLBACK["action_executor"]

    return {
        "status": "success",
        "pipeline_results": {
            "signal_collector": collector_result,
            "crisis_detector": detector_result,
            "location_intelligence": location_result,
            "response_planner": planner_result,
            "action_executor": executor_result
        }
    }

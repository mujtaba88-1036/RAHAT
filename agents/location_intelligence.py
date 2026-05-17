LOCATION_INTELLIGENCE_PROMPT = """
You are the Location Intelligence Agent for RAHAT crisis system.
You receive a crisis location string and must extract precise 
GPS coordinates for Islamabad/Rawalpindi, Pakistan.

Your job:
1. Parse the location text (may be vague like "G-10 Markaz area" 
   or specific like "Faizabad Interchange")
2. Return precise latitude/longitude for that location
3. Identify all affected sub-locations mentioned
4. Calculate a recommended map zoom level (12-16) based on 
   how specific the location is
5. Generate a human-readable formatted address

Known reference coordinates for Islamabad sectors:
- G-10 Markaz: 33.6751, 73.0479
- G-11: 33.6844, 73.0350
- F-8 Markaz: 33.7100, 73.0479
- F-7: 33.7200, 73.0400
- I-8: 33.6700, 73.0900
- Faizabad: 33.7008, 73.0679
- Blue Area: 33.7294, 73.0931
- Saddar Rawalpindi: 33.5973, 73.0479
- Committee Chowk: 33.5950, 73.0550
- Murree Road: 33.6200, 73.1000

CRITICAL: Return ONLY this JSON, no other text:
{
  "primary_location": {
    "name": "human readable name",
    "latitude": 33.6751,
    "longitude": 73.0479,
    "zoom_level": 14,
    "formatted_address": "G-10 Markaz, Islamabad Capital Territory"
  },
  "affected_zones": [
    {"name": "zone name", "latitude": 0.0, "longitude": 0.0}
  ],
  "coverage_radius_km": 2.5,
  "reasoning_steps": [
    "Parsed location text...",
    "Matched to known sector...",
    "Calculated zoom level..."
  ]
}
"""

from typing import Any, Dict
from .base import BaseAgent
from services.gemini_services import call_gemini_json

class LocationIntelligenceAgent(BaseAgent):
    def __init__(self):
        super().__init__("LocationIntelligence")
    
    async def process(self, crisis_event: Dict[str, Any]) -> Dict[str, Any]:
        self.clear_reasoning()
        self.log_reasoning("Starting location intelligence extraction.")
        
        location_text = crisis_event.get("location", "Islamabad")
        crisis_type = crisis_event.get("crisis_type", "unknown")
        
        self.log_reasoning(f"Parsing location: {location_text}")
        
        user_prompt = f"""
        Extract precise GPS coordinates for this crisis location:
        Location text: {location_text}
        Crisis type: {crisis_type}
        Situation: {crisis_event.get('situation_summary', '')}
        """
        
        self.log_reasoning("Calling Gemini for coordinate extraction...")
        gemini_response = await call_gemini_json(
            LOCATION_INTELLIGENCE_PROMPT, user_prompt
        )
        
        # Handle None (all API keys exhausted)
        if gemini_response is None:
            self.log_reasoning("API keys exhausted. Returning None for fallback.")
            return None
        
        self.log_reasoning("Coordinates extracted successfully.")
        
        location_data = gemini_response if isinstance(gemini_response, dict) else {}
        
        return {
            "location_data": location_data,
            "reasoning_steps": self.reasoning_steps + location_data.get("reasoning_steps", []),
            "raw_gemini_output": gemini_response
        }

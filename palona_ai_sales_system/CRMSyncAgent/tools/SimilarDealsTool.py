from agency_swarm.tools import BaseTool
from pydantic import Field
import os
import json
from typing import Dict, Optional
import numpy as np
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class SimilarDealsTool(BaseTool):
    """
    Identifies similar past deals based on industry and other criteria.
    Uses a robust similarity scoring system to find relevant matches.
    """
    industry: str = Field(
        ..., description="Target industry to match against"
    )
    criteria: Optional[Dict] = Field(
        default={},
        description="Additional matching criteria (e.g., deal_size, company_size)"
    )

    def _calculate_similarity_score(self, deal: Dict, target_industry: str, target_criteria: Dict) -> float:
        """
        Calculate similarity score between a deal and target criteria.
        """
        score = 0.0
        
        # Industry match (partial match allowed)
        deal_industry = deal.get("industry", "").lower()
        target_industry_lower = target_industry.lower()
        
        if target_industry_lower in deal_industry or deal_industry in target_industry_lower:
            score += 1  # Full score for exact match
        elif any(word in deal_industry for word in target_industry_lower.split()):
            score += 0.9  # Partial score for partial match
        
        
        # Deal size similarity (if available)
        if "deal_size" in deal and "deal_size" in target_criteria:
            size_diff = abs(deal["deal_size"] - target_criteria["deal_size"])
            size_score = max(0, 0.2 - (size_diff / target_criteria["deal_size"]) * 0.2)
            score += size_score
        

        return score

    def run(self):
        """
        Finds similar deals based on industry and provided criteria.
        Returns top matches with similarity scores.
        """
        try:
            # Direct path to the CRM data file
            data_file = Path(__file__).parent.parent.parent / 'data' / 'crm_data.json'
            
            # Load deals
            with open(data_file, 'r') as f:
                crm_data = json.load(f)
            
            # Calculate similarity scores
            scored_deals = []
            for deal in crm_data["deals"]:
                if deal.get("status") == "successful":  # Only consider successful deals
                    score = self._calculate_similarity_score(
                        deal,
                        self.industry,
                        self.criteria
                    )
                    if score > 0:  # Only include deals with some similarity
                        scored_deals.append({
                            "deal_id": deal.get("id"),
                            "company_name": deal.get("company"),
                            "industry": deal.get("industry"),
                            "deal_size": deal.get("deal_size"),
                            "deal_date": deal.get("start_date"),
                            "completion_date": deal.get("completion_date"),
                            "key_metrics": deal.get("key_metrics"),
                            "similarity_score": round(score, 2)
                        })

            # Sort by similarity score
            scored_deals.sort(key=lambda x: x["similarity_score"], reverse=True)

            # Return top 5 matches
            return json.dumps({
                "status": "success",
                "matches": scored_deals[:5]
            })

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            }) 
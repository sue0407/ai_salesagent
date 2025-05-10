from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from pathlib import Path
from dotenv import load_dotenv
import openai
import json
import importlib.util
import requests

load_dotenv()

class MessageDraftingTool(BaseTool):
    """
    Generates a personalized sales message using GPT-4/Claude, based on:
    - Sales preparation report (from ReportGenerationTool)
    - Communication summary (from CommunicationSummaryTool)
    - A recent similar deal (from SimilarDealsTool)
    - Lead segmentation (lead_score, customer_segment) from CRM
    The message references a recent similar deal, interprets lead segmentation, and is tailored to the prospect's context.
    """
    company_name: str = Field(
        ..., description="Name of the company to generate message for"
    )
    prospect_name: str = Field(
        ..., description="Full name of the prospect to generate message for"
    )
    lead_id: str = Field(
        ..., description="Lead ID to reference communication history and CRM segmentation"
    )

    def _get_openai_key(self) -> str:
        """Get OpenAI API key from environment"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found in environment")
        return api_key

    def _get_claude_api_key(self):
        return os.getenv("CLAUDE_API_KEY")

    def _read_input_file(self, filename: str) -> str:
        """Read content from a file in the data/outputs directory"""
        try:
            file_path = Path(__file__).parent.parent.parent / 'data' / 'outputs' / filename
            with open(file_path, 'r') as f:
                return f.read().strip()
        except Exception as e:
            return f"Error reading {filename}: {str(e)}"

    def _get_lead_info(self, lead_id: str):
        data_file = Path(__file__).parent.parent.parent / 'data' / 'crm_data.json'
        with open(data_file, 'r') as f:
            crm_data = json.load(f)
        lead = next((l for l in crm_data["crm_leads"] if l["record_id"] == lead_id), None)
        if not lead:
            raise ValueError(f"Lead with id {lead_id} not found.")
        return {
            "lead_score": lead.get("lead_score"),
            "customer_segment": lead.get("customer_segment"),
            "industry": lead.get("industry"),
            "deal_size": lead.get("deal_size"),
            "company_name": lead.get("company_name"),
            "first_name": lead.get("first_name"),
            "last_name": lead.get("last_name")
        }

    def _get_similar_deal(self, industry: str, deal_size):
        # Dynamically import SimilarDealsTool
        tool_path = Path(__file__).parent.parent.parent / 'CRMSyncAgent' / 'tools' / 'SimilarDealsTool.py'
        spec = importlib.util.spec_from_file_location("SimilarDealsTool", tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        SimilarDealsTool = getattr(module, "SimilarDealsTool")
        # Prepare criteria
        criteria = {"deal_size": deal_size} if deal_size else {}
        tool = SimilarDealsTool(industry=industry, criteria=criteria)
        result = tool.run()
        try:
            result_json = json.loads(result)
            if result_json["status"] == "success" and result_json["matches"]:
                return result_json["matches"][0]  # Top match
        except Exception:
            pass
        return None

    def _create_message_prompt(self, report_summary: str, comm_summary: str, similar_deal: dict, lead_info: dict) -> str:
        """Create prompt for message generation"""
        # Similar deal phrase
        similar_deal_phrase = ""
        if similar_deal:
            company = similar_deal.get("company_name", "a peer company")
            industry = similar_deal.get("industry", "your industry")
            metric = similar_deal.get("key_metrics", {}).get("roi")
            metric_phrase = f" (ROI: {metric}%)" if metric else ""
            similar_deal_phrase = f"Recently, we completed a successful project with {company} in {industry}{metric_phrase}, which may be relevant to your goals."
        # Lead segmentation context (subtle, not explicit)
        lead_score = lead_info.get("lead_score")
        customer_segment = (lead_info.get("customer_segment") or "").lower()
        # Data-driven context for LLM
        if customer_segment == "enterprise" and lead_score is not None and lead_score >= 90:
            context_phrase = (
                "This is a flagship, high-priority client for Palona AI, a leader in their industry with significant influence and expectations. "
                "They should be made to feel like a strategic partner and top priority. "
            )
        elif customer_segment == "enterprise" and lead_score is not None and 80 <= lead_score < 90:
            context_phrase = (
                "This is a major enterprise player with strong potential for partnership and impact. "
                "Highlight their scale, reputation, and readiness for innovation. "
            )
        elif customer_segment in ["mid-market", "midmarket", "mid market"] and lead_score is not None and lead_score >= 85:
            context_phrase = (
                "This is a fast-growing, innovative brand in the mid-market segment, showing strong momentum and openness to new solutions. "
                "Emphasize their growth, agility, and potential to become a market leader. "
            )
        elif customer_segment in ["mid-market", "midmarket", "mid market"]:
            context_phrase = (
                "This is a promising mid-market company with ambitions for growth and digital transformation. "
                "Position Palona AI as a catalyst for their next stage of success. "
            )
        elif customer_segment in ["smb", "small business", "small & medium business"]:
            context_phrase = (
                "This is an emerging brand with entrepreneurial spirit and a focus on innovation. "
                "Highlight how Palona AI can help them scale and compete with larger players. "
            )
        else:
            context_phrase = (
                "This prospect represents a valuable opportunity for Palona AI, with unique strengths and potential for partnership. "
                "Tailor the message to their business context and aspirations. "
            )
        segmentation_context = (
            f"{context_phrase}Weave this context into the message naturally, highlighting their leadership, innovation, or market position, but do NOT mention scoring, segmentation, or any internal labels."
        )
        prompt = f"""
# Role
You are an expert sales copywriter specializing in personalized B2B outreach messages for Palona AI, a startup that develops emotionally intelligent, brand-aligned AI agents for D2C businesses.

# Task
Generate a personalized sales outreach message based on the sales preparation report, communication summary, recent similar deal, and the subtle client context provided. The message should be tailored to the prospect's profile, reference prior communications, and propose clear next steps.

# Context
Palona AI's Value Proposition:
- Emotionally intelligent AI agents that mirror a brand's best advisors
- Personalized, persuasive conversations that drive revenue
- Brand-aligned communication across all channels
- 24/7 VIP customer experiences
- Multi-agent systems with proprietary emotional intelligence

# Input Data
---
SALES PREPARATION REPORT:
{report_summary}

---
COMMUNICATION SUMMARY:
{comm_summary}

---
RECENT SIMILAR DEAL:
{similar_deal_phrase}

---
CLIENT CONTEXT (for LLM only, do NOT mention directly):
{segmentation_context}

# Requirements
1. Message Structure:
   - Subject line that captures attention and references key value proposition
   - Conversational introduction that establishes rapport
   - Body that addresses specific pain points and opportunities
   - Reference the recent similar deal to build credibility
   - Subtly convey that the prospect is a high-priority, high-value client, without mentioning scoring or segmentation
   - Clear call to action and next steps

2. Content Guidelines:
   - Keep tone professional yet conversational
   - Reference specific details from the sales report
   - Acknowledge prior communications if any
   - Focus on value proposition and ROI
   - Keep message concise (150-200 words)
   - Personalize based on prospect's background and company context

3. Strategic Elements:
   - Use talking points from the sales report
   - Address identified pain points
   - Reference company initiatives and goals
   - Align with prospect's role and responsibilities
   - Propose specific, relevant next steps

# Output Format
Generate a complete email with:
1. Subject line
2. Body text
3. Signature

The message should be ready to send, with no additional formatting needed.
"""
        return prompt

    def _call_claude(self, prompt: str) -> str:
        api_key = self._get_claude_api_key()
        if not api_key:
            raise ValueError("CLAUDE_API_KEY not found in environment variables.")
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 1000,
            "temperature": 0.7,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["content"][0]["text"].strip()

    def _call_openai(self, prompt: str) -> str:
        api_key = self._get_openai_key()
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert sales copywriter specializing in personalized B2B outreach messages."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()

    def _generate_message(self, prompt: str) -> dict:
        try:
            if self._get_claude_api_key():
                message = self._call_claude(prompt)
            else:
                message = self._call_openai(prompt)
            parts = message.split("\n\n", 1)
            subject = parts[0].replace("Subject:", "").strip()
            body = parts[1] if len(parts) > 1 else message
            return {
                "subject": subject,
                "body": body,
                "recipient": self.prospect_name,
                "company": self.company_name
            }
        except Exception as e:
            raise Exception(f"Error generating message: {str(e)}")

    def run(self):
        """
        Generates a personalized sales message based on sales preparation report, communication summary, recent similar deal, and lead segmentation.
        Reads from saved text files and saves the generated message.
        """
        try:
            # Read input files
            safe_company = self.company_name.replace(' ', '_').lower()
            safe_name = self.prospect_name.replace(' ', '_').lower()
            
            report_summary = self._read_input_file(f'report_{safe_company}_{safe_name}.txt')
            comm_summary = self._read_input_file(f'comm_{self.lead_id}.txt')
            lead_info = self._get_lead_info(self.lead_id)
            similar_deal = self._get_similar_deal(lead_info["industry"], lead_info["deal_size"])
            
            # Create the prompt
            prompt = self._create_message_prompt(report_summary, comm_summary, similar_deal, lead_info)
            
            # Generate the message
            message = self._generate_message(prompt)
            
            # Save output
            outputs_dir = Path(__file__).parent.parent.parent / 'data' / 'outputs'
            outputs_dir.mkdir(parents=True, exist_ok=True)
            output_file = outputs_dir / f'message_{safe_company}_{safe_name}.txt'
            with open(output_file, 'w') as f:
                f.write(f"Subject: {message['subject']}\n\n")
                f.write(message['body'])
            
            return {
                "status": "success",
                "message": message,
                "output_file": str(output_file)
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

if __name__ == "__main__":
    # Test with actual output files and CRM data
    tool = MessageDraftingTool(
        company_name="Sephora",
        prospect_name="Artemis Patrick",
        lead_id="3"
    )
    result = tool.run()
    print(result) 
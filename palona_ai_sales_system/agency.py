from agency_swarm import Agency
from CRMSyncAgent.crm_sync_agent import CRMSyncAgent
from ResearchAgent.research_agent import ResearchAgent
from MessageGenerationAgent.message_generation_agent import MessageGenerationAgent
from ApprovalActionAgent.approval_action_agent import ApprovalActionAgent
from dotenv import load_dotenv

load_dotenv()

# Initialize agents
crm_sync = CRMSyncAgent()
research = ResearchAgent()
message_gen = MessageGenerationAgent()
approval_action = ApprovalActionAgent()

# Create agency with communication flows
agency = Agency(
    [
        approval_action,  # Entry point for user communication
        [approval_action, message_gen],  # Approval agent can communicate with Message Generation agent
        [message_gen, research],  # Message Generation agent can communicate with Research agent
        [research, crm_sync],  # Research agent can communicate with CRM Sync agent
        [message_gen, crm_sync],  # Message Generation agent can communicate with CRM Sync agent
        [approval_action, crm_sync]  # Approval agent can communicate with CRM Sync agent
    ],
    shared_instructions="agency_manifesto.md",
    temperature=0.7,
    max_prompt_tokens=4000
)

if __name__ == "__main__":
    agency.run_demo() 
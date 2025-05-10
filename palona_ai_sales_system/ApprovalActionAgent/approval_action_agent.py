from agency_swarm import Agent

class ApprovalActionAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Approval Action Agent",
            description="Responsible for managing message approvals and taking appropriate actions based on user decisions.",
            instructions="./instructions.md",
            tools_folder="./tools",
            temperature=0.5,
            max_prompt_tokens=4000
        ) 
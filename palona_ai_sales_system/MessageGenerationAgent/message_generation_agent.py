from agency_swarm import Agent

class MessageGenerationAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Message Generation Agent",
            description="Responsible for creating personalized and contextually relevant messages for sales interactions.",
            instructions="./instructions.md",
            tools_folder="./tools",
            temperature=0.7,
            max_prompt_tokens=4000
        ) 
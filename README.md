# Palona AI Sales System

## Overview
Palona AI Sales System is a multi-agent, LLM-powered sales workflow platform designed to automate and enhance the sales process for D2C businesses. It features:
- Multi-step sales workflow (lead selection, research, sales prep, communication summary, email drafting, meeting scheduling)
- CRM integration and update
- LLM-powered research, message generation, and action detection
- Streamlit-based modern UI
- Downloadable sales prep and communication summary reports

## Features
- Lead selection and CRM lookup
- Automated company and LinkedIn research
- AI-generated sales prep guide
- Communication summary with document upload
- AI-generated, editable email drafts
- Meeting scheduling with timezone support
- CRM update and message logging
- Downloadable reports

## Prerequisites
- Python 3.9+
- [pip](https://pip.pypa.io/en/stable/)
- [Git](https://git-scm.com/)
- Claude API key (and optionally OpenAI API key)
- Google API credentials for Gmail/Calendar integration (if using those features)

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sue0407/ai_salesagent.git
   cd ai_salesagent
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r palona_ai_sales_system/requirements.txt
   ```

4. **Set up environment variables:**
   - Copy `.env.example` to `.env` (if provided), or create a `.env` file in `palona_ai_sales_system/` with:
     ```env
     OPENAI_API_KEY=your_openai_api_key
     CLAUDE_API_KEY=your_claude_api_key  
     GMAIL_API_CREDENTIALS=path_to_your_google_credentials.json  # if using Gmail/Calendar
     FROM_EMAIL=your_email@example.com
     ```

5. **Prepare CRM data:**
   - Ensure `palona_ai_sales_system/data/crm_data.json` exists and is populated with your leads and deals.

## Running the App Locally

1. **Start the Streamlit app:**
   ```bash
   streamlit run palona_ai_sales_system/ui/app.py
   ```

2. **Navigate the UI:**
   - Use the sidebar to move through the workflow: Lead Selection → Sales Prep → Communication Summary → Message Drafting → HubSpot Database.
   - Follow on-screen instructions for each step.

## Troubleshooting
- **API Key Errors:** Ensure your `.env` file is set up and keys are valid.
- **File Not Found:** Make sure all required data files (e.g., `crm_data.json`) exist.
- **Gmail/Calendar Integration:** Ensure Google API credentials are set up and OAuth tokens are generated.
- **Streamlit Warnings:** If you see widget/session state warnings, ensure you are not setting session state after widget creation.
- **UI Not Updating:** Use the "Refresh" button in the HubSpot Database page to reload CRM data after updates.

## Architecture Decisions

### Multi-Agent Design
- The system is built using the Agency Swarm framework, with each agent responsible for a distinct part of the sales workflow (CRM Sync, Research, Message Generation, Approval/Action).
- Agents communicate via structured data handoffs and follow defined communication flows for modularity and traceability.

### Modular Tool Structure
- Each agent has its own set of tools (Python classes) for specific tasks (e.g., research, CRM update, message drafting).
- Tools are implemented as Pydantic classes for type safety and validation, and are easily extensible.
- Shared state and session management are used for efficient data passing between steps.

### Streamlit UI
- The user interface is built with Streamlit for rapid development, modern UX, and easy integration with Python backends.
- Each workflow step (lead selection, research, prep, summary, drafting) is a separate Streamlit page/module.
- Session state is used to persist user selections and workflow progress.

### Environment Variable Management
- Sensitive credentials (API keys, Google credentials) are managed via a `.env` file and loaded with `python-dotenv`.
- This approach keeps secrets out of the codebase and supports easy local and cloud deployment.

### Data Management
- CRM data is stored in a JSON file for easy prototyping and local testing.
- All updates (messages, logs, follow-ups) are written back to this file, simulating a real CRM integration.

### Extensibility
- The architecture supports adding new agents, tools, or workflow steps with minimal changes to the core system.
- LLM provider (Claude, OpenAI) is selected dynamically based on available API keys.

## Contributing
Pull requests and issues are welcome!

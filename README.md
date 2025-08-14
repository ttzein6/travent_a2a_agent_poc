# Travel Agent System

A multi-agent travel planning system that coordinates between specialized agents to provide comprehensive travel solutions.

## Project Structure

The project consists of three main components:

- **Host Agent** (`host_agent/`) - Travel orchestrator that coordinates between specialized agents
- **Travel Planning Agent** (`travel_planning_agent/`) - Creates detailed itineraries, recommends accommodations, and plans activities
- **Search Agent** (`search_agent/`) - Performs real-time searches for flights, hotels, activities, and travel information

## Prerequisites

- Python 3.10 or higher
- UV package manager

## Environment Setup

Create a `.env` file in the root directory with the following variables:

```env
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_custom_search_engine_id
TRAVEL_PLANNING_AGENT_PORT=10002
SEARCH_AGENT_PORT=10003
```

Required environment variables:
- `GOOGLE_API_KEY`: Your Google API key for both Gemini and Custom Search
- `GOOGLE_SEARCH_ENGINE_ID`: Your Google Custom Search Engine ID

Optional environment variables:
- `GOOGLE_GENAI_USE_VERTEXAI=TRUE` (if using Vertex AI instead of API key)
- `HOST_OVERRIDE=http://custom-host:port/` (to override default host URL)

## Installation and Running Guide

### For Individual Agents (Travel Planning Agent & Search Agent)

Start with the **Travel Planning Agent**:

1. Navigate to the agent directory:
   ```bash
   cd travel_planning_agent
   ```

2. Create a virtual environment:
   ```bash
   uv venv
   ```

3. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   uv sync
   ```

5. Run the agent:
   ```bash
   uv run --active .
   ```
   The agent will start on `http://127.0.0.1:10002`

Now start the **Search Agent** (in a new terminal):

1. Navigate to the agent directory:
   ```bash
   cd search_agent
   ```

2. Create a virtual environment:
   ```bash
   uv venv
   ```

3. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   uv sync
   ```

5. Run the agent:
   ```bash
   uv run --active .
   ```
   The agent will start on `http://127.0.0.1:10003`

### For Host Agent

Finally, start the **Host Agent** (in a third terminal):

1. Navigate to the host agent directory:
   ```bash
   cd host_agent
   ```

2. Create a virtual environment:
   ```bash
   uv venv
   ```

3. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   uv sync
   ```

5. Run the host agent with ADK web interface:
   ```bash
   uv run --active adk web
   ```

### Startup Order
**Important**: Always start agents in this order:
1. Travel Planning Agent (port 10002)
2. Search Agent (port 10003)  
3. Host Agent (ADK web interface)

The Host Agent will automatically discover and connect to the other agents running on their respective ports.

## Agent Capabilities

### Travel Planning Agent
- **Skill**: `travel_planning`
- **Description**: Creates comprehensive, personalized travel itineraries with accommodations, activities, and logistics
- **Input**: Text/plain
- **Output**: Text/plain
- **Port**: 10002
- **Capabilities**: 
  - Detailed day-by-day itinerary creation
  - Accommodation recommendations based on budget and preferences
  - Activity planning and cultural insights
  - Transportation and logistics coordination

### Search Agent  
- **Skill**: `travel_search`
- **Description**: Performs real-time searches for travel information including flights, hotels, activities, and local details
- **Input**: Text/plain
- **Output**: Text/plain, text/event-stream
- **Port**: 10003
- **Tools**: Google Custom Search API
- **Capabilities**:
  - Real-time flight and hotel pricing
  - Availability checks for accommodations and activities
  - Local information and weather updates
  - Current travel advisories and requirements

### Host Agent
- **Description**: Travel orchestrator that coordinates between planning and search agents to provide complete travel solutions

## Usage

Once all agents are running, you can interact with the travel system by sending requests to the Host Agent. The system will:

1. **Analyze your travel request** - Understanding destination, dates, budget, and preferences
2. **Delegate to appropriate agents** - Travel planning for itineraries, search agent for real-time information
3. **Coordinate responses** - Combining expert planning with current travel data
4. **Provide comprehensive solutions** - Complete travel plans with actionable information

### Example Travel Requests:
- "Plan a 5-day romantic trip to Paris for $2500 in April"
- "Find the best family-friendly hotels in Tokyo with current pricing"
- "Create an adventure travel itinerary for Costa Rica with flight options"

## Development

This project uses:
- **A2A SDK** (v0.2.5) for agent-to-agent communication
- **Google ADK** (v1.3.0) for agent development
- **Google Custom Search API** for real-time travel information
- **Uvicorn** for ASGI server
- **Python-dotenv** for environment variable management
- **HTTPX** for HTTP client functionality

## Setup Google Custom Search

To enable the search agent functionality:

1. **Create a Google Custom Search Engine**:
   - Visit [Google Custom Search](https://cse.google.com/)
   - Create a new search engine
   - Configure it to search the entire web
   - Get your Search Engine ID

2. **Enable Custom Search API**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Custom Search API
   - Use your existing Google API key

## Troubleshooting

- Ensure all required environment variables are set (especially `GOOGLE_SEARCH_ENGINE_ID`)
- Make sure each agent is running on its designated port
- Check that the Google API key has permissions for both Gemini and Custom Search APIs  
- Verify that ports 10002 and 10003 are available
- Test Google Custom Search API access independently if search functionality fails
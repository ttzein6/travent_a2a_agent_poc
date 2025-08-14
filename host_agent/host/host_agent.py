import asyncio
import base64
import json
import uuid

from typing import List, Optional

import httpx

from a2a.client import A2ACardResolver
from a2a.types import (
    AgentCard,
    DataPart,
    Message,
    MessageSendConfiguration,
    MessageSendParams,
    Part,
    Task,
    TaskState,
    TextPart, SendMessageRequest, SendMessageResponse, SendMessageSuccessResponse, FilePart, FileWithBytes, Role,
    FileWithUri,
)
from google.adk import Agent
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.llm_agent import BeforeToolCallback
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.events import Event
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from google.adk.runners import Runner
from .remote_agent_connection import RemoteAgentConnections, TaskCallbackArg, TaskUpdateCallback
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

class HostAgent:
    """The host agent.

    This is the agent responsible for choosing which remote agents to send
    tasks to and coordinate their work.
    """

    def __init__(self):
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        # self.httpx_client = http_client
        self.agents :str = ''
        self.agent = self.create_agent()
        self._user_id= "host_agent"
        self.session_service =InMemorySessionService()
        self.session_id = str(uuid.uuid4())
        self.session = self.session_service.create_session_sync(session_id=self.session_id,app_name=self.agent.name,user_id="host_agent")
        self.runner = Runner(
            app_name=self.agent.name,
            agent=self.agent,
            artifact_service=InMemoryArtifactService(),
            session_service=self.session_service,
            memory_service=InMemoryMemoryService(),
        )
        # Initialize task_callback properly
        # self.task_callback = task_callback if task_callback else self._default_task_callback
        # loop = asyncio.get_running_loop()
        # loop.create_task(self.init_remote_agent_addresses(remote_agent_addresses))
    
    
    async def _async_init_components(self,remote_agent_addresses: List[str]):
        async with httpx.AsyncClient(timeout=30) as client:
            for address in remote_agent_addresses:
                card_resolver = A2ACardResolver(client, address)
                try: 
                    card = await card_resolver.get_agent_card()
                    remote_connection = RemoteAgentConnections(card, address)
                    self.remote_agent_connections[card.name] = remote_connection
                    self.cards[card.name] = card
                except httpx.ConnectError as e:
                    print(f"Error connecting to {address}: {e}")
                    continue
                except Exception as e:
                    print(f"Error retrieving card for {address}: {e}")
                    continue
        agent_info = [
            json.dumps({"name": card.name, "description": card.description})
            for card in self.cards.values()
        ]
        print("================================================\n")
        print(f"agent_info ==== {agent_info}")
        self.agents = '\n'.join(agent_info) if agent_info else 'No remote agents found'


    @classmethod
    async def create(cls,remote_agent_addresses: List[str]):
        instance = cls()
        await instance._async_init_components(remote_agent_addresses)
        return instance

    def get_current_date_time(self, tool_context: ToolContext) -> str:
        """Returns the current date and time in ISO format."""
        return types.Timestamp.now().isoformat()
    def create_agent(self) -> Agent:

        return LlmAgent(
            model='gemini-2.0-flash-001',
            name='Travel_Host_Agent',
            instruction=self.root_instruction,
            description=(
                'This agent orchestrates travel requests by coordinating between'
                ' the travel planning agent and search agent to provide comprehensive'
                ' travel solutions.'
            ),

            tools=[
                self.send_message,
                self.get_current_date_time,
            ],
        )

    def root_instruction(self, context: ReadonlyContext) -> str:

        # return f"""You are an expert delegator that can delegate the user request to the
        # appropriate remote agents.
        # If user request contains file or documents extract text (or OCR) then delegate the task with text extracted.
        # Discovery:
        # - You can use `send_message` to send a task to a remote agent.
        #
        # Execution:
        # - For actionable requests, you can use `send_message` to interact with remote agents to take action.
        # ***Important Notice*** if user request includes a file, extract text content from file and use for tool calling
        # Be sure to include the remote agent name when you respond to the user.
        #
        # Please rely on tools to address the request, and don't make up the response. If you are not sure, please ask the user for more details.
        # Focus on the most recent parts of the conversation primarily.
        #
        # - If you are not sure about the task, please ask the user for more details.
        #
        #  <Available Agents>
        #         {self.agents}
        #  </Available Agents>
        # """
        return f"""# Travel Orchestrator AI Agent System Instruction

You are an intelligent travel orchestrator responsible for coordinating comprehensive travel planning services. Your primary role is to analyze travel requests and delegate tasks between the travel planning agent and search agent to provide complete travel solutions.
You can use get_current_date_time to get the current date and time in ISO format.
## Core Responsibilities

### 1. Travel Request Analysis & Agent Selection
- **Parse travel intent**: Analyze user requests for destinations, dates, budget, preferences, and travel style
- **Match travel capabilities**: Select appropriate agents based on travel planning needs (itinerary creation vs. real-time search)
- **Multi-agent coordination**: Coordinate between planning and search agents for comprehensive travel solutions

### 2. Travel Context Processing
- **Extract travel details**: Process travel dates, budget constraints, group size, preferences, and special requirements
- **Context preservation**: Maintain travel context when delegating between agents
- **Preference handling**: Track user preferences for accommodations, activities, transportation, and dining

### 3. Travel Task Delegation & Communication
- **Travel planning delegation**: Send detailed travel requirements to the travel planning agent for itinerary creation
- **Search delegation**: Request real-time information from search agent for flights, hotels, activities, and local information
- **Context coordination**: Ensure both agents have complete travel context and user preferences

## Travel Execution Guidelines

### Discovery Phase
- Use `send_message(agent_name, travel_request)` to delegate travel tasks to specialized agents
- Include complete travel context: destinations, dates, budget, group details, preferences
- For unclear travel requests, ask specific clarifying questions about dates, budget, preferences

### Travel Planning Coordination
- **ALWAYS Search First**: Begin by delegating to the Search Agent to gather current information about destinations, pricing, availability, and conditions
- **Then Plan Based on Data**: Use search results to inform the Travel Planning Agent with real-time constraints and opportunities
- **Two-Phase Approach**: Search → Plan → Synthesize for optimal travel recommendations

## Travel Quality Assurance

### Travel Information Validation
- **Real-time accuracy**: Ensure search agent provides current pricing and availability information
- **Practical planning**: Verify travel planning agent creates realistic and feasible itineraries
- **Budget compliance**: Ensure all recommendations align with stated budget constraints

### Travel Error Handling
- If search agent can't find current information, suggest alternative dates or destinations
- If planning agent creates unfeasible itineraries, request revisions with specific constraints
- Provide backup options for fully booked destinations or dates

## Travel Communication Standards

### User Interaction
- **Travel transparency**: Always inform users which agent is handling specific aspects of their trip
- **Travel progress**: Provide updates on itinerary creation and search progress
- **Clear travel attribution**: Indicate whether recommendations come from planning expertise or real-time searches

### Travel Agent Communication
- **Structured travel requests**: Use consistent format for travel requirements (dates, budget, preferences)
- **Complete travel context**: Include all travel details in agent communications
- **Specific travel instructions**: Provide clear, actionable travel planning or search instructions

## Travel Decision Framework

For each travel request, systematically follow this workflow:
1. **Identify travel type** (leisure, business, adventure, luxury, budget)
2. **Determine travel components** (flights, accommodation, activities, transportation)
3. **MANDATORY: Search First** - Always delegate to Search Agent first to gather:
   - Current pricing and availability for flights and accommodations
   - Seasonal considerations and weather conditions
   - Local events, festivals, or disruptions
   - Travel advisories and entry requirements
4. **Plan Based on Search Results** - Use search findings to inform Travel Planning Agent with:
   - Real-time constraints (availability, pricing)
   - Current opportunities (deals, events, optimal timing)
   - Updated requirements (visa changes, health protocols)
5. **Synthesize Complete Solution** - Combine search data with expert planning for actionable recommendations

## Travel Specializations

### Search Agent Tasks (ALWAYS USE FIRST):
- Real-time flight searches and pricing
- Hotel availability and current rates
- Local attraction information and reviews
- Weather forecasts and seasonal considerations
- Transportation options and schedules
- Travel advisories and entry requirements
- Local events and festivals during travel dates

### Travel Planning Agent Tasks (USE AFTER SEARCH RESULTS):
- Creating detailed day-by-day itineraries informed by current data
- Recommending accommodations based on search results and preferences
- Planning activities based on availability and current conditions
- Organizing transportation using real-time options and pricing
- Managing travel logistics with current requirements and constraints

## Available Travel Agents
{self.agents}

Remember: Your effectiveness in travel orchestration is measured by how well you coordinate between specialized agents to create seamless, personalized travel experiences that meet user preferences and constraints.

<Available Agents>
    {self.agents}
</Available Agents>"""
    async def get_file_from_name(self, file_name: str,tool_context: ToolContext) -> Optional[str]:
        """
        Retrieve file bytes from the conversation history based on the file name.
        
        Args:
            tool_context:
            file_name: Name of the file to retrieve
            
        Returns:
            Base64-encoded string of the file bytes if found, None otherwise
        """
        files = tool_context.state.get("files",[])
        if len(files)> 0:
            for file in files:
                if file["file_name"] == file_name:
                    return file["file_bytes"]
        else:
            return None
        # try:
        #
        #     sessions = await self.runner.session_service.list_sessions(app_name=self.agent.name,user_id=self._user_id)
        #     print(f"sessions: \n=================================================\n{sessions}")
        #     # Get the most recent session
        #     # session = await self._runner.session_service.get_session(
        #     #     app_name=self.agent.name,
        #     #     user_id=self._user_id,
        #     #     session_id=self.session_id,
        #     # )
        #     session = self.session
        #     if not session:
        #         print(f"No active session found for user {self._user_id}")
        #         return None
        #
        #     # Get recent messages from the session
        #     events : List[Event] = session.events
        #     if len(events) == 0:
        #         print("EVENTS ARE EMTPY")
        #         return None
        #     for e in events:
        #         print(f"Event: {e}")
        #         if e.content.parts:
        #             for part in e.content.parts:
        #                 print(f"PART: {part}")
        #
        #                 if isinstance(part, FilePart):
        #                     print(f"FILE PART: {part.file.name}")
        #                     if part.file.name == file_name:
        #                         return base64.b64encode(part.file.bytes.encode('utf-8')).decode('utf-8')
        #                 else:
        #                     print(f"TPART:{part.inline_data.mime_type}\n{part.inline_data.data}")
        #         else:
        #             print(f"No parts found in event {e}")
        #     return None
        # except Exception as e:
        #     print(f"Error retrieving file: {str(e)}")
        #     return None
            
    async def send_message(
            self,agent_name: str,
            task: str,
            tool_context: ToolContext,
            # file_name :str = "" ,
            # file_mime_type: str = "",
            # file_url: str ="",
           ):
        """Sends a task to a remote agent"""

        if agent_name not in self.remote_agent_connections:
             print(f"Unknown agent: {agent_name}")
             return
        client = self.remote_agent_connections[agent_name]
        if not client:
            print(f"No connection to {agent_name}")
            return
        message_id = str(uuid.uuid4())
        # file_part : FilePart | None = None

        # if file_url != "" or file_name != "":
        #
        #     print("========================================================")
        #     print("====================File Name Search====================")
        #     print(f"================={file_name}=================")
        #
        #     # Ensure we have a mime type if not provided
        #     if not file_mime_type:
        #         # Guess MIME type based on file extension
        #         if file_name.lower().endswith('.pdf'):
        #             file_mime_type = 'application/pdf'
        #         elif file_name.lower().endswith(('.doc', '.docx')):
        #             file_mime_type = 'application/msword'
        #         elif file_name.lower().endswith(('.xls', '.xlsx')):
        #             file_mime_type = 'application/vnd.ms-excel'
        #         elif file_name.lower().endswith(('.ppt', '.pptx')):
        #             file_mime_type = 'application/vnd.ms-powerpoint'
        #         elif file_name.lower().endswith(('.jpg', '.jpeg')):
        #             file_mime_type = 'image/jpeg'
        #         elif file_name.lower().endswith('.png'):
        #             file_mime_type = 'image/png'
        #         elif file_name.lower().endswith('.txt'):
        #             file_mime_type = 'text/plain'
        #         else:
        #             file_mime_type = 'application/octet-stream'
        #
        #     print(f"Creating file part with name: {file_name}, mime_type: {file_mime_type}")
        #     if file_url != "":
        #         file_part = FilePart(file=FileWithUri(name=file_name, uri=file_url, mimeType=file_mime_type))
        #     else:
        #         file_bytes = await self.get_file_from_name(file_name,tool_context)
        #         if file_bytes:
        #             file_part = FilePart(file=FileWithBytes(name=file_name, bytes=file_bytes, mimeType=file_mime_type))
        #         else:
        #             print(f"=!+!+!+!+!+!+!+ File bytes failed")
        # else:
        #      print(f"Could not find file: {file_name}")
        #      return
        text_part = TextPart(
            text=task,
        )
        parts : List[Part] = [text_part]
        # if file_part:
        #     parts.append(file_part)

        message_send_params = MessageSendParams(
            message=Message(
                role=Role.user,
                messageId= message_id,
                parts= parts,
            )
        )
        message_request = SendMessageRequest(
            id=message_id,
            # params=MessageSendParams.model_validate(payload),
            params= message_send_params,
        )
        send_response: SendMessageResponse = await client.send_message(message_request)
        print(f"send_response ==== {send_response}")
        if not isinstance(send_response.root, SendMessageSuccessResponse) or not isinstance(send_response.root.result, Task):
            print("Received a non-success or non-task response from the remote agent")
            return 
        response_content = send_response.root.model_dump_json(exclude_none=True)
        json_content = json.loads(response_content)
        resp = []
        if json_content.get("result", {}).get("artifacts"):
            for artifact in json_content["result"]["artifacts"]:
                if artifact.get("parts"):
                    resp.extend(artifact["parts"])
        return resp
        



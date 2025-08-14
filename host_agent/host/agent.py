# from .host_agent import HostAgent
# import httpx
# agents_addresses= ['http://localhost:10002', 'http://localhost:10003']
# root_agent = HostAgent(agents_addresses,http_client=httpx.AsyncClient()).create_agent()


import asyncio


import nest_asyncio
from google.adk.runners import Runner
from a2a.types import (
    AgentCard,
    AgentCapabilities, AgentSkill,
)
import logging

from dotenv import load_dotenv

from google.genai import types

from .host_agent import HostAgent


load_dotenv()
nest_asyncio.apply()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def _get_initialized_host_agent_sync() -> HostAgent:
    """Synchronously creates and initializes the HostAgent."""

    async def _async_main():
        # Hardcoded URLs for the friend agents
        friend_agent_urls = [
            "http://127.0.0.1:10002",  # Evaluation Agent
            "http://127.0.0.1:10003",  # RFP Parser Agent
            # "http://localhost:10004",  # Nate's Agent
        ]

        print("initializing host agent")
        hosting_agent_instance = await HostAgent.create(
            remote_agent_addresses=friend_agent_urls
        )
        print("HostAgent initialized")
        return hosting_agent_instance

    try:
        return asyncio.run(_async_main())
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            print(
                f"Warning: Could not initialize HostAgent with asyncio.run(): {e}. "
                "This can happen if an event loop is already running (e.g., in Jupyter). "
                "Consider initializing HostAgent within an async function in your application."
            )
        else:
            raise

host = "127.0.0.1"
port = 9999


host_agent = _get_initialized_host_agent_sync()
runner: Runner = host_agent.runner
root_agent = runner.agent


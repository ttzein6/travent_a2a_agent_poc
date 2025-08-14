import asyncio
import logging
from collections.abc import AsyncGenerator

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    FilePart,
    FileWithBytes,
    FileWithUri,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.task import new_task
from a2a.utils.errors import ServerError
from google.adk import Runner
from google.adk.events import Event
from google.genai import types

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TravelPlanningAgentExecutor(AgentExecutor):
    """An AgentExecutor that runs Travel Planning Agent."""
    def __init__(self, runner: Runner):
    
        self.runner = runner
        self._running_sessions = {}

    def _run_agent(
        self, session_id, new_message: types.Content
    ) -> AsyncGenerator[Event, None]:
        try:
            return self.runner.run_async(
                session_id=session_id, user_id="travel_planning_agent", new_message=new_message
            )
        except asyncio.CancelledError as e:
            logger.error(f"Agent execution was cancelled: {e}")
            # Re-raise to allow proper handling by caller
            raise
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            raise

    async def _process_request(
        self,
        new_message: types.Content,
        session_id: str,
        task_updater: TaskUpdater,
    ) -> None:
        try:
            session_obj = await self._upsert_session(session_id)
            session_id = session_obj.id
            print(f"new_message {new_message}")
            
            # Set a timeout for the API call
            try:
                async with asyncio.timeout(30):  # 30 second timeout
                    async for event in self._run_agent(session_id, new_message):
                        if event.is_final_response():
                            parts = convert_genai_parts_to_a2a(
                                event.content.parts if event.content and event.content.parts else []
                            )
                            logger.debug("Yielding final response: %s", parts)
                            await task_updater.add_artifact(parts)
                            await task_updater.complete()
                            
                            break
                        if not event.get_function_calls():
                            logger.debug("Yielding update response")
                            await task_updater.update_status(
                                TaskState.working,
                                message=task_updater.new_agent_message(
                                    convert_genai_parts_to_a2a(
                                        event.content.parts
                                        if event.content and event.content.parts
                                        else []
                                    ),
                                ),
                            )
                            continue
                        else:
                            logger.debug("Skipping event")
            except asyncio.TimeoutError:
                logger.error("API call timed out")
                await task_updater.update_status(
                    TaskState.failed,
                    message=task_updater.new_agent_message([
                        Part(root=TextPart(text="The API call timed out. Please try again later."))
                    ]),
                )
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            await task_updater.update_status(
                TaskState.failed,
                message=task_updater.new_agent_message([
                    Part(root=TextPart(text=f"An error occurred: {str(e)}"))
                ]),
            )

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ):
        if not context.task_id or not context.context_id:
            raise ValueError("RequestContext must have task_id and context_id")
        if not context.message:
            raise ValueError("RequestContext must have a message")
        print("================================================\n")
        print(f"context ==== {context}")
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        
        # Properly set up the task and notify that work has started
        if not context.current_task:
            try:
                await updater.submit(context.message)
            except Exception as e:
                logger.error(f"Error submitting task: {e}")
        
        try:
            await updater.start_work()
        except Exception as e:
            logger.error(f"Error starting work: {e}")
            
        print("================================================\n")
        print(f"updater ==== started working....")
        await self._process_request(
            types.UserContent(
                parts=convert_a2a_parts_to_genai(context.message.parts),
            ),
            task.contextId,
            updater,
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise ServerError(error=UnsupportedOperationError())

    async def _upsert_session(self, session_id: str):
        session = await self.runner.session_service.get_session(
            app_name=self.runner.app_name, user_id="travel_planning_agent", session_id=session_id
        )
        if session is None:
            session = await self.runner.session_service.create_session(
                app_name=self.runner.app_name,
                    user_id="travel_planning_agent",
                session_id=session_id,
            )
        if session is None:
            raise RuntimeError(f"Failed to get or create session: {session_id}")
        return session


def convert_a2a_parts_to_genai(parts: list[Part]) -> list[types.Part]:
    """Convert a list of A2A Part types into a list of Google Gen AI Part types."""
    return [convert_a2a_part_to_genai(part) for part in parts]


def convert_a2a_part_to_genai(part: Part) -> types.Part:
    """Convert a single A2A Part type into a Google Gen AI Part type."""
    root = part.root
    if isinstance(root, TextPart):
        return types.Part(text=root.text)
    if isinstance(root, FilePart):
        if isinstance(root.file, FileWithUri):
            return types.Part(
                file_data=types.FileData(
                    file_uri=root.file.uri, mime_type=root.file.mimeType
                )
            )
        if isinstance(root.file, FileWithBytes):
            return types.Part(
                inline_data=types.Blob(
                    data=root.file.bytes.encode("utf-8"),
                    mime_type=root.file.mimeType or "application/octet-stream",
                )
            )
        raise ValueError(f"Unsupported file type: {type(root.file)}")
    raise ValueError(f"Unsupported part type: {type(part)}")


def convert_genai_parts_to_a2a(parts: list[types.Part]) -> list[Part]:
    """Convert a list of Google Gen AI Part types into a list of A2A Part types."""
    return [
        convert_genai_part_to_a2a(part)
        for part in parts
        if (part.text or part.file_data or part.inline_data)
    ]


def convert_genai_part_to_a2a(part: types.Part) -> Part:
    """Convert a single Google Gen AI Part type into an A2A Part type."""
    if part.text:
        return Part(root=TextPart(text=part.text))
    if part.file_data:
        if not part.file_data.file_uri:
            raise ValueError("File URI is missing")
        return Part(
            root=FilePart(
                file=FileWithUri(
                    uri=part.file_data.file_uri,
                    mimeType=part.file_data.mime_type,
                )
            )
        )
    if part.inline_data:
        if not part.inline_data.data:
            raise ValueError("Inline data is missing")
        return Part(
            root=FilePart(
                file=FileWithBytes(
                    bytes=part.inline_data.data.decode("utf-8"),
                    mimeType=part.inline_data.mime_type,
                )
            )
        )
    raise ValueError(f"Unsupported part type: {part}")

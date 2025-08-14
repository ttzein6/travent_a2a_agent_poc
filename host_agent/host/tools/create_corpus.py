"""
Tool for creating a new candidate corpus for resume/CV matching.
"""

import re

from google.adk.tools.tool_context import ToolContext
from vertexai import rag

from ..config import (
    DEFAULT_EMBEDDING_MODEL,
)
from .utils import check_corpus_exists


def create_corpus(
    corpus_name: str,
    tool_context: ToolContext,
) -> dict:
    """
    Create a new candidate corpus for storing resumes, CVs, and candidate profiles.

    Args:
        corpus_name (str): The name for the new candidate corpus (e.g., "engineering_candidates", "marketing_applicants")
        tool_context (ToolContext): The tool context for state management

    Returns:
        dict: Status information about the operation
    """
    # Check if corpus already exists
    if check_corpus_exists(corpus_name, tool_context):
        return {
            "status": "info",
            "message": f"Candidate corpus '{corpus_name}' already exists",
            "corpus_name": corpus_name,
            "corpus_created": False,
        }

    try:
        # Clean corpus name for use as display name
        display_name = re.sub(r"[^a-zA-Z0-9_-]", "_", corpus_name)

        # Configure embedding model optimized for candidate profile matching
        embedding_model_config = rag.RagEmbeddingModelConfig(
            vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
                publisher_model=DEFAULT_EMBEDDING_MODEL
            )
        )

        # Create the candidate corpus
        rag_corpus = rag.create_corpus(
            display_name=display_name,
            backend_config=rag.RagVectorDbConfig(
                rag_embedding_model_config=embedding_model_config
            ),
        )

        # Update state to track corpus existence
        tool_context.state[f"corpus_exists_{corpus_name}"] = True

        # Set this as the current corpus
        tool_context.state["current_corpus"] = corpus_name

        return {
            "status": "success",
            "message": f"Successfully created candidate corpus '{corpus_name}'",
            "corpus_name": rag_corpus.name,
            "display_name": rag_corpus.display_name,
            "corpus_created": True,
            "next_steps": "You can now add candidate profiles using the add_data tool."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating candidate corpus: {str(e)}",
            "corpus_name": corpus_name,
            "corpus_created": False,
        }

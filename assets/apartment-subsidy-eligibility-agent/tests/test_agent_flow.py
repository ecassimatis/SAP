"""Integration test for the apartment subsidy eligibility agent end-to-end flow."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agent import SampleAgent


@pytest.fixture
def mock_tools():
    """Return a mock tool list simulating MCP + custom tools."""
    tool = MagicMock()
    tool.name = "ingest_documents"
    return [tool]


@pytest.mark.asyncio
async def test_agent_stream_completes(mock_tools):
    """Agent stream() completes and returns a result dict."""
    agent = SampleAgent()

    with patch.object(
        agent, "_invoke_with_fallback", new_callable=AsyncMock
    ) as mock_invoke:
        mock_message = MagicMock()
        mock_message.content = (
            "The applicant qualifies for housing subsidy. "
            "Recommendation: APPROVE with confidence 95%."
        )
        mock_invoke.return_value = {"messages": [mock_message]}

        results = []
        async for chunk in agent.stream(
            query="Check eligibility for this applicant with country code DE.",
            context_id="test-ctx-001",
            tools=mock_tools,
        ):
            results.append(chunk)

    assert len(results) >= 2
    final = results[-1]
    assert final["is_task_complete"] is True
    assert "APPROVE" in final["content"] or "eligibility" in final["content"].lower()


@pytest.mark.asyncio
async def test_agent_invoke_returns_response(mock_tools):
    """Agent invoke() returns an AgentResponse."""
    agent = SampleAgent()

    with patch.object(
        agent, "_invoke_with_fallback", new_callable=AsyncMock
    ) as mock_invoke:
        mock_message = MagicMock()
        mock_message.content = "Eligibility check complete. Recommendation: REJECT."
        mock_invoke.return_value = {"messages": [mock_message]}

        response = await agent.invoke(
            query="Validate documents for apartment access.",
            context_id="test-ctx-002",
            tools=mock_tools,
        )

    assert response.status == "completed"
    assert "REJECT" in response.message or response.message


@pytest.mark.asyncio
async def test_agent_stream_handles_exception(mock_tools):
    """Agent stream() handles exceptions gracefully."""
    agent = SampleAgent()

    with patch.object(
        agent, "_invoke_with_fallback", side_effect=Exception("LLM unavailable")
    ):
        results = []
        async for chunk in agent.stream(
            query="Check this applicant.",
            context_id="test-ctx-003",
            tools=mock_tools,
        ):
            results.append(chunk)

    final = results[-1]
    assert final["is_task_complete"] is True
    assert "error" in final["content"].lower()

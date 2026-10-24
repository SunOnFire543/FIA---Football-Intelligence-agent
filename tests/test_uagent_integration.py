"""Unit and integration tests for Fetch.ai uAgents native runtime and AgentChatProtocol."""

import time
import uuid
import pytest
from uagents_core.contrib.protocols.chat import ChatMessage, ChatAcknowledgement, TextContent
from app.fetch.uagent_service import (
    FootballAnalysisResult,
    create_football_uagent,
    execute_pipeline_for_query,
    official_chat_protocol,
)


def test_uagent_instantiation_and_chat_protocol():
    agent = create_football_uagent(name="TestFootballAgent", seed="test_seed_phrase_123")
    assert agent.name == "TestFootballAgent"
    # uAgents addresses start with 'agent1q'
    assert agent.address.startswith("agent1q")
    assert len(agent.protocols) >= 1

    # Check that official AgentChatProtocol is registered
    protocol_names = [p.name for p in agent.protocols.values()]
    assert "AgentChatProtocol" in protocol_names


def test_chat_message_schema_and_text_extraction():
    msg = ChatMessage(
        timestamp=int(time.time()),
        msg_id=uuid.uuid4(),
        content=[TextContent(type="text", text="Analyse the next Arsenal match")],
    )
    assert msg.text() == "Analyse the next Arsenal match"
    ack = ChatAcknowledgement(
        timestamp=int(time.time()),
        acknowledged_msg_id=msg.msg_id,
    )
    assert ack.acknowledged_msg_id == msg.msg_id


def test_uagent_pipeline_execution_demo_mode():
    res = execute_pipeline_for_query("Arsenal", data_mode="DEMO")
    assert res.status == "SUCCESS"
    assert res.data_mode == "DEMO"
    assert "[DATA MODE: DEMO (SIMULATED)]" in res.report
    assert "DEMO / SIMULATION MODE NOTICE" in res.report
    assert res.evidence_record_id is not None


def test_uagent_pipeline_execution_live_mode_rejection():
    # In LIVE mode without configured provider keys, pipeline must reject rather than fabricate
    res = execute_pipeline_for_query("Arsenal", data_mode="LIVE")
    assert res.status == "UNCONFIGURED_PROVIDER"
    assert res.data_mode == "LIVE"
    assert "Live Data Provider Unconfigured" in res.report


def test_uagent_identity_consistency_and_mailbox_configuration():
    # Verify deterministic identity derivation from seed across restarts
    a1 = create_football_uagent(seed="test_consistent_seed")
    a2 = create_football_uagent(seed="test_consistent_seed")
    assert a1.address == a2.address
    assert str(a1.wallet.address()) == str(a2.wallet.address())

    # Verify mailbox configuration sets mailbox endpoint without changing identity
    a_mb = create_football_uagent(seed="test_consistent_seed", mailbox="test_key")
    assert a_mb._use_mailbox is True
    assert "mailbox" in a_mb._endpoints[0].url
    assert a_mb.address == a1.address
    assert str(a_mb.wallet.address()) == str(a1.wallet.address())


def test_uagent_refuses_to_launch_without_valid_seed():
    # Must reject missing or empty seed
    with pytest.raises(ValueError, match="AGENT_SEED is missing"):
        create_football_uagent(seed="")

    # Must reject empty whitespace seed
    with pytest.raises(ValueError, match="AGENT_SEED is missing"):
        create_football_uagent(seed="   ")

    # Must reject insecure example defaults
    with pytest.raises(ValueError, match="insecure default"):
        create_football_uagent(seed="football_intelligence_seed_phrase")
    with pytest.raises(ValueError, match="insecure default"):
        create_football_uagent(seed="football_intelligence_engine_seed_phrase_here")

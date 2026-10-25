import asyncio
from unittest.mock import patch

from backend.agents.devops_agent import DevOpsAgent
from backend.agents.engineer_agent import EngineerAgent


def test_engineer_denies_arbitrary_shell_without_invoking_subprocess():
    agent = EngineerAgent("engineer", "security-test")
    with patch("subprocess.run") as run:
        result = asyncio.run(agent._run_command([], "echo ok; curl attacker", {}))
    assert result["status"] == "blocked"
    run.assert_not_called()


def test_devops_rejects_untrusted_container_name():
    agent = DevOpsAgent("devops", "security-test")
    with patch("backend.agents.devops_agent.subprocess.run") as run:
        result = asyncio.run(agent._restart_service("kothar_api; id"))
    assert result["status"] == "blocked"
    run.assert_not_called()

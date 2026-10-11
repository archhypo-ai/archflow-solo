from pydantic import SecretStr

from archhypo_flow_agent.config import AgentSettings
from archhypo_flow_agent.providers.openrouter import create_openrouter_model


def test_factory_accepts_langchain_model_prefix() -> None:
    configuration = AgentSettings(
        openrouter_api_key=SecretStr("test-key"),
        openrouter_model="openrouter:deepseek/deepseek-v4.1-flash",
    )

    model = create_openrouter_model(configuration)

    assert model.model == "deepseek/deepseek-v4.1-flash"

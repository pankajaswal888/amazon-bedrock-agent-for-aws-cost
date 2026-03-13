from enum import StrEnum
from pathlib import PosixPath


class Sender(StrEnum):
    USER = "user"
    BOT = "assistant"
    TOOL = "tool"


CONFIG_DIR = PosixPath("~/.bedrockagent").expanduser()
WARNING_TEXT = ":material/warning: Security Alert: Never provide access to sensitive accounts or data, as malicious web content can hijack Agents's behavior"


DEFAULT_VALUES = {
    "agent_id": "",
    "agent_alias_id": "",
    "agent_id_input": "",
    "agent_alias_id_input": "",
    "provider": "claude-3-7-sonnet",
    "provider_radio": "claude-3-7-sonnet",
}

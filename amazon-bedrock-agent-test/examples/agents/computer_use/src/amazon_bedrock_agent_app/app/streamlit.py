import asyncio
import base64
from functools import partial
import logging

from typing import (
    cast,
    Dict,
)

import streamlit as st

from anthropic_local.tools import ToolResult
from anthropic.types import TextBlock, ToolUseBlock

from components import UIComponents

from error import handle_error
from helpers import validate_auth
from state_manager import StateManager
from performance_monitor import PerformanceMonitor

from constants import Sender, WARNING_TEXT
from invoke_agent_with_roc import invoke_agent_with_roc

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

import uuid

# # Initialize global instances
state_manager = StateManager()
performance_monitor = PerformanceMonitor()
ui_components = UIComponents()


async def process_messages(
    new_message: str,
    # chat_input_container: DeltaGenerator,
) -> None:
    """Process and handle messages with error handling"""
    try:
        with performance_monitor.measure_time("message_processing"):
            # Add user message
            st.session_state.messages.append(
                {
                    "role": Sender.USER,
                    "content": [TextBlock(type="text", text=new_message)],
                }
            )
            _render_message(Sender.USER, new_message)

            # Process message through sampling loop
            st.session_state.messages = await invoke_agent_with_roc(
                sessionId=st.session_state.session_id,
                messages=st.session_state.messages,
                agent_id=st.session_state.agent_id,
                agent_alias_id=st.session_state.agent_alias_id,
                inputText=new_message,
                model_id=st.session_state.provider,
                tool_use_callback=partial(_render_message, Sender.BOT),
                tool_output_callback=partial(
                    _tool_output_callback, tool_state=st.session_state.tools
                ),
                agent_response_callback=partial(_render_message, Sender.BOT),
            )
    except Exception as e:
        handle_error(e, "processing messages")


def _render_message(
    sender: Sender,
    message: str | TextBlock | ToolUseBlock | ToolResult,
) -> None:
    """Render a message with error handling"""
    try:
        is_tool_result = not isinstance(message, str) and (
            isinstance(message, ToolResult)
            or message.__class__.__name__ == "ToolResult"
        )
        if not message or (
            is_tool_result
            # and st.session_state.hide_images
            and not hasattr(message, "error")
            and not hasattr(message, "output")
        ):
            return

        with st.chat_message(sender):
            if is_tool_result:
                _render_tool_result(cast(ToolResult, message))
            elif isinstance(message, TextBlock):
                st.write(message.text)
            elif isinstance(message, ToolUseBlock):
                st.code(f"Tool Use: {message.name}\nInput: {message.input}")
            else:
                st.markdown(message)
    except Exception as e:
        handle_error(e, "rendering message")


def _render_tool_result(message: ToolResult) -> None:
    """Render tool result with error handling"""
    try:
        if message.output:
            if message.__class__.__name__ == "CLIResult":
                st.code(message.output)
            else:
                st.markdown(message.output)
        elif message.system:
            st.markdown(message.system)
        if message.error:
            st.error(message.error)
        if message.base64_image:  # and not st.session_state.hide_images:
            st.image(base64.b64decode(message.base64_image), width=100)
    except Exception as e:
        handle_error(e, "rendering tool result")


def _tool_output_callback(
    tool_output: ToolResult, tool_id: str, tool_state: Dict[str, ToolResult]
) -> None:
    """Handle tool output with error handling"""
    try:
        tool_state[tool_id] = tool_output
        _render_message(Sender.TOOL, tool_output)
    except Exception as e:
        handle_error(e, "processing tool output")


async def main():
    try:
        with performance_monitor.measure_time("main_execution"):
            st.set_page_config(page_title="Amazon Bedrock Agent Computer Use")

            # Initialize state
            state_manager.initialize_state()

            # Render UI components
            ui_components.render_header()
            st.warning(WARNING_TEXT)

            # Render sidebar
            ui_components.render_sidebar_config()
            ui_components.render_documentation()

            # Validate authentication
            if not st.session_state.auth_validated:
                if auth_error := validate_auth():
                    st.warning(
                        f"Please resolve the following auth issue:\n\n{auth_error}"
                    )
                    return
                st.session_state.auth_validated = True

            # Render existing messages
            for message in st.session_state.messages:
                if isinstance(message["content"], str):
                    _render_message(sender=message["role"], message=message["content"])
                elif isinstance(message["content"], list):
                    for block in message["content"]:
                        if isinstance(block, dict) and block["type"] == "tool_result":
                            _render_message(
                                Sender.TOOL,
                                st.session_state.tools[block["tool_use_id"]],
                            )
                        else:
                            _render_message(
                                message["role"],
                                cast(TextBlock | ToolUseBlock, block),
                            )

            # Process new message
            if new_message := st.chat_input("Do you want me to search about GenAi?"):
                with st.spinner("Running Agent..."):
                    await process_messages(new_message)

    except Exception as e:
        handle_error(e, "main application execution")


if __name__ == "__main__":
    asyncio.run(main())

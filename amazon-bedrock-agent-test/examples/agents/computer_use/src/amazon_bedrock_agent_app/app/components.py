import logging
import streamlit as st

from error import handle_error

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _reset_api_provider():
    """Reset API provider and related settings with error handling"""
    try:
        current_provider = st.session_state.provider
        new_provider = st.session_state.provider_radio

        if current_provider != new_provider:
            st.session_state.provider = new_provider
    except Exception as e:
        handle_error(e, "resetting model provider")


def _reset_agent_id():
    """Reset API provider and related settings with error handling"""

    try:
        current_id = st.session_state.agent_id
        new_id = st.session_state.agent_id_input

        if current_id != new_id:
            st.session_state.agent_id = new_id
    except Exception as e:
        handle_error(e, "resetting API provider")


def _reset_agent_alias_id():
    """Reset API provider and related settings with error handling"""

    try:
        current_alias = st.session_state.agent_alias_id
        new_alias = st.session_state.agent_alias_id_input

        if current_alias != new_alias:
            st.session_state.agent_alias_id = new_alias

    except Exception as e:
        handle_error(e, "resetting API provider")


class UIComponents:
    @staticmethod
    def render_header():
        """Render application header"""
        st.markdown(
            """
            <h3 style='
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                font-size: 1.5rem;
                font-weight: 500;
                margin-bottom: 1rem;
                margin-top: 0.5rem;
                text-align: center;
            '>
                Amazon Bedrock Agents - Computer Use
            </h3>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def render_sidebar_config():
        """Render sidebar configuration"""
        with st.sidebar:
            st.markdown("---")
            st.markdown(":material/settings: **Configuration:**")

            st.text_input(
                "Agent Id",
                key="agent_id_input",
                on_change=_reset_agent_id,
            )

            st.text_input(
                "Agent Alias Id",
                key="agent_alias_id_input",
                on_change=_reset_agent_alias_id,
            )

            # Provider selection
            provider_options = ["claude-3-5-sonnet", "claude-3-7-sonnet"]
            selected_provider = st.radio(
                "API Provider",
                options=provider_options,
                key="provider_radio",
                format_func=lambda x: x.title(),
                on_change=_reset_api_provider,
                index=provider_options.index(st.session_state.provider),
            )

            st.write(f"SessionId: {st.session_state.session_id}")

    @staticmethod
    def render_documentation():
        """Render documentation section"""
        with st.sidebar:
            st.markdown("---")
            st.markdown(":material/menu_book: **Documentation:**")
            st.markdown(
                "[Anthropic Computer Use Docs](https://docs.anthropic.com/en/docs/build-with-claude/computer-use)"
            )
            st.markdown(
                ":fire: :fire: [Anthropic Computer Use Implementation](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo)"
            )
            st.markdown(
                ":fire: [Anthropic on AWS Computer Use Implementation](https://github.com/aws-samples/anthropic-on-aws/tree/main/computer-use)"
            )

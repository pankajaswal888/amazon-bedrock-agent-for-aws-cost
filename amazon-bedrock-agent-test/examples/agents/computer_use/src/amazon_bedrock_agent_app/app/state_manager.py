import uuid
import streamlit as st
from constants import DEFAULT_VALUES


class StateManager:
    def __init__(self):
        self.default_values = DEFAULT_VALUES

    def initialize_state(self):
        """Initialize all state variables with validation"""
        # Initialize auth manager first
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())

        # Set default values with validation
        for key, value in self.default_values.items():
            if key not in st.session_state:
                st.session_state[key] = value

        # Initialize other state variables
        self._initialize_additional_state()

    def _initialize_additional_state(self):
        """Initialize additional state variables"""

        # Initialize messages and responses
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "responses" not in st.session_state:
            st.session_state.responses = {}

        # Initialize auth and tools
        if "auth_validated" not in st.session_state:
            st.session_state.auth_validated = False
        if "tools" not in st.session_state:
            st.session_state.tools = {}

    def reset_state(self):
        """Reset application state while preserving authentication"""

        st.session_state.clear()

        # Reset to default values
        for key, value in self.default_values.items():
            st.session_state[key] = value

        # Initialize empty collections
        st.session_state.messages = []
        st.session_state.responses = {}
        st.session_state.tools = {}
        st.session_state.session_id = str(uuid.uuid4())
        # st.session_state.auth_validated = False

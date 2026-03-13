from quart import Quart, request, jsonify
from anthropic_local.tools import (
    BashTool20241022,
    BashTool20250124,
    ComputerTool20241022,
    ComputerTool20250124,
    EditTool20241022,
    EditTool20250124,
    ToolCollection,
)
import asyncio
from typing import Optional, Dict, Any

app = Quart(__name__)

versions = ["20250124", "20241022"]


def get_tool_collection(version: str) -> ToolCollection:
    if version not in versions:
        raise ValueError(f"Invalid version: {version}")

    if version == "20250124":
        return ToolCollection(
            ComputerTool20250124(),
            EditTool20250124(),
            BashTool20250124(),
        )
    elif version == "20241022":
        return ToolCollection(
            ComputerTool20241022(),
            EditTool20241022(),
            BashTool20241022(),
        )


# Add request validation
def validate_request_data(data: Optional[Dict[str, Any]]) -> tuple[bool, str]:
    if not data:
        return False, "Request body is empty"
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object"
    if "tool" not in data or "input" not in data or "version" not in data:
        return False, "Missing required fields: 'tool', 'version', and 'input'"
    if (
        not isinstance(data["tool"], str)
        or not isinstance(data["input"], dict)
        or not isinstance(data["version"], str)
    ):
        return (
            False,
            "Tool must be string, version must be a string and input must be dict",
        )
    return True, ""


@app.route("/execute", methods=["POST"])
async def execute_tool():
    try:
        data = await request.get_json()

        # Validate request data
        is_valid, error_message = validate_request_data(data)
        if not is_valid:
            return jsonify({"error": error_message}), 400

        tool_name = data["tool"]
        tool_input = data["input"]
        tool_version = data["version"]

        # Get cached tool collection
        tool_collection = get_tool_collection(version=tool_version)

        # Execute tool with timeout
        try:

            result = await tool_collection.run(name=tool_name, tool_input=tool_input)
            return jsonify({"result": result.to_dict()})
        except asyncio.TimeoutError:
            return jsonify({"error": "Operation timed out"}), 504

    except Exception as e:
        # Log the error with more details
        app.logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


if __name__ == "__main__":
    # Add configuration for better performance
    app.config["JSON_SORT_KEYS"] = (
        False  # Disable JSON key sorting for better performance
    )
    app.config["PROPAGATE_EXCEPTIONS"] = True

    # Run with optimized settings
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,  # Disable debug mode in production
    )

from mcp.server import MCPServer

from math_research_workflow import differentiate_polynomial


mcp = MCPServer("guarded-math-tools")


@mcp.tool()
def differentiate(expression: str) -> dict[str, str]:
    """Differentiate a polynomial in x after applying local safety checks."""
    try:
        derivative = differentiate_polynomial(expression)
    except ValueError as error:
        return {
            "status": "rejected",
            "expression": expression,
            "message": str(error),
        }

    return {
        "status": "success",
        "expression": expression,
        "derivative": derivative,
    }

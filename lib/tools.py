from langchain_core.tools import tool

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers.
    Args:
        a: first int
        b: second int
    """
    print(f"Tool called..multiply {a} and {b}")
    return (a * b)

@tool
def divide(a: int, b: int) -> int:
    """Divide two numbers."""
    print(f"Tool called..divide {a} by {b}")
    return a / b

@tool
def HowIsWeather() -> str:
    """Get the Weather."""
    print(f"Tool called..Weather")
    return "Good Weather"

tools = [multiply, divide, HowIsWeather]
tool_functions = {
    "multiply": multiply,
    "divide": divide,
    "HowIsWeather": HowIsWeather,
}

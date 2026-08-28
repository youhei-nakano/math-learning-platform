import json

from openai import OpenAI

client = OpenAI()

def add_numbers(a, b):

    return a + b

tools = [
    {
        "type": "function",
        "name": "add_numbers",
        "description": "2つの数を足し算する",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "1つ目の数",
                },
                "b": {
                    "type": "number",
                    "description": "2つ目の数",
                },
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        },
        "strict": True,
    }
]

response = client.responses.create(
    model="gpt-4.1-mini",
    input="12と30を足してください",
    tools=tools,
)

tool_call = response.output[0]
arguments = json.loads(tool_call.arguments)
result = add_numbers(**arguments)

final_response = client.responses.create(
    model="gpt-4.1-mini",
    previous_response_id=response.id,
    input=[
        {
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": str(result),
        }
    ],
)

print(final_response.output_text)
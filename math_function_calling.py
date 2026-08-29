import json
import re

import sympy
from openai import OpenAI


MAX_EXPRESSION_LENGTH = 200


def differentiate_polynomial(expression):
    if not expression or len(expression) > MAX_EXPRESSION_LENGTH:
        raise ValueError("式は1〜200文字で入力してください。")

    allowed_pattern = r"[0-9x+\-*/^().\s]+"
    if not re.fullmatch(allowed_pattern, expression):
        raise ValueError(
            "式には数字、x、四則演算、べき乗、括弧だけを使用してください。"
        )

    x = sympy.Symbol("x")
    parsed_expression = sympy.sympify(
        expression.replace("^", "**"),
        locals={"x": x},
    )

    if not parsed_expression.free_symbols.issubset({x}):
        raise ValueError("使用できる変数はxだけです。")

    derivative = sympy.diff(parsed_expression, x)
    return str(derivative)


client = OpenAI()

tools = [
    {
        "type": "function",
        "name": "differentiate_polynomial",
        "description": "多項式をxについて記号的に微分する",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "xを変数とする多項式。例: x^3 + 2*x",
                }
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
        "strict": True,
    }
]

user_input = input("微分したい式を含む質問を入力してください: ")

response = client.responses.create(
    model="gpt-4.1-mini",
    input=user_input,
    tools=tools,
    tool_choice="required",
)

tool_call = next(
    (
        item
        for item in response.output
        if item.type == "function_call"
        and item.name == "differentiate_polynomial"
    ),
    None,
)

if tool_call is None:
    print(response.output_text)
    raise SystemExit

arguments = json.loads(tool_call.arguments)

try:
    result = differentiate_polynomial(**arguments)
except (ValueError, TypeError, sympy.SympifyError) as error:
    print("計算結果:")
    print(f"このツールでは計算できません: {error}")
    raise SystemExit

final_response = client.responses.create(
    model="gpt-4.1-mini",
    previous_response_id=response.id,
    input=[
        {
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": result,
        }
    ],
)

print("計算結果:")
print(final_response.output_text)

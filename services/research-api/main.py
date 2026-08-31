from openai import OpenAI

from openai_config import GENERATION_MODEL

client = OpenAI()

response = client.responses.create(model=GENERATION_MODEL, input="こんにちは")

print(response.output_text)

from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

load_dotenv(find_dotenv())

client = OpenAI()

response = client.responses.create(
    model="gpt-4.1-mini",
    tools=[
        {
            "type": "web_search_preview",
            "search_context_size": "low",
            "user_location": {
                "type": "approximate",
                "country": "US",
            }
        }
    ],
    input="What was a positive news story from today?"
)


output_text = response.output_text
annotations = response.output[-1].content[0].annotations

print(f"Output: {output_text}")
for citation in annotations:
    print(f"{citation.url} - {citation.title}")

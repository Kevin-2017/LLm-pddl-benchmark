import anthropic
import os

client = anthropic.Anthropic(
    api_key = os.environ["ANTHROPIC_API_KEY"]
)
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, Claude"}
    ]
)

# claude-3-5-sonnet-20241022
# claude-3-5-haiku-20241022

print(message.content[0].text)
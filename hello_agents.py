from autogen_ext.models.anthropic import AnthropicChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from dotenv import load_dotenv
import asyncio
import os

# Load environment variables from .env file
load_dotenv()

# Create the model client
model_client = AnthropicChatCompletionClient(
    model="claude-3-5-sonnet-20240620", api_key=os.getenv("ANTHROPIC_API_KEY")
)

# Create assistant agent
assistant = AssistantAgent(
    "assistant",
    model_client=model_client,
    description="An AI assistant that helps with creative writing",
)


# Run a simple conversation
async def main():
    # Send a message to the assistant
    response = await assistant.on_messages(
        [TextMessage(content="Write a haiku about sailing.", source="user")],
        CancellationToken(),
    )

    # Print the response
    print("Assistant's response:")
    print(response.chat_message.content)


if __name__ == "__main__":
    asyncio.run(main())

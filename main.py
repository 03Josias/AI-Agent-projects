from openai import OpenAI
from dotenv import load_dotenv
from agent import ProjectAgent
import sys

load_dotenv()

client = OpenAI()
agent = ProjectAgent()

print("Project Agent listo (escribe 'salir' para terminar)")

def format_user_message(text):
    return {
        "role": "user",
        "content": [
            {"type": "input_text", "text": text}
        ]
    }

while True:
    try:
        user_input = input("Tú: ").strip()

        if user_input.lower() in ("salir", "exit"):
            print(" Hasta luego")
            break

        agent.messages.append(format_user_message(user_input))

        while True:
            response = client.responses.create(
                model="gpt-4o-mini",
                input=agent.messages,
                tools=agent.tools,
                tool_choice="auto"
            )

            called_tool = agent.process_response(response)
            if not called_tool:
                break

        if len(agent.messages) > 20:
            agent.messages = agent.messages[:1] + agent.messages[-10:]

    except Exception as e:
        print(f" Error: {e}")

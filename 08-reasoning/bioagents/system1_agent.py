from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
import time
from openai import OpenAI

class System1Agent:
    def __init__(self):
        self.client = OpenAI()

    def chat(self, message: str) -> str:
        start_time = time.time()
        response = self.client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message},
            ],
        )
        end_time = time.time()
        print(f"Time taken: {end_time - start_time: .2f} seconds")

        return response.choices[0].message.content

#-----------------------
# smoke test
#-----------------------

if __name__ == "__main__":
    agent = System1Agent()
    query = "What is the capital of the moon?"
    print(f"Starting query: {query}")
    while query.strip() != "":
        response = agent.chat(query)
        print(f"Agent: {response}")
        query = input("Enter query again: ")





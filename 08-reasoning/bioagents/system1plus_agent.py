from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
import time
from openai import OpenAI

PROMPT_TEMPLATE = """
You are a helpful assistant.

You are given a question and you need to answer it carefully.

Before you answer the question, make sure that you expand the user query
into a more detailed and comprehensive question in case it has 
missing information or has tricky language.

You need to answer the question in a way that is helpful and informative.

Here is the user query:

{user_query}

Your response should be in the following format:

Question: <expanded question>
Answer: <answer>
"""

class System1plusAgent:
    def __init__(self):
        self.client = OpenAI()

    def chat(self, message: str) -> str:
        start_time = time.time()
        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": PROMPT_TEMPLATE.format(user_query=message)},
            ],
        )
        end_time = time.time()
        print(f"Time taken: {end_time - start_time: .2f} seconds")

        return response.choices[0].message.content

#-----------------------
# smoke test
#-----------------------

if __name__ == "__main__":
    agent = System1plusAgent()
    query = "What is the capital of the moon?"
    print(f"Starting query: {query}")
    while query.strip() != "":
        response = agent.chat(query)
        print(f"Agent: {response}")
        query = input("Enter query again: ")





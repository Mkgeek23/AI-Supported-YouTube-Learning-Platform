# Create an API key (https://studio.nebius.com/settings/api-keys)
# and save it into the NEBIUS_API_KEY environment variable.

# Create a `.env` file in your project root:
# NEBIUS_API_KEY=your-api-key-here

# Use the code below to continue working with your model,
# its parameters and the chat so far in your application.

import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

client = OpenAI(
    base_url="https://api.studio.nebius.com/v1/",
    api_key=os.environ.get("NEBIUS_API_KEY")
)


def call_nebius_llm(model="nvidia/Nemotron-3-Nano-Omni", prompt=""):
    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=8192,
            temperature=0.7, # TODO: put value according to the lesson
            top_p=0.9, # TODO: put value according to the lesson
            extra_body={
                "top_k": 50
            },
            messages=[
                {"role": "user",
                 "content": prompt
                }
            ]
        )
        result = response.to_json()
        return result

    except Exception as e:
        print(f"Error making API call: {e}")
        return None


def gen_spec():
    model =  "nvidia/Nemotron-3-Nano-Omni" # TODO: try different models
    prompt = """You are a senior python developer working for company which creates a Learning Platform. Create some specification for Learning Platform""" # TODO: try to change the prompt (use triple quotes """ for multi-line text)

    response = call_nebius_llm(model=model, prompt=prompt)
    if response:
        response_dict = json.loads(response)
        # Extract content from the response
        content = response_dict['choices'][0]['message']['content']

        # Write content to a file
        with open('student_specification.md', 'w', encoding='utf-8') as f:
            f.write(content)

        print("Content has been written to student_specification.md")


if __name__ == "__main__":
    gen_spec()

import json
from typing import Generator
from openai import OpenAI
from knowledge_store import MarqoKnowledgeStore
import os
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY is not set in the .env file.")

client = OpenAI(api_key=API_KEY)

def answer(user_input: str, mks: MarqoKnowledgeStore, limit: int = 5) -> Generator[str, None, None]:
    """
    Generate an answer using OpenAI GPT model and Marqo Knowledge Store.

    Args:
        user_input (str): User's query.
        mks (MarqoKnowledgeStore): Marqo Knowledge Store for querying context.
        limit (int): Maximum number of context entries to retrieve.

    Yields:
        Generator[str, None, None]: Streamed response chunks.
    """


    context = mks.query_for_content(user_input, "text", limit)

    if context:

        sources = "\n".join(f"[{i+1}] {source}" for i, source in enumerate(context))
    else:
        sources = "No relevant context found from the knowledge base."

    print(f"QUERY: {user_input}")
    print("Context from Marqo:", json.dumps(context, indent=4) if context else "No context found.")


    if context:
        prompt = f"""
        You are a helpful academic advisor for Towson University's Computer & Information Sciences (CIS) department.

        Use the following official information to accurately answer the question:

        Context:
        {sources}

        Question: {user_input}
        Answer:
        """
    else:
        prompt = f"""
        You are a helpful academic advisor for Towson University's Computer & Information Sciences (CIS) department.

        Unfortunately, I don't have official information on this topic in the current knowledge base. 
        Please recommend that the user consult the official Towson University course catalog or contact the department directly.

        Question: {user_input}
        Answer:
        """

    try:
 
        response = client.chat.completions.create(
            model="gpt-4",  
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )

        # Stream the response
        for chunk in response:
            if chunk.choices:
                delta_content = chunk.choices[0].delta.get("content", "")
                if delta_content:
                    yield delta_content
    except Exception as e:
        print(f"Error generating response: {e}")
        yield f"Error generating response: {e}"

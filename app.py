from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os
import getpass
from dotenv import load_dotenv
from langchain_openai import OpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import ConversationChain
import json



# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
# Dynamically prompt for OpenAI API key if not set
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OpenAI API key: ")

# Initialize the Flask app
app = Flask(__name__)
CORS(app)

# Define the system prompt
system_prompt = (
    "You are a CIS Advising Assistant for Towson University. "
    "Your job is to provide accurate and concise information about CIS courses, prerequisites, and general advising. "
    "If a question is unrelated to Towson University or its CIS department, politely inform the user. "
    "Focus on being helpful, factual, and student-friendly. "
    "If you don't have accurate and factual information about Towson University, say you do not know and advise the user to contact an advisor."
)

# Initialize OpenAI LLM
llm = OpenAI(temperature=0.7, openai_api_key=openai_api_key)

# Initialize memory for multi-turn conversations
memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=100)
conversation_chain = ConversationChain(llm=llm, memory=memory)

# Load course information from JSON file (if necessary)
course_info_file = "towson_course_info.json"
if os.path.exists(course_info_file):
    with open(course_info_file, "r") as file:
        course_info = json.load(file)
else:
    course_info = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['POST'])
def get_data():
    try:
        # Get user input from the request
        data = request.get_json()
        user_input = data.get('data', '').strip()

        # Check if the input contains a specific course code
        course_code = next(
            (word for word in user_input.upper().split() if word in course_info), None
        )

        # If a course code is found, return course information
        if course_code:
            course_details = course_info[course_code]
            response_message = (
                f"Course Code: {course_code}\n"
                f"Title: {course_details.get('title', 'N/A')}\n"
                f"Description: {course_details.get('description', 'N/A')}\n"
                f"Prerequisite: {course_details.get('prerequisite', 'None')}"
            )
            return jsonify({"response": True, "message": response_message})

        # Otherwise, process the query using the OpenAI assistant
        prompt_with_system_message = f"{system_prompt}\nUser: {user_input}"
        output = conversation_chain.predict(input=prompt_with_system_message)
        memory.save_context({"input": user_input}, {"output": output})

        return jsonify({"response": True, "message": output})

    except Exception as e:
        # Log the error and return a user-friendly message
        print(f"Error: {e}")
        return jsonify({"response": False, "message": f"An error occurred: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True, port=5001)

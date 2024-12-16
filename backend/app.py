from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from knowledge_store import MarqoKnowledgeStore, WebScraper
import marqo
from openai import OpenAI
import json


# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path)

# Verify API Key
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API_KEY is not loaded. Check your .env file location and content.")

print(f"Loaded API Key: {api_key[:5]}...")

openai_client = OpenAI(api_key=api_key)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Knowledge Store Configuration
INDEX_NAME = "knowledge-management"
MARQO_CLIENT_URL = "http://localhost:8882"

WEBPAGES = [
    "https://catalog.towson.edu/graduate/course-descriptions/cosc/",
    "https://catalog.towson.edu/undergraduate/course-descriptions/cosc/",
    "https://catalog.towson.edu/undergraduate/fisher-science-mathematics/computer-information-sciences/computer-science/",
    "https://catalog.towson.edu/undergraduate/fisher-science-mathematics/computer-information-sciences/computer-science/#fouryearplanofstudytext",
    "https://catalog.towson.edu/graduate/degree-certificate-programs/jess-mildred-fisher-science-mathematics/computer-science-ms/#requirementstext",
    "https://catalog.towson.edu/graduate/degree-certificate-programs/jess-mildred-fisher-science-mathematics/computer-science-ms/#text"
]
GRADUATE_COURSES_PATH = "./full_graduate_course.json"
UNDERGRADUATE_COURSES_PATH = "./full_undergrad_course.json"


# Initialize Marqo client and knowledge store
marqo_client = marqo.Client(MARQO_CLIENT_URL)
MKS = MarqoKnowledgeStore(marqo_client, INDEX_NAME)
scraper = WebScraper(WEBPAGES)

# Ensure index exists
def initialize_index():
    try:
        marqo_client.index(INDEX_NAME).get_settings()
        print(f"Index '{INDEX_NAME}' already exists.")
    except Exception:
        print(f"Creating index '{INDEX_NAME}'...")
        marqo_client.create_index(index_name=INDEX_NAME, **{
            "model": "hf/all_datasets_v4_MiniLM-L6",
            "text_preprocessing": {
                "split_length": 5,  
                "split_overlap": 2,
                "split_method": "sentence"
            },
            "score_cutoff": 0.5  
        })

initialize_index()


def load_json_data(filepath):
    try:
        with open(filepath, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading JSON file {filepath}: {e}")
        return []

# Load graduate and undergraduate course data
graduate_courses = load_json_data(GRADUATE_COURSES_PATH)
undergraduate_courses = load_json_data(UNDERGRADUATE_COURSES_PATH)

@app.route("/initializeKnowledge", methods=["POST"])
def initialize_knowledge():
    """Load course data from JSON files and populate the Marqo index."""
    try:
        print("Initializing knowledge from JSON files...")

        # Index graduate courses
        for course in graduate_courses:
            course_text = f"{course['title']}: {course['description']}"
            MKS.add_document(course_text)

        # Index undergraduate courses
        for course in undergraduate_courses:
            course_text = f"{course['title']}: {course['description']}"
            MKS.add_document(course_text)

        print("Knowledge index successfully populated with JSON data.")
        return jsonify({"message": "Knowledge index initialized with JSON data"})
    except Exception as e:
        print(f"Error during initialization: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/chatbot", methods=["POST"])
def chatbot():
    """Dynamic chatbot using OpenAI with Marqo knowledge."""
    data = request.get_json()
    user_input = data.get("message", "")

    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Fetch context from knowledge store
        raw_context = MKS.query_for_content(user_input, "text", limit=5)
        print(f"Raw context: {raw_context}")

        cleaned_context = [entry[:500] for entry in raw_context] if raw_context else []

        # Construct OpenAI input
        system_message = (
            "You are a helpful academic advisor for Towson University's CIS department.\n"
            f"Here is some relevant knowledge to help answer the query:\n\n{''.join(cleaned_context)}"
            if cleaned_context else "You are a helpful advisor for Towson University's CIS department."
        )

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ]
        )

        assistant_message = response.choices[0].message.content
        print(f"Assistant response: {assistant_message}")

        return jsonify({"response": assistant_message})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/getKnowledge", methods=["POST"])
def get_knowledge():
    """Retrieve and clean knowledge from Marqo."""
    data = request.get_json()
    q = data.get("q", "")
    limit = data.get("limit", 5)

    if not q:
        return jsonify({"error": "Query string 'q' is required"}), 400

    try:
        raw_context = MKS.query_for_content(q, "text", limit)
        cleaned_context = [entry[:500] for entry in raw_context] if raw_context else ["No relevant content found."]
        return jsonify({"context": cleaned_context})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/debugIndex", methods=["GET"])
def debug_index():
    """Debug the contents of the Marqo index."""
    try:
        response = marqo_client.index(INDEX_NAME).search("any test query", limit=5)
        print("Index contents:", response) 
        return jsonify(response)  
    except Exception as e:
        print(f"Error fetching index contents: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/testIndex', methods=['GET'])
def test_index():
    response = marqo_client.index(INDEX_NAME).search("any test query", limit=5)
    print("Index contents:", response)
    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True)

<<<<<<< HEAD
# COSC601Proj
=======
### Frontend

Installs the necessary Node.js packages for the frontend project and then start the development server. This will be at http://localhost:3000.
```
cd frontend
npm i
npm run dev
```

### Backend

#### 1. Install Dependencies
Next, navigate to the backend directory, create a virtual environment, activate it, and install the required Python packages listed in the [requirements.txt](/backend/requirements.txt) file.

```
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

To run this project, you'll need download NLTK (Natural Language Toolkit) data because the [`document_processors.py`](/backend/document_processors.py) script uses NLTK's sentence tokenization functionality. Specifically, the `sentence_chunker` and `sentence_pair_chunker` functions rely on NLTK's sent_tokenize method to split text into sentences.

Specify Python interpreter:
```
python3
```
Import NLTK:
```python
import nltk
nltk.download("all")
```

#### 2. Run Marqo
Use docker to run Marqo:

```bash
docker rm -f marqo
docker pull marqoai/marqo:latest
docker run --name marqo -it -p 8882:8882 marqoai/marqo:latest
```


#### 3. Run the Web Server
Starts a Flask development server in debug mode on port 5001 using Python 3:
```
python -m flask run --debug -p 5001
```

Navigate to http://localhost:3000


## Specifications
This can run locally on an M1 or M2 Mac or with a CUDA capable GPU on Linux or Windows.
>>>>>>> 36fcf20 (Initial commit for NewFinalProject)

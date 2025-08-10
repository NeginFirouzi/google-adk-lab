# google-adk-lab

## Setup and Installation

Follow the steps below to set up and run the project locally.

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows use: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create a .env file in the project root

Make sure you have a .env file at the root of the project with your configuration variables (GEMINI_API_KEY="your_API_key", OPENAI_API_KEY).

### 4. Run the agent with Google ADK Web

```bash
adk web
```

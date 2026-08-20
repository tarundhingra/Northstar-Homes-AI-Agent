# Northstar Homes — AI Sales Agent

A conversational AI sales assistant named Zara built for Northstar One, a residential development in Sector 79, Gurugram. The agent conducts lead qualification, speaks English/Hindi/Hinglish, and seamlessly manages site-visit bookings. 

## How to Run the Bot

### Prerequisites
- Python 3.10+
- `uv` installed (for lightning-fast virtual environments and package management). If you don't have it, run `pip install uv`.
- A Google Gemini API Key.

### Setup Instructions

1. **Clone the repository:** 
   ```bash
   git clone <your-repo-url>
   cd <your-repo-folder>
Set up the virtual environment:
We use uv for fast environment creation.

Bash
uv venv
Activate the virtual environment:

On macOS/Linux: source .venv/bin/activate

On Windows: .venv\Scripts\activate

Install dependencies:

Bash
uv pip install -r requirements.txt
Environment Variables:
Copy the example environment file and add your actual API key.

Bash
cp .env.example .env
Open .env and set:
GEMINI_API_KEY=your_actual_api_key_here

Start the Backend:
Run the FastAPI server using Uvicorn.

Bash
uvicorn main:app --reload --port 8000
Start the Frontend:
Open a new terminal window, activate the virtual environment again, and launch Streamlit:

Bash
streamlit run streamlit_app.py

Key Assumptions
Project Scope: The agent is strictly constrained to representing Northstar One (2 BHK & 3 BHK). It is explicitly instructed via the system prompt to never hallucinate pricing, possession dates, or amenities outside the provided ground truth.

Lexical/Semantic Routing: We assume users will mix languages (Hinglish/Hindi) and phrase requests unpredictably. Instead of brittle keyword matching, the backend uses a secondary zero-shot LLM call to classify "booking intent," ensuring that natural phrases like "main kal dekhne aana chahta hun" successfully trigger the booking system.

In-Memory Storage: For the scope of this assignment, conversation history and booking states are stored in-memory rather than relying on an external database.

Known Limitations
State Persistence: Because sessions are stored in-memory, restarting the Uvicorn server will wipe all active chat histories.

Booking System: The site visit mechanism is a mock function with a simulated 15% failure rate to demonstrate edge-case handling and error recovery. It does not integrate with a real CRM.

AI Tools Used
Google Gemini API (gemini-3.5-flash) powers the core conversational engine, the semantic intent detector, and the post-conversation analytics extraction.

AI Coding Assistants were utilized to help structure the FastAPI boilerplate and refine the Markdown formatting.
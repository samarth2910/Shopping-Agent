# 🛍️ Shopping Agent — Agentic AI Project

An **agentic AI** shopping assistant that autonomously plans, reasons, and executes multi-step tasks — searching products, checking inventory, reading reviews, and placing orders — all from a single natural language or image input.

Built using a **LangChain agent** with custom tools that the AI decides when and how to use, making it a true agentic system rather than a simple chatbot.

## 📸 Demo

![AI Shopping Assistant](https://github.com/samarth2910/Shopping-Agent/blob/master/assets/demo%20(2).png)

## 🤖 Built With

- **LangChain** — Agentic framework with custom tools & reasoning loop
- **Groq** — Fast LLM inference powering the agent
- **Streamlit** — Chat UI
- **SQLite** — Local product & reviews database

## ✨ Features

- 🤖 Agentic reasoning — AI autonomously decides which tools to use
- 🔍 Natural language product search
- 🖼️ Image-based product search
- ⭐ Product ratings & reviews
- 📦 Real-time inventory checking
- 🛒 Autonomous order placement
- ⚡ Fast responses powered by Groq

## 🧠 How It Works (Agentic Loop)

```
User Input → LangChain Agent → Decides which tool(s) to call
                ↓
    [search_products] [check_inventory] [get_reviews] [place_order]
                ↓
         Final Response to User
```

The agent autonomously chains multiple tools together to complete complex tasks — no hardcoded logic.

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/samarth2910/Shopping-Agent.git
cd Shopping-Agent
```

### 2. Install dependencies
```bash
uv sync
# or
pip install -r requirements.txt
```

### 3. Set up environment variables
Create a `.env` file:
```
GROQ_API_KEY=your_groq_api_key
```

### 4. Set up the database
```bash
python setup_db.py
```

### 5. Run the app
```bash
streamlit run app.py
```

## 📁 Project Structure

```
Shopping-Agent/
├── app.py              # Streamlit UI
├── shopping_agent.py   # LangChain agent & tools
├── reviews_api.py      # Product reviews API
├── setup_db.py         # Database setup
├── resources/          # Sample images for image search
└── requirements.txt
```

## 🔑 API Keys

- Get your free Groq API key at [console.groq.com](https://console.groq.com)

# 🛍️ Shopping Agent

An AI-powered shopping assistant that helps users find products, check inventory, and read reviews using natural language and image search.

## 📸 Demo

![AI Shopping Assistant](assets/demo_(2).png)

## 🤖 Built With

- **LangChain** — Agent framework with custom tools
- **Groq** — Fast LLM inference
- **Streamlit** — Chat UI
- **SQLite** — Local product & reviews database

## ✨ Features

- 🔍 Natural language product search
- 🖼️ Image-based product search
- ⭐ Product ratings & reviews
- 📦 Real-time inventory checking
- ⚡ Fast responses powered by Groq

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

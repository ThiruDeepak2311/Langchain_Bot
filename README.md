# 🤖 KnowledgeGPT: Your Personal AI Knowledge Assistant

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Powered-orange)](https://github.com/langchain-ai/langgraph)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MLflow](https://img.shields.io/badge/MLflow-Tracking-blue)](https://mlflow.org/)

A powerful yet simple Python chatbot that can answer questions using Wikipedia and knowledge sources. Built for learning and customization - no UI required!

## ✨ Features

- 🔍 Retrieves information from Wikipedia and structured knowledge bases
- 🧠 Maintains conversation context for natural follow-up questions
- 📊 Tracks performance with MLflow for continuous improvement
- 🌐 Extensible architecture - easily add new knowledge sources
- 💬 Conversation flow management with LangGraph
- 🔄 Supports context-aware personalized responses

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/knowledgegpt.git
cd knowledgegpt

# Set up environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the chatbot
python chatbot.py
```

## 📖 Usage Example

```python
from knowledgegpt import ChatBot

# Create a new chatbot instance
bot = ChatBot()

# Start a conversation
response = bot.chat("Who was Albert Einstein?")
print(response)

# Ask a follow-up question
response = bot.chat("What were his major contributions?")
print(response)
```

## 🏗️ Architecture

```
User Query → Conversation Manager → Knowledge Retrieval → Response Generation → User
     ↑                                      ↓
     └──────────── Conversation Memory ─────┘
```

## 🔮 Future Enhancements

- [ ] Add support for custom document knowledge bases
- [ ] Implement advanced retrieval techniques
- [ ] Create CLI interface for easier interaction
- [ ] Add voice interaction capabilities

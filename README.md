# Travelmate BD – Regional Tourism Chatbot

Travelmate BD is an AI-driven regional tourism assistant built to help users plan trips across Bangladesh. The application integrates a multilingual conversational interface, an automated tour budget estimator, a document-based Q&A engine, and a real-time system performance monitor into a unified Gradio dashboard.

This project was developed for **CSE 299: Junior Design Project (Spring 2025)** at North South University under the supervision of **Dr. Shafin Rahman**.

---

## Technical Overview

* **Multilingual Chatbot:** Powered by `deepseek-ai/deepseek-llm-7b-base` to answer travel and regional queries in Bangla and English.
* **Document Q&A System:** Leverages ChromaDB and sentence transformers to extract context-aware insights from uploaded PDF and DOCX files.
* **Tour Budget Calculator:** Algorithmic expense estimation based on transport mode, accommodation tier, and dining preferences.
* **System Monitor:** Uses `psutil` to track runtime memory consumption and response latency.

---

## Repository Structure

```text
Regional-Travelmate-Chatbot/
├── app.py                   # Main Gradio application entry point
├── colab_setup.py           # Dependency installation script for Google Colab
├── core_utils.py            # Model loading & document processing modules
├── performance_analyzer.py # Memory and latency profiling utilities
├── tour_budget.py           # Expense calculation logic
├── requirements.txt         # Project dependencies
└── .env.example             # Environment variable template

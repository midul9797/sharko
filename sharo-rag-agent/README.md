---
title: Sharo Rag Agent
emoji: 🌍
colorFrom: pink
colorTo: red
sdk: docker
pinned: false
short_description: An AI assistant to assist in sharko project
---

This Space serves a Retrieval-Augmented Generation (RAG) API using FastAPI.

**API Endpoint:** `/ask`

Send a POST request with a JSON body like:

```json
{
  "contex": ["q1": "What is Gemini?","a1": "A LLM" ],
  "question": "What is a LLM?"

}

```

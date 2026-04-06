---
title: Autonomous Multi-Agent Debate API
emoji: ⚖️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 7860
---

# Autonomous Web-Scraping Debate Arena

This is the backend API for the Multi-Agent Debate Arena. 
It utilizes FastAPI, CrewAI, Pinecone (Vector DB), and Serper API to orchestrate autonomous research and debate between AI agents.

## Architecture
* **FastAPI:** Handles Server-Sent Events (SSE) streaming.
* **CrewAI:** Orchestrates the Architect, Risk Director, and CTO agents.
* **RAG & Search:** Agents are equipped with Pinecone memory and live Google Search (Serper API).
# 🤖 DocuMind AI - Intelligent Document Processing System

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![PostgreSQL](https://img.shields.io/badge/postgresql-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)
![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)
![Celery](https://img.shields.io/badge/celery-%23a9cc54.svg?style=for-the-badge&logo=celery&logoColor=ddf4a4)

</div>

## 🚀 Overview

DocuMind AI is a cutting-edge document processing and intelligent Q&A system that leverages advanced AI technologies to extract, analyze, and provide insights from your documents. Built with enterprise-grade architecture and modern web technologies.

### ✨ Key Features

- 🔍 **Intelligent Document Analysis** - AI-powered extraction and processing
- 💬 **Smart Q&A System** - Ask questions about your documents using natural language
- 🎯 **Multiple AI Engines** - Support for LangChain, OpenAI Direct, and more
- 🔐 **Secure Authentication** - JWT-based user authentication and authorization
- 📊 **Real-time Processing** - Asynchronous document processing with Celery
- 🎨 **Modern UI** - Responsive React frontend with intuitive design
- 🐳 **Docker Ready** - Fully containerized for easy deployment
- 📈 **Production Ready** - Scalable architecture with nginx load balancing

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │────│  Nginx Proxy    │────│  FastAPI Backend│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                               ┌────────────────────────┼────────────────────────┐
                               │                        │                        │
                    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                    │   PostgreSQL    │    │     Redis       │    │  Celery Workers │
                    │    Database     │    │   Cache/Queue   │    │   Background    │
                    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **PostgreSQL** - Robust relational database
- **SQLAlchemy** - Python SQL toolkit and ORM
- **Alembic** - Database migration tool
- **Celery** - Distributed task queue
- **Redis** - In-memory data structure store

### Frontend
- **React** - Modern JavaScript library for building user interfaces
- **Vite** - Fast build tool and development server
- **Axios** - Promise-based HTTP client

### AI & ML
- **OpenAI GPT** - Advanced language model for document analysis
- **LangChain** - Framework for developing LLM applications
- **Vector Embeddings** - Semantic search and retrieval

### DevOps & Deployment
- **Docker** - Containerization platform
- **Docker Compose** - Multi-container application orchestration
- **Nginx** - High-performance web server and reverse proxy

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API Key

### Development Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd doc-proc

# Start development environment
docker-compose up --build
```

### Production Deployment
```bash
# Start production environment
docker-compose -f docker-compose.prod.yml up --build -d
```

## 🔧 Configuration

Create a `.env` file with your configuration:

```env
# Database
POSTGRES_DB=docuai
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password

# AI Configuration
OPENAI_API_KEY=your_openai_api_key

# Security
JWT_SECRET_KEY=your_jwt_secret_key
```

## 📱 Features Showcase

- **Document Upload & Processing** - Support for PDF, DOC, TXT files
- **AI-Powered Analysis** - Intelligent content extraction and summarization
- **Semantic Search** - Find relevant information across all documents
- **Question Answering** - Natural language queries with contextual responses
- **User Management** - Secure authentication and personal document libraries
- **Real-time Updates** - Live processing status and notifications

## 🎯 Use Cases

- **Legal Document Review** - Analyze contracts and legal documents
- **Research & Academia** - Process research papers and academic content
- **Business Intelligence** - Extract insights from business documents
- **Content Management** - Organize and search through large document collections

## 🤝 Professional Services

This project demonstrates expertise in:
- Modern full-stack web development
- AI/ML integration and deployment
- Enterprise-grade architecture design
- Docker containerization and DevOps
- Database design and optimization
- API development and documentation

---

<div align="center">

**Built with ❤️ for intelligent document processing**

*Ready for production deployment on AWS, GCP, or Azure*

</div>

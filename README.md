# ECE 461 – Trustworthy Model Registry

A command-line interface and web frontend for evaluating and managing ML models, datasets, and codebases from HuggingFace, GitHub, and other sources. This project assesses artifacts against multiple quality metrics to determine their suitability for production use.

## Overview

The Trustworthy Model Registry provides:

- **CLI Backend**: A Python-based backend that fetches and evaluates LLMs, datasets, and codebases
- **REST API**: RESTful endpoints to query, search, and analyze artifacts
- **Web Frontend**: A modern React + TypeScript UI for browsing, searching, and analyzing artifacts
- **Quality Metrics**: Multiple evaluation criteria including:
  - Model size and performance
  - License compliance
  - Cost analysis
  - Dependency lineage
  - Health and availability status

## Project Structure

```
ECE-30861-Phase2-24/
├── README.md                    # This file
├── frontend/                    # React + TypeScript + Vite frontend
│   ├── src/
│   │   ├── app/               # Theme and query client setup
│   │   ├── api/               # FastAPI client and registry service functions
│   │   ├── components/        # Reusable UI components
│   │   └── page.tsx
│   ├── package.json
├── src/                        # Python backend implementation
    ├── api/                    # FastAPI endpoints
    ├── ...                     # Metric implementations
```

## Quick Start

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# IF USING CLI: Run the CLI
./run [command]

# IF RUNNING API SERVICE
cd src
python -m uvicorn api.main:app --reload

```

### Frontend

```powershell
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will open at `http://localhost:3000`.

## Key Features

### CI/CD Pipeline (Grading Criterion)
**Features:**
- Implemented with Github Actions
- Python linting and unit tests via pytest
- Automatic execution on pull requests and pushes to main
- Package FastAPI backend
- Deploy to AWS EC2 using SSH and environment secrets
- Deploy frontend to Vercel (automatic)

Relevant file:
```.github/workflows/deploy.yml```

### LLM Integration

- Used throughout development (Copilot, ChatGPT, CLAUDE, etc...)
- Used to analyze READMEs in ```src/performance_claims.py```

### CLI Features
- Evaluate models from HuggingFace
- Analyze datasets for quality and size
- Inspect GitHub repositories for code metrics
- Score artifacts against multiple criteria

### Frontend Features
- **Artifact CRUD**: Create, read, update, and delete models, datasets, and code artifacts
- **Search**: Find artifacts by name or regex pattern
- **Analysis Tools**:
  - Model rating and performance metrics
  - Cost analysis with dependency tracking
  - Lineage visualization
  - License compliance checking
- **Health Monitoring**: Real-time component status and system metrics

### API Endpoints

Core endpoints provided by the backend:

- `PUT /authenticate` – User login
- `GET /health` – System health status
- `GET /health/components` – Detailed component health
- `POST /artifacts` – List artifacts with pagination
- `POST /artifact/{type}` – Create new artifact
- `GET/PUT/DELETE /artifacts/{type}/{id}` – Artifact CRUD operations
- `GET /artifact/byName/{name}` – Search by name
- `POST /artifact/byRegEx` – Search by regex pattern
- `GET /artifact/model/{id}/rate` – Get model rating
- `GET /artifact/{type}/{id}/cost` – Calculate artifact cost
- `GET /artifact/model/{id}/lineage` – Trace artifact dependencies
- `POST /artifact/model/{id}/license-check` – Verify license compliance
- `GET /tracks` – List planned feature tracks
- `DELETE /reset` – Reset registry (admin only)

## Testing

### Frontend and Backend Tests

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## Development

### Prerequisites

- **Node.js** 16+ (frontend)
- **Python** 3.9+ (backend)
- **npm** or **yarn** (frontend package manager)
- **Chrome/Chromedriver** (for frontend tests)

## Architecture

### Frontend Architecture

- **State Management**: React Query for server state
- **HTTP Client**: Axios with automatic authorization header injection
- **UI Framework**: Material-UI (MUI) with custom dark theme
- **Build Tool**: Vite
- **Authentication**: Token-based (localStorage)

### Backend Architecture

- **Framework**: Python (FastAPI)
- **API Spec**: OpenAPI 3.0.2
- **Database**: Amazon DynamoDB

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Run tests to ensure nothing breaks
4. Submit a pull request

## License

ECE 461 – Fall 2025 Project Phase 2

## Contact & Support

For issues, questions, or contributions, refer to the project repository or contact the development team.

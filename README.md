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
│   │   ├── api/               # Axios client and registry service functions
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Dashboard and feature panels
│   │   └── main.tsx
│   ├── tests/selenium/        # Smoke and accessibility tests
│   ├── package.json
│   └── vite.config.ts
└── src/                        # Python backend implementation
    ├── ...                     # CLI and API implementation
```

## Quick Start

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run the CLI
python -m src.cli [options]

# Or start the API server
python -m src.server
```

### Frontend

```powershell
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will open at `http://localhost:5173`.

## Key Features

### CLI Features
- Evaluate models from HuggingFace
- Analyze datasets for quality and size
- Inspect GitHub repositories for code metrics
- Score artifacts against multiple criteria
- Output results in various formats

### Frontend Features
- **Authentication**: Secure login for artifact management
- **Artifact CRUD**: Create, read, update, and delete models, datasets, and code artifacts
- **Search**: Find artifacts by name or regex pattern
- **Analysis Tools**:
  - Model rating and performance metrics
  - Cost analysis with dependency tracking
  - Lineage visualization
  - License compliance checking
- **Admin Panel**: Registry management and system health monitoring
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

## Configuration

### Frontend (.env)

Set the backend API URL:

```
VITE_API_URL=http://ec2-52-23-239-59.compute-1.amazonaws.com
```

Or use the default localhost during development.

### Backend

See `src/` directory for configuration options and environment variables.

## Testing

### Frontend Tests

```powershell
cd frontend

# Run smoke tests (UI functionality)
npm run test:ui

# Run accessibility audit (WCAG 2.1 AA)
npm run test:a11y
```

### Backend Tests

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

### Building for Production

**Frontend:**

```powershell
cd frontend
npm run build
npm run preview
```

**Backend:**

Refer to backend documentation in `src/` for build and deployment instructions.

## Architecture

### Frontend Architecture

- **State Management**: React Query for server state
- **HTTP Client**: Axios with automatic authorization header injection
- **UI Framework**: Material-UI (MUI) with custom dark theme
- **Build Tool**: Vite
- **Authentication**: Token-based (localStorage)

### Backend Architecture

- **Framework**: Python (Flask or FastAPI)
- **API Spec**: OpenAPI 3.0.2
- **Database**: See backend docs
- **Authentication**: Token-based with X-Authorization header

## Troubleshooting

### Frontend Issues

**"Cannot find module" errors in Vite:**
- Check relative import paths. Panel components in `src/pages/panels/` must import API with `../../api/`

**"Failed to reach backend":**
- Verify `VITE_API_URL` in `.env` or environment variables
- Ensure backend server is running and accessible

**"Token not being sent to API":**
- Check browser DevTools Network tab; verify `X-Authorization` header is present
- Ensure token is stored in `localStorage` under key `token`

**"Frontend folder not visible in explorer":**
- Open the repo root folder (`ECE-30861-Phase2-24`) in VS Code, not a subdirectory

### Backend Issues

Refer to backend documentation in the `src/` directory.

## Design & UX

- **Dark Theme**: Blue primary color (#1E4ED8) with dark backgrounds (#0B1020, #131A2A)
- **Components**: Rounded cards, soft shadows, pill-shaped buttons
- **Accessibility**: WCAG 2.1 AA compliant with visible focus styles, skip link, and aria-live regions
- **Responsive**: Mobile-friendly layout with MUI Grid system

## Metrics Explained

The registry evaluates artifacts on several dimensions:

- **Model Size Score**: Smaller, more efficient models score higher
- **License Compliance**: Artifacts with clear, permissive licenses score higher
- **Cost Analysis**: Quantifies standalone vs. total cost including dependencies
- **Lineage**: Traces upstream dependencies and data provenance
- **Health**: Continuous monitoring of availability and component status

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Run tests to ensure nothing breaks
4. Submit a pull request

## License

ECE 461 – Fall 2025 Project Phase 2

## Contact & Support

For issues, questions, or contributions, refer to the project repository or contact the development team.
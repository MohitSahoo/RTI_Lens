# RTI-Lens Frontend

React + TypeScript + Vite frontend for the RTI-Lens civic-tech platform.

## What lives here

- Landing page and dashboard shell
- RTI Q&A interface
- RTI first-appeal draft assistant
- Outcome predictor
- Analytics and knowledge graph views
- Blockchain tracker
- Government portal simulation

## App routes

| Route | Screen |
|-------|--------|
| `/` | Landing page |
| `/dashboard` | Overview |
| `/dashboard/qa` | Q&A assistant |
| `/dashboard/draft` | First-appeal draft assistant |
| `/dashboard/predictor` | Outcome predictor |
| `/dashboard/analytics` | Analytics |
| `/dashboard/graph` | Knowledge graph |
| `/dashboard/blockchain` | Blockchain tracker |
| `/dashboard/gov` | Government portal |

## Draft assistant

The draft assistant on `/dashboard/draft` sends the user query to the backend draft pipeline and displays:

- the generated RTI first-appeal draft
- the resolved addressee
- the predicted ministry and RTI section
- accepted and rejected agent outputs
- a pipeline trace for transparency

## Development

Run the frontend from the `frontend/` directory:

```bash
npm install
npm run dev
```

The Vite dev server is configured to proxy API requests to the FastAPI backend.

# LostLink

A campus lost-and-found platform. Students report a lost or found item with a
photo, and LostLink uses text similarity to surface likely matches between lost
and found reports.

- **Backend:** FastAPI + Supabase (Postgres + Storage) + scikit-learn
- **Frontend:** React 19 + Vite
- **Matching:** weighted per-field TF-IDF with typo tolerance and synonyms

## Features

- Report lost or found items with a photo, category, brand, color, location and date
- Browse, search and filter open reports
- "Find matches" compares a report against all open reports of the opposite type
- Match results show a percentage score, strength label and the fields that matched
- Mark a report as resolved so it leaves the open list
- Item photos are served through short-lived signed URLs from a private bucket

## Project structure

```
LostLink/
├── backend/
│   ├── app/
│   │   ├── config.py            # Environment settings
│   │   ├── database.py          # Supabase client
│   │   ├── main.py              # FastAPI app + CORS
│   │   ├── routes/reports.py    # API endpoints
│   │   ├── schemas/report.py    # Response models
│   │   └── services/
│   │       ├── matching.py      # Similarity scoring
│   │       └── storage.py       # Signed image URLs
│   ├── test_matching.py
│   ├── Dockerfile
│   ├── Procfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api.js
│   │   ├── App.jsx
│   │   ├── components/
│   │   └── utils/
│   ├── .env.example
│   └── package.json
└── README.md
```

## Local setup

### 1. Supabase

1. Create a project at [supabase.com](https://supabase.com).
2. Open **SQL Editor** and run the schema below.
3. Open **Storage → New bucket**, create a **private** bucket named `item-images`.
4. Copy the project URL and `service_role` key from **Project Settings → API**.

```sql
create extension if not exists "pgcrypto";

create table if not exists public.reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users (id) on delete set null,
  report_type text not null check (report_type in ('lost', 'found')),
  item_name text not null,
  category text not null,
  description text not null,
  color text,
  brand text,
  location_text text not null,
  event_date date not null,
  image_path text,
  status text not null default 'open' check (status in ('open', 'resolved')),
  created_at timestamptz not null default now()
);

create index if not exists reports_status_type_idx
  on public.reports (status, report_type, created_at desc);

alter table public.reports enable row level security;
-- The backend uses the service role key, which bypasses RLS.
```

> The `service_role` key must only ever be used on the server. Never put it in
> the frontend or commit it to git.

### 2. Backend

```bash
cd backend

# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env` from `.env.example` and fill in the Supabase values:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174
```

Run the API:

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Interactive docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

Check the matching engine without the API:

```bash
python test_matching.py
```

### 3. Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env` from `.env.example`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

```bash
npm run dev
```

Open the URL printed by Vite (usually http://localhost:5173).

Production build:

```bash
npm run build
npm run preview
```

## Matching

Each lost/found pair is scored field by field:

| Field | Weight |
| --- | --- |
| Item name | 30% |
| Description | 20% |
| Category | 15% |
| Color | 15% |
| Brand | 10% |
| Location | 10% |

For every field, the service combines word-level TF-IDF with character
n-gram TF-IDF (to tolerate typos) and a shared-word score. Fields that are empty
on both reports are skipped, and common synonyms such as `mobile → phone` or
`purse → wallet` are normalised first. Results below `MATCH_THRESHOLD` (25 by
default) are hidden.

## API

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | API welcome message |
| `GET` | `/health` | Health check |
| `POST` | `/api/reports` | Create a report (`multipart/form-data`) |
| `GET` | `/api/reports?report_type=lost` | List open reports |
| `GET` | `/api/matches/{report_id}?min_score=25&limit=20` | Find matches |
| `PATCH` | `/api/reports/{report_id}/status` | Set status to `open` or `resolved` |

`POST /api/reports` accepts: `report_type`, `item_name`, `category`,
`description`, `color`, `brand`, `location_text`, `event_date` and `image`
(JPG, PNG or WEBP, max 5 MB).

## Deployment

### Backend (Render, Railway, Fly.io or any Docker host)

The `backend/Dockerfile` runs the API with `uvicorn` on `$PORT`.

**Render**

1. Push this project to GitHub.
2. Create a **New Web Service** and select the Docker runtime.
3. Set **Root Directory** to `backend`.
4. Add environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `ALLOWED_ORIGINS=https://your-frontend-domain`
5. Health check path: `/health`.

Alternatively, commit `render.yaml` (included) and use a Render Blueprint.

**Railway / Fly.io**

Use the Dockerfile in `backend/` and set the same environment variables.

### Frontend (Vercel or Netlify)

1. Set the project root to `frontend`.
2. Build command: `npm run build`, output directory: `dist`.
3. Add environment variable `VITE_API_URL=https://your-backend-domain`.
4. Deploy, then add the deployed frontend URL to the backend's
   `ALLOWED_ORIGINS` and redeploy the backend.

`frontend/netlify.toml` is included for Netlify. Vercel auto-detects Vite.

### Checklist after deploying

- `GET https://your-backend/health` returns `{"status":"ok"}`
- The frontend loads reports and images
- Submitting a report works
- CORS allows the deployed frontend origin

## Security notes

- The API currently has no authentication. Anyone who can reach it can submit
  reports or mark them resolved. Add Supabase Auth (and a `user_id` check) before
  a public launch.
- The storage bucket is private; images are exposed only through signed URLs
  that expire after `IMAGE_URL_TTL` seconds (one day by default).
- Reported text is validated and length-limited, and uploads are restricted to
  JPG/PNG/WEBP under 5 MB.

# LostLink frontend

React 19 + Vite client for the LostLink lost-and-found platform.

## Development

```bash
npm install
cp .env.example .env   # Windows: copy .env.example .env
npm run dev
```

`VITE_API_URL` must point at the FastAPI backend (default
`http://127.0.0.1:8000`).

## Scripts

- `npm run dev` — start the Vite dev server
- `npm run build` — production build into `dist/`
- `npm run preview` — preview the production build
- `npm run lint` — run ESLint

See the [project README](../README.md) for backend setup and deployment.

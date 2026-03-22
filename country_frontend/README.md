# Country Intelligence Agent — Frontend

React frontend for the Country Intelligence Agent API.

## Stack

- React 18 + React Router v6
- Vite (dev server + build)
- No UI library — pure CSS with custom design system
- Fonts: Syne (display) + DM Mono (code/labels)

## Quick Start

```bash
npm install

# Dev (proxies /query, /history, /health to localhost:8000)
npm run dev

# Production build
npm run build
npm run preview
```

## Production (pointing at Fly.io)

```bash
cp .env.example .env.local
# Set VITE_API_URL=https://your-app.fly.dev

npm run build
# Serve dist/ from any static host (Vercel, Netlify, Fly.io static)
```

## Pages

| Route | Description |
|---|---|
| `/` | Main query interface — search bar + result card + example chips |
| `/history` | Paginated audit log with status + country filters |

## Project Structure

```
src/
├── components/
│   ├── Layout.jsx / .css     # Sidebar navigation shell
│   ├── HealthBar.jsx / .css  # Top API status ribbon (polls /health every 30s)
│   ├── SearchBar.jsx / .css  # Query input with animated placeholder
│   ├── ResultCard.jsx / .css # Agent response display
│   ├── HistoryPanel.jsx /.css # Paginated history table
│   └── StatusBadge.jsx / .css # Coloured status pill
├── hooks/
│   └── useQuery.js           # useQuery, useHistory, useHealth hooks
├── lib/
│   └── api.js                # Typed fetch wrapper for all endpoints
├── pages/
│   ├── Home.jsx / .css       # Main page
│   └── History.jsx / .css    # History page
├── App.jsx                   # Router setup
├── main.jsx                  # Entry point
└── index.css                 # Global styles + CSS variables
```

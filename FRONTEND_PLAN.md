# Frontend Redesign Plan — Household Finance Copilot

## Decision

Replace Streamlit with **React + Vite** SPA. Chosen aesthetic: **Midnight Ledger** (Option 1).  
Reference mockup: `mockups/option1-midnight-ledger.html`

Backend (FastAPI at `localhost:8000`) is **untouched**. All existing API routes stay as-is.

---

## Design System

### Typography
- **UI + titles**: IBM Plex Sans (300, 400, 500, 600)
- **Numbers + data**: IBM Plex Mono (300, 400, 500)
- No serif fonts

### Color Tokens
```css
--bg: #0E0E0E
--surface: #161616
--surface2: #1E1E1E
--border: #2A2A2A
--text: #F0EAD6
--text-muted: #7A7060
--text-dim: #4A4438
--gold: #C9924A
--gold-dim: #8A6030
--green: #4A8C5C
--red: #8C4A4A
```

### Layout
- Vertical sidebar nav (200px, collapsible to icons)
- Topbar with page title + contextual filters
- Left analytics strip (260px) + right table area
- All text: IBM Plex Sans; all numbers: IBM Plex Mono tabular

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Framework | React 18 + Vite | Fast dev, tiny bundle, free deploy |
| Routing | React Router v6 | Tab navigation maps to routes |
| Data fetching | TanStack Query v5 | Cache, background refetch, loading states |
| Charts | Recharts | Lightest, composable, React-native |
| Styling | CSS Modules + CSS vars | Zero runtime, no Tailwind bloat |
| Auth | Context + localStorage | Matches existing JWT token flow |
| Deploy | Vercel or Netlify | Free tier, drag-and-drop or git push |

---

## Project Structure

```
frontend-react/
├── src/
│   ├── main.jsx
│   ├── App.jsx                  # Router, auth gate
│   ├── api/
│   │   ├── client.js            # Base fetch wrapper (auth token, error handling)
│   │   ├── transactions.js      # All /api/transactions/* calls
│   │   ├── analytics.js         # All /api/analytics/* calls
│   │   ├── categories.js        # /api/categories/rules
│   │   └── documents.js         # /api/transactions/statements, upload, document fetch
│   ├── auth/
│   │   ├── AuthContext.jsx      # token, username, login(), logout()
│   │   └── LoginPage.jsx
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.jsx      # Nav, user info, badge on Review Queue
│   │   │   └── Topbar.jsx       # Page title + filter controls
│   │   ├── shared/
│   │   │   ├── CategoryPill.jsx
│   │   │   ├── TagChip.jsx
│   │   │   ├── AmountCell.jsx   # Mono font, debit/credit color
│   │   │   ├── Spinner.jsx
│   │   │   └── ErrorBanner.jsx
│   │   └── charts/
│   │       ├── DonutChart.jsx
│   │       ├── SparkLine.jsx
│   │       ├── BarChart.jsx
│   │       └── StackedBarChart.jsx
│   ├── pages/
│   │   ├── Browse/
│   │   │   ├── Browse.jsx       # Main layout: analytics strip + table
│   │   │   ├── AnalyticsStrip.jsx
│   │   │   ├── TransactionTable.jsx
│   │   │   ├── TransactionRow.jsx
│   │   │   ├── EditForm.jsx     # Inline slide-down edit
│   │   │   └── Browse.module.css
│   │   ├── Analytics/
│   │   │   ├── Analytics.jsx    # Full analytics dashboard + filters
│   │   │   └── Analytics.module.css
│   │   ├── ReviewQueue/
│   │   │   ├── ReviewQueue.jsx  # Split: transaction list + document panel
│   │   │   ├── ReviewCard.jsx
│   │   │   ├── DocumentPanel.jsx
│   │   │   └── ReviewQueue.module.css
│   │   ├── Statements/
│   │   │   ├── Statements.jsx   # Upload form + statement list
│   │   │   ├── UploadZone.jsx
│   │   │   └── Statements.module.css
│   │   └── Rules/
│   │       ├── Rules.jsx
│   │       ├── RuleCategory.jsx # Expandable, keyword pills
│   │       └── Rules.module.css
│   └── styles/
│       ├── tokens.css           # All CSS vars (design system)
│       ├── global.css           # Reset, body, scrollbar, font-face
│       └── fonts.css            # Google Fonts import
├── index.html
├── vite.config.js
└── package.json
```

---

## API Client

```js
// src/api/client.js
const BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export async function apiFetch(method, path, { token, body, params } = {}) {
  const url = new URL(BASE + path)
  if (params) Object.entries(params).forEach(([k, v]) => v != null && url.searchParams.set(k, v))

  const res = await fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: body ? JSON.stringify(body) : undefined,
  })

  if (res.status === 204) return null
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
```

---

## All API Calls to Implement

### Auth
| Action | Method | Endpoint |
|---|---|---|
| Login | POST | `/api/auth/token` |
| Logout | POST | `/api/auth/logout` |

### Transactions (Browse + Review)
| Action | Method | Endpoint |
|---|---|---|
| List processed | GET | `/api/transactions/processed` |
| List pending | GET | `/api/transactions/pending` |
| Update (edit) | PATCH | `/api/transactions/{id}` |
| Approve | POST | `/api/transactions/{id}/approve` |
| Reject | POST | `/api/transactions/{id}/reject` |
| Export CSV | GET | `/api/transactions/export` |
| Poll Gmail | POST | `/api/transactions/poll_email` |
| Get document | GET | `/api/transactions/{id}/document` |
| Add tag | PUT | `/api/transactions/{id}/tags/{tag}` |
| Remove tag | DELETE | `/api/transactions/{id}/tags/{tag}` |

### Analytics
| Action | Method | Endpoint |
|---|---|---|
| By category | GET | `/api/analytics/by_category` |
| Trends (weekly) | GET | `/api/analytics/trends` |
| By tag | GET | `/api/analytics/by_tag` |
| By month | GET | `/api/analytics/by_month` |
| By owner | GET | `/api/analytics/by_owner` |
| Category trends | GET | `/api/analytics/category_trends` |

### Categories
| Action | Method | Endpoint |
|---|---|---|
| List rules | GET | `/api/categories/rules` |
| Add keyword | POST | `/api/categories/rules/{category}/keywords` |
| Delete keyword | DELETE | `/api/categories/rules/{category}/keywords/{keyword}` |

### Documents / Statements
| Action | Method | Endpoint |
|---|---|---|
| List statements | GET | `/api/transactions/statements` |
| Upload document | POST | `/api/upload` |

---

## Pages: Feature Spec

### Browse (`/browse`)

**Layout:** Topbar (title + date/category filters + export button) | Left analytics strip 260px | Right scrollable transaction table

**Analytics strip (left):**
- Period summary: total spent, income, tx count (stat blocks with mono numbers)
- Donut chart: spending by category (Recharts PieChart with inner radius)
- Legend rows below donut
- Sparkline: weekly trend (Recharts AreaChart, no axes)

**Transaction table (right):**
- Sticky header: Date | Merchant | Category | Owner | Amount (right-aligned) | Actions
- Row: date (mono, muted), merchant name + bank sub-label, category pill, owner, amount (mono, debit/credit color), edit + menu buttons
- Selected row: `rgba(201,146,74,0.06)` background
- Tags displayed as small chips under merchant name when present
- Inline edit: clicking edit expands a form below the row (not a modal) with fields: Merchant, Amount, Description, Owner (dropdown), Category (dropdown) — Save / Cancel buttons
- Footer: tx count | period total | prev/next pagination

**Filters (topbar):**
- From date, To date (date inputs)
- Category dropdown (All + 13 categories)
- Filters refetch analytics + table on change

### Analytics (`/analytics`)

**Layout:** Topbar (title + date filters + month window) | responsive analytics grid

**Graphs:**
- Spending per category: donut chart + ranked legend
- Spending per month: monthly bar chart
- Weekly trend: area chart
- Category trends: stacked monthly bar chart for top categories
- Spending by owner: horizontal bar chart
- Spending by tag: horizontal bar chart

**Summary metrics:**
- Total spending
- Monthly average
- Top category

### Review Queue (`/review`)

**Layout:** Topbar (title + "Poll Gmail" button) | Split pane — left 60% transaction list, right 40% document viewer

**Transaction list:**
- Each card: date, merchant, amount, confidence badge, bank
- Owner dropdown + category dropdown inline per card
- Edit button → expands form (merchant, amount, description)
- ✓ Approve button → saves owner + category, removes from list
- ✗ Reject button → removes from list
- 📄 button → loads document in right panel
- Tags section per card

**Document panel (right):**
- Shows filename, upload date
- PDF: `<iframe>` with base64 blob URL, or `<img>` for images
- Download button

**Sort:** dropdown — Date newest/oldest, Amount high/low, Confidence high/low

**Sidebar badge:** shows pending count, updates after approve/reject

### Statements (`/statements`)

**Upload zone (top):**
- Drag-and-drop or click-to-select file input
- Accepts PDF, images
- On upload: POST `/api/upload`, show progress → success toast with tx count extracted

**Statement list (below):**
- Each row: icon (📄/🖼), filename, bank, period start→end, upload date, tx count
- Read-only

### Rules (`/rules`)

**Layout:** one expandable section per category (13 total)

**Each section:**
- Header: category name + keyword count badge, click to expand
- Body: keyword pills grid (max 5 per row)
- Each pill: keyword text + ✕ delete button
- Bottom of body: text input + Add button

---

## Constants

```js
export const CATEGORIES = [
  'Groceries', 'Restaurants', 'Transportation', 'Utilities',
  'Shopping', 'Entertainment', 'Healthcare', 'Travel',
  'Insurance', 'Salary', 'Bonus', 'Investments', 'Other'
]

export const OWNERS = ['—', 'Rafael', 'Heloisa', 'Shared']

export const PAGE_SIZE = 15  // increase from Streamlit's 10 — table fits more rows now
```

---

## Auth Flow

1. `AuthContext` reads token from `localStorage` on mount
2. If token present → render app; if not → render `LoginPage`
3. Login POSTs to `/api/auth/token`, stores token + username in context + localStorage
4. Logout clears both
5. All API calls inject `Authorization: Bearer {token}` header
6. On 401 response → auto-logout + redirect to login

---

## Sidebar Navigation Logic

Mirrors existing Streamlit logic: if pending transactions exist, Review Queue shows badge count. Order is always: Browse → Analytics → Review Queue → Statements → Rules.

Check pending count on app load with a lightweight GET `/api/transactions/pending?limit=1` — store result in context.

---

## Deployment

### Vercel (recommended)
1. `npm run build` → `dist/` folder
2. `vercel --prod` or connect GitHub repo to Vercel dashboard
3. Set env var: `VITE_API_BASE=https://your-backend-url`

### Netlify alternative
1. Build command: `npm run build`
2. Publish dir: `dist`
3. Set env var: `VITE_API_BASE=...`

### Backend CORS
Add frontend origin to FastAPI CORS middleware in `backend/main.py`:
```python
origins = [
    "http://localhost:5173",   # Vite dev
    "https://your-vercel-url.vercel.app",
]
```

---

## Implementation Order

1. **Scaffold** — `npm create vite@latest frontend-react -- --template react`, install deps (react-router-dom, @tanstack/react-query, recharts)
2. **Design tokens** — `tokens.css`, `global.css`, fonts
3. **Auth** — `AuthContext`, `LoginPage`, route guard
4. **API client** — `client.js` + all endpoint modules
5. **Layout shell** — `Sidebar`, `Topbar`, router setup
6. **Browse page** — highest priority, most complex
   - Analytics strip + charts
   - Transaction table + pagination
   - Inline edit form
   - Tags
7. **Analytics page** — dedicated chart workspace
   - Category, monthly, weekly, owner, tag, and category-trend charts
   - Date filters and month-window selector
8. **Review Queue** — second priority (has pending badge dependency)
   - Cards with inline dropdowns
   - Approve / Reject
   - Document panel
9. **Statements** — upload zone + list
10. **Rules** — expandable categories + keyword CRUD
11. **Polish** — loading skeletons, error states, toast notifications, CSV export

---

## Notes

- Keep `frontend/` (Streamlit) intact during build — don't delete until React version is verified end-to-end
- CSV export: use `window.open(url)` with auth token in query param, or fetch blob + `URL.createObjectURL`
- Document viewer: fetch base64 from `/api/transactions/{id}/document`, decode to blob URL, render `<iframe>` or `<img>`
- Recharts responsive containers need explicit height on parent — use CSS vars for chart heights
- Page size bumped to 15 (table can show more rows at new density)

# Frontend

## Overview
Static HTML/CSS/JS app served via any static server. Uses Poppins/Inter fonts, Cigna-themed palette, and responsive layouts. Patient and Admin portals share a sidebar shell with collapse toggle.

## Structure
- `frontend/index.html`: Home page with hero, tray, value blocks, notice.
- `frontend/member-guide.html`: Demo access and portal guide.
- `frontend/css/style.css`: Global styles, patient/admin shell, components.
- `frontend/js/auth.js`: Auth helpers, login/register calls.
- Patient pages: `frontend/patient/*`
- Admin pages: `frontend/admin/*`
- Assets: `frontend/assets/*` (logos, icons)

## Auth Flow
- Login via email or patient ID and password using `POST /api/v1/auth/login`.
- Token is stored in session/local storage. Guards block unauthenticated navigation and redirect to `login.html?next=...`.

## Patient Pages
- Sidebar: Profile, Dashboard, Submit, History, Lifecycle, Home.
- Dashboard: KPIs, monthly claims + amount chart, status donut, recent claims.
- Claims History: Filter by status/year + text search; timeline chart.
- Submit Claim: Card form, INR currency, dropzone preview (S3 uploads currently disabled).
- Lifecycle: Stepper showing Submitted → In Review → Decision with color codes.

## Admin Pages
- Sidebar: Home, Profile, Dashboard, Claims, Analytics.
- Dashboard: KPIs and charts based on all claims (`GET /admin/claims`) with real-time polling; status donut shows Pending/Approved/Rejected.
- Claims: Pending claims table with approve/reject actions; Search by Patient ID lists all claims for that patient (`GET /admin/claims/by-patient/{patient_id}`).
- Analytics: Year + user filters drive monthly counts/amounts, status donut, top users by amount and also filter the User Search table accordingly.

## Development
- Start a static server in `frontend`: `python3 -m http.server 8080`
- Update Playwright tests (optional): `npm i -D @playwright/test && npx playwright test`

## Accessibility
- Semantic landmarks (`header`, `nav`, `aside`, `main`), focus states and high-contrast colors. Charts include readable labels.

## Notes
- Admin endpoints include `GET /admin/claims` and `GET /admin/claims/by-patient/{patient_id}` used by dashboard/analytics/search.
- S3 uploads are temporarily disabled; file selection is preview-only.

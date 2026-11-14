IntelliCampus frontend fast-track update
========================================

This archive contains the updated frontend source only. It deliberately excludes:
- .env files (keep your existing local frontend/.env)
- node_modules
- .git history
- dist/build output

How to apply safely:
1. Make a backup copy of your current `intellicampus/frontend` folder.
2. Extract this archive. It contains a `frontend/` folder.
3. Copy the extracted `frontend/` contents into your existing `FYP/intellicampus/frontend/` folder and allow source files to be replaced.
4. Do NOT replace or delete your local `.env`.
5. In VS Code terminal, from the existing frontend directory run:
   npm install
   npm run build
   npm run dev

The pages for applications, opportunities, FYP, chatbot, notifications, analytics, user management, workflow settings and knowledge base currently use illustrative/demo data. These are frontend previews, not live backend records. Authentication keeps the existing API integration code. Real module API integration is intentionally deferred until the database/authentication issue is resolved.

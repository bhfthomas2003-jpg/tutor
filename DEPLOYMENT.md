# Deployment

## A. Frontend (GitHub Pages)
1. github.com -> New repository `thomas-ai-math-studio` (public is required for free Pages; it contains no secrets).
2. Upload the project files (Add file -> Upload files). Never upload `.env`.
3. Settings -> Pages -> Deploy from branch `main`, folder `/frontend` is not offered, so either move frontend files to `/docs` and choose `/docs`, or use `/ (root)` with the frontend files at root.
4. Copy `config.example.js` to `config.js`, set `API_BASE` to your backend URL (after Part B), commit.
Your site: https://USERNAME.github.io/thomas-ai-math-studio/

## B. Backend (separate; needs ffmpeg + Python, so not GitHub Pages)
Use any Docker host (Render, Railway, Fly.io; free tiers are limited and sleep, long renders may time out - check current limits). Point it at `backend/` with its Dockerfile.
Environment variables (set in the host dashboard, never in Git): `APP_TOKEN` (long random), `ALLOWED_ORIGIN` (https://USERNAME.github.io, no trailing slash), `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `ELEVENLABS_API_KEY`, optional `ELEVENLABS_VOICE_ID`.
Attach a persistent disk at `DATA_DIR` or cached audio/videos vanish on restart. Visit `/health` to confirm.

## C. Connect providers
- AI: create an Anthropic API key (console.anthropic.com), set `ANTHROPIC_API_KEY`.
- Voice: ElevenLabs key; instant voice cloning requires a plan that includes it. Upload only your own recordings.
- Storage: milestone 1 stores files on the backend disk. Google Drive needs a Google Cloud OAuth client and backend-side tokens; not implemented yet.

## D. First run
Open the site -> Settings -> paste APP_TOKEN -> Dashboard should show AI, voice, FFmpeg status. Follow the order in README. Preview the intro before the full video.

## Troubleshooting
- "Cannot reach the backend": wrong API_BASE, host asleep, or ALLOWED_ORIGIN mismatch.
- 401: token mismatch. 503: a key is missing on the backend.
- "Voice not set up": upload samples first. 502 from voice: plan lacks cloning or no credit.
- FFmpeg failed / tiny fonts: image lacks ffmpeg or fonts-dejavu-core (use the Dockerfile).

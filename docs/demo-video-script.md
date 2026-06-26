# ClaimFarm — 3-minute demo video script

> Target: 180 seconds (judges stop watching at 3:00 sharp per rules).
> Tone: calm, technical, evidence-first — no salesman energy. Let the work speak.
> Tool: QuickTime (macOS) screen + mic recording, then trim in iMovie or DaVinci Resolve.

## What's changed vs the earlier script

We now have a real product surface live on the open internet:

- Frontend: **`https://claimfarm-dashboard.vercel.app`** — Next.js + the Figma-ported design system (auth-canvas backgrounds, brand mark, gradient CTAs).
- Backend: **`https://claimfarm-api-wovsxktpbk.ap-southeast-1.fcapp.run`** — Alibaba Function Compute 3.0, custom container pulled from `ghcr.io/hemnaath04/claimfarm:latest`.
- Telegram bot is the live intake channel (Twilio/Bird were dead-ended on the free tier).
- Streamlit dashboard is gone — the adjuster console now lives at `/admin`, the workspace owner dashboard at `/dashboard`.
- The adjuster claim detail includes the **Claim photo + verification signals** card (EXIF, Qwen-VL authenticity, weather corroboration, GPS, near-duplicate).

No laptop processes are required. Everything in the demo is running on Vercel + Alibaba Cloud.

## Asset prep — before you press record

1. **Reset cookies in the recording browser** so you record a clean sign-up.
   - Brave/Chrome → Cmd+Shift+Delete → cookies for `vercel.app` + `*.fcapp.run` only.

2. **Open these tabs in this order** (Cmd+1 to Cmd+6 will cycle cleanly):
   - **Tab 1**: `https://claimfarm-dashboard.vercel.app` (marketing landing).
   - **Tab 2**: `https://claimfarm-dashboard.vercel.app/auth/sign-up` (auth flow).
   - **Tab 3**: `https://claimfarm-dashboard.vercel.app/admin` (adjuster console — the centrepiece).
   - **Tab 4**: `https://claimfarm-dashboard.vercel.app/dashboard` (workspace owner).
   - **Tab 5**: Telegram desktop, conversation with your `@claimfarm_bot`.
   - **Tab 6**: `https://github.com/hemnaath04/claimfarm` (repo).

3. **Have a damaged-crop photo ready on your desktop.** Use `data/eval/sample_drought_corn.jpg` or any real phone photo of distressed maize / wheat / rice. The verification panel pops more when the photo is a real phone capture (EXIF present, GPS, capture time).

4. **Pre-record optional B-roll**:
   - The Alibaba FC 3.0 console showing `claimfarm-api` "Running".
   - The Vercel project list showing the production deployment "Ready".
   - The DashVector cluster overview.
   These can be still images dropped onto the timeline as cutaways.

5. **Mic + capture**: QuickTime → File → New Screen Recording → choose internal mic. Aim for **1080p+, 30fps**.

## Script — every line, with timing

### 0:00 – 0:12 · Hook + problem

**Visual:** Title card on the auth-canvas black `#05070A`. Brand mark on the left (the gradient leaf-grid tile) + the wordmark `claim` + neon `farm`. Subtitle below: *"Insurance claims for the next 500 million farmers."* Hold 3 seconds, then cut to a fullscreen still of distressed maize.

**Voiceover (~10s):**

> "Five hundred million smallholder farmers globally are locked out of insurance — the paperwork is in the wrong language and demands evidence they can't structure. ClaimFarm turns one photo into a filed claim in sixty seconds."

### 0:12 – 0:40 · Farmer side (Telegram intake)

**Visual:** Switch to **Telegram desktop** (Tab 5). Show the conversation. Send a photo with a short caption — e.g. `"My maize field after the dry spell"`. Within ~30 seconds the bot replies with a localized confirmation message and a claim reference.

**Voiceover (~25s):**

> "The farmer interface is Telegram — free, low-bandwidth, supports voice, runs on any feature phone with a data line. They send a photo and a one-line description. In the background, Qwen-VL identifies the crop and damage, Qwen-Max corroborates against Open-Meteo weather data for the photo's GPS and capture date, and the bot replies in the farmer's own language. No forms, no upload portals."

### 0:40 – 1:35 · Adjuster console (the showpiece — 55 seconds)

**Visual:** Cut to **Tab 3 — `/admin`**. The queue shows the freshly-filed claim at the top. Click it.

The claim detail panel scrolls in. **Pause for two beats on the "Claim photo + verification signals" card** — this is the new bit the judges haven't seen.

Then scroll through:
- AI damage assessment (Qwen-VL-Max card with crop / cause / severity / affected / confidence).
- Weather corroboration (Open-Meteo + Qwen-Max card, with the strength bar and flags).
- Similar past claims (DashVector card).
- Localized farmer message preview.
- Adjuster decision row at the bottom.

Click **Approve & submit**. The status pill flips from `pending review` → `submitted`.

**Voiceover (~52s):**

> "The adjuster console. Up top — the photo the farmer sent, alongside six verification signals we compute on every intake. EXIF metadata present, GPS coordinates pulled from the camera, capture time, Qwen-VL authenticity score — that's a vision prompt asking 'is this a real phone photo, or a screenshot, render, or stock image?' — weather corroboration against Open-Meteo for the photo's location and date, and a near-duplicate check against past claims indexed in Alibaba DashVector.
>
> Below — the structured AI damage assessment. Crop, cause, severity zero to one hundred, affected area, confidence. The corroboration card cross-references against thirty days of historical weather. Similar past claims surface via the same embeddings.
>
> Approve, and the claim is forwarded to the carrier endpoint, the status flips, and the farmer gets a localized notification."

### 1:35 – 2:00 · Workspace dashboard

**Visual:** Cut to **Tab 4 — `/dashboard`**. Land on the Overview tab — show the four KPI tiles (claims this month, approved, fraud flags, time-to-decision). Switch to the **API & webhooks** tab. Click **Issue key**. The one-time secret pane appears with the `cf_live_…` token. Click Copy. Switch to revoke flow briefly — show the revoked badge appearing.

**Voiceover (~22s):**

> "Operators get a workspace dashboard — claims this month, approval rate, fraud flags, average time to decision. Issue API keys with scoped permissions for carrier integrations, webhooks signed with HMAC, GDPR data export and account deletion built in. The whole surface is auth-gated with Argon2id password hashing, opaque session cookies, and a magic-link option for passwordless sign-in."

### 2:00 – 2:25 · Alibaba Cloud proof

**Visual:** Cut to a terminal (or a pre-prepared still). Show the curl:

```
$ curl -sS https://claimfarm-api-wovsxktpbk.ap-southeast-1.fcapp.run/healthz
{"status":"ok"}

$ curl -sS .../openapi.json | jq '.paths | length'
31
```

Then cut to the **Alibaba FC 3.0 console** with `claimfarm-api` showing the image `ghcr.io/hemnaath04/claimfarm:latest` and the function in Running state. Brief cut to the DashVector cluster page.

**Voiceover (~22s):**

> "The backend runs on Alibaba Function Compute 3.0, Singapore region, custom container pulled from a public registry. Thirty-one HTTP routes live behind one public HTTPS trigger. Photos persist to Alibaba Object Storage. The vector store is Alibaba DashVector — same product family as the Qwen models we call, so vision, reasoning, embeddings, and retrieval all flow through one Alibaba Cloud account."

### 2:25 – 2:50 · Three Qwen capabilities

**Visual:** Briefly show `app/clients/qwen.py` open in VS Code for two beats (the chat + vision wrapper, ~5s), then `app/agents/photo_forensics.py` (the structured authenticity prompt, ~5s), then scroll through `docs/architecture.md` highlighting the Qwen capability inventory section.

**Voiceover (~22s):**

> "Three Qwen capabilities are exercised end-to-end. Qwen-VL-Max for multimodal damage assessment and photo authenticity. Qwen-Max for reasoning, weather corroboration, and multilingual rewriting in ten languages. Qwen text-embedding-v3 for retrieval and near-duplicate fraud detection. Every model boundary uses a Pydantic schema — no hand-waving JSON."

### 2:50 – 3:00 · Close

**Visual:** Black card. Centred: brand mark + `claimfarm` wordmark. Below, the three URLs stacked in JetBrains Mono:

```
github.com/hemnaath04/claimfarm
claimfarm-dashboard.vercel.app
claimfarm-api-wovsxktpbk.ap-southeast-1.fcapp.run
```

**Voiceover (~8s):**

> "Open source, MIT licensed, running entirely on Alibaba Cloud. Thanks for watching."

## Production tips

- **Voiceover separately.** Record the screen capture silent first, then record voiceover into a second QuickTime audio file. Drop them on the same iMovie timeline — easier to retake voice without redoing the screen.
- **Speak at ~150 wpm** (TED-talk cadence). The script above is ~430 words → fits in 175s comfortably.
- **No music** unless it's royalty-free. YouTube Audio Library → "Cinematic" or "Ambient" works.
- **Captions help judges**: YouTube auto-captions are fine for this length — review and fix the Qwen, Open-Meteo, DashVector, Argon2id, Pydantic spellings.
- **Upload Unlisted while iterating**, flip to Public on submission day.
- **Test the demo URLs from a clean browser session** (incognito) before recording — confirms cookies aren't masking a regression.

## Hard-rules sanity check

- [ ] Runtime ≤ 3:00
- [ ] No third-party trademarks or copyrighted music
- [ ] Uploaded publicly on YouTube / Vimeo / Youku
- [ ] Captions visible (auto-generated is fine)
- [ ] Demo shows the project actually working (live URLs, not just slides)
- [ ] Track 4 (Autopilot Agent) called out

## Filename + title for upload

- **File**: `claimfarm-demo.mp4`
- **YouTube title**: `ClaimFarm — Crop insurance claims in 60 seconds (Qwen Cloud Hackathon, Track 4)`
- **YouTube description**:

```
ClaimFarm turns a smallholder farmer's Telegram photo of a damaged
crop into a filed insurance claim. Built on Qwen-VL-Max, Qwen-Max,
and Qwen text-embedding-v3 with Alibaba Function Compute 3.0,
Object Storage, and DashVector.

Six verification signals per claim — EXIF metadata, GPS, capture
time, Qwen-VL authenticity, weather corroboration via Open-Meteo,
and DashVector near-duplicate detection — give the human adjuster
the evidence they need to approve in seconds.

Track 4 (Autopilot Agent) — Global AI Hackathon Series with Qwen Cloud.

Code: https://github.com/hemnaath04/claimfarm
Live frontend: https://claimfarm-dashboard.vercel.app
Live API: https://claimfarm-api-wovsxktpbk.ap-southeast-1.fcapp.run

Open source, MIT licensed.
```

## Quick fallbacks if something breaks during recording

| Problem | Fallback |
|---|---|
| Telegram bot is slow on a cold-start FC instance | The first message after a long idle can take 10-15s. Warm it up with a `curl /healthz` before recording. |
| The freshly-filed claim doesn't show forensics | FC's `/tmp` is wiped between cold starts. Send the photo twice — the second one will land with a warm instance and full forensics. |
| Vercel cookie issue (cf_session) | Sign in fresh in the recording browser; SameSite=None requires HTTPS, which both deployed surfaces have. |
| Auth verification email | The dev-mode response includes a `verification_url` field that the sign-up flow auto-follows. You'll see the green "You're verified" card in ~2s. |

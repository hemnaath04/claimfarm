# ClaimFarm — 3-minute demo video script

> Target: 180 seconds (judges stop watching at 3:00 sharp per rules).
> Tone: serious, calm, technical — no salesman energy. Let the work speak.
> Tool: QuickTime (macOS) screen + mic recording, then trim in iMovie.

## Asset prep — do these BEFORE you press record

1. **Reset the dashboard data** so the demo is reproducible:
   ```bash
   cd ~/projects/claimfarm
   rm -f claimfarm.sqlite
   uv run python scripts/reindex_claims.py   # clears vector store of stale claims
   ```

2. **Pre-seed two claims** so the queue isn't empty:
   ```bash
   # Claim 1 — Ravi Kumar, drought, Hindi farmer
   uv run python scripts/seed_demo_claim.py \
     data/eval/sample_drought_corn.jpg 35.15 -89.97 2007-08-15 \
     "Ravi Kumar" +91-555-0100 hi

   # Claim 2 — different farmer, flood (download a flood photo first)
   curl -sSLo data/eval/sample_flood.jpg \
     "https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Drought_affected_Maize_crop_-_geograph.org.uk_-_7267273.jpg/960px-Drought_affected_Maize_crop_-_geograph.org.uk_-_7267273.jpg"
   uv run python scripts/seed_demo_claim.py \
     data/eval/sample_flood.jpg 11.5564 104.9282 2024-08-10 \
     "Lina Tan" +60-12-3456789 en
   ```

3. **Start the services** in three terminal windows:
   ```bash
   # T1 — mock insurer (port 8001)
   uv run uvicorn mock_insurer.main:app --port 8001 --reload

   # T2 — Streamlit dashboard
   uv run streamlit run dashboard/app.py

   # T3 — keep open for live curl to FC
   ```

4. **Open browser tabs in this order** (so Cmd+1, Cmd+2, etc. switch cleanly):
   - Tab 1: Streamlit dashboard (http://localhost:8501)
   - Tab 2: docs/architecture.md rendered on GitHub
   - Tab 3: The live Function Compute /docs URL
   - Tab 4: Alibaba Cloud console showing FC function overview
   - Tab 5: VS Code with `app/agents/damage_assessor.py` open

5. **Record at 1080p or higher**. QuickTime → File → New Screen Recording → choose internal mic + system audio if you want UI clicks audible.

## Script (every line, with timing)

### 0:00 – 0:15 — The problem
**Visual:** Title card "ClaimFarm" + subtitle "Crop insurance for the next 500 million farmers" on a black background for 3 seconds. Then cut to a stock photo of a damaged field (use the same data/eval/sample_drought_corn.jpg fullscreen).

**Voiceover (read in 12 seconds):**
> "Five hundred million smallholder farmers lose crops to weather every year. Most never file an insurance claim — the forms are in the wrong language, demand evidence they can't structure, and assume literacy in domains they were never trained for. ClaimFarm fixes that with one photo."

### 0:15 – 0:35 — Pipeline overview
**Visual:** Show docs/architecture.md mermaid diagram fullscreen for 20 seconds. Optionally trace the flow with your cursor.

**Voiceover:**
> "A farmer sends a WhatsApp photo. Qwen-VL identifies the crop and the damage. Open-Meteo confirms the weather supports the diagnosis. Qwen embeddings retrieve similar past claims and matching agronomy guidance from a vector database. A PDF claim is drafted and sent to a human adjuster for review."

### 0:35 – 1:30 — Live dashboard walkthrough (the meat)
**Visual:** Switch to the Streamlit dashboard. Click into the Ravi Kumar drought-cornfield claim. Cursor through the panels as you narrate.

**Voiceover (55 seconds, paced — show, don't rush):**
> "Here's a claim from Ravi Kumar in Tennessee. The AI assessment ran on a real Wikimedia photo of his cornfield: it identified maize, classified the damage as drought, scored severity at 85 out of 100, and listed the visible indicators it relied on."
>
> *(scroll to weather panel)*
>
> "The weather corroboration pulled 30 days of Open-Meteo data: 21 millimeters of rainfall, 14 days above 35 Celsius, a 17-day dry run. Qwen-Max agreed: corroborated at 0.9 strength."
>
> *(scroll to similar claims + fraud flags)*
>
> "Below it, the RAG layer surfaces similar past claims indexed in Alibaba DashVector. If a farmer's narrative was suspiciously close to a previous claim, the fraud check would raise a block flag here."
>
> *(scroll to localized message preview)*
>
> "And the message that goes back to the farmer is localized to their language — in this case, Hindi."
>
> *(click Approve & submit)*
>
> "On approve, the claim is forwarded to the insurer API, the status hops to submitted, and the farmer gets the notification."

### 1:30 – 2:00 — Architecture + Alibaba Cloud
**Visual:** Cut to terminal. Run the live curl:
```bash
curl -sS https://claimfarm-api-wovsxktpbk.ap-southeast-1.fcapp.run/healthz
```
Show `{"status":"ok"}`. Then cut to the Alibaba Cloud console showing the FC function "Running" + the OSS bucket with claim PDFs + the DashVector cluster.

**Voiceover (30 seconds):**
> "The backend runs on Alibaba Function Compute, region Singapore, behind a public HTTPS trigger. Photos and rendered PDFs land in Alibaba Object Storage. The vector store is Alibaba DashVector — the same product family as Qwen models, which means the agent's vision, reasoning, and embeddings all come from one ecosystem."

### 2:00 – 2:30 — Three Qwen capabilities
**Visual:** Switch to VS Code, briefly show app/clients/qwen.py (the chat + vision wrapper) for 5 seconds, then app/agents/damage_assessor.py (the structured prompt) for 10 seconds, then docs/architecture.md highlighting the "Qwen Cloud capability inventory" section.

**Voiceover:**
> "Three distinct Qwen Cloud capabilities are exercised: Qwen-VL for multimodal damage assessment, Qwen-Max for reasoning and multilingual rewriting, and Qwen text-embedding-v3 for retrieval and fraud detection. Each one has a structured Pydantic schema at its boundary — no hand-waving JSON."

### 2:30 – 2:55 — Impact & close
**Visual:** Title card with three numbers stacked: "500M farmers · 10 supported languages · 1 photo → 1 filed claim". Hold for 25 seconds.

**Voiceover:**
> "ClaimFarm collapses an inaccessible workflow into one photo. It's open source, it runs end-to-end on Alibaba Cloud, and it's built to be picked up by any micro-insurer or NGO operating in the field. Thanks for watching."

### 2:55 – 3:00 — Title card
**Visual:** Repo URL `github.com/hemnaath04/claimfarm` on a black card with the ClaimFarm wordmark. No audio.

## Production tips

- **Voiceover separately**: record the screen capture silent first, then record voiceover into a separate audio file (QuickTime → File → New Audio Recording), then drop them on the same iMovie timeline. Easier to retake voice without re-doing the screen.
- **Speak slowly**. Aim for 150 words/min — about the pace of TED talks. You have 450 words above. Time yourself.
- **No music** unless it's royalty-free (the rules forbid copyrighted music). YouTube Audio Library has good free options under "Cinematic" or "Ambient".
- **Captions help judges**: YouTube auto-captions are usually fine for this length — just review and fix the Qwen / Open-Meteo / DashVector names.
- **Upload as Unlisted while iterating**, then switch to Public on submission day.

## Hard rules sanity check

- [ ] Total runtime ≤ 3:00 (judges stop watching at 3:00 exactly)
- [ ] No third-party trademarks or copyrighted music
- [ ] Uploaded publicly on YouTube/Vimeo/Youku
- [ ] Captions visible (auto-generated is fine)
- [ ] Demo shows the Project actually working (not just slides)

## Suggested filename + title for upload

- **File**: `claimfarm-demo.mp4`
- **YouTube title**: `ClaimFarm — Crop insurance claims via WhatsApp photo (Qwen Cloud Hackathon, Track 4)`
- **YouTube description**:
  ```
  ClaimFarm turns a smallholder farmer's WhatsApp photo of a damaged crop
  into a filed insurance claim. Built on Qwen-VL-Max, Qwen-Max, and Qwen
  text-embedding-v3 (Qwen Cloud) with Alibaba Function Compute, OSS, and
  DashVector.

  Track 4 (Autopilot Agent) submission for the Global AI Hackathon
  Series with Qwen Cloud.

  Code: https://github.com/hemnaath04/claimfarm
  Live API: https://claimfarm-api-wovsxktpbk.ap-southeast-1.fcapp.run

  Open source, MIT licensed.
  ```

"""Adjuster review dashboard for ClaimFarm.

Run:
    uv run streamlit run dashboard/main.py
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from app.agents import fraud_check, past_claim_rag
from app.agents.multilingual import status_message
from app.clients import insurer
from app.models.claim import Claim, ClaimStatus
from app.storage import claims_repo


@st.cache_data(show_spinner=False)
def _cached_similar(claim_id: str, status_key: str) -> list[dict]:
    claim = claims_repo.get(claim_id)
    if claim is None:
        return []
    hits = past_claim_rag.find_similar(claim, k=3)
    return [
        {
            "id": h.metadata.get("claim_id"),
            "score": h.score,
            "status": h.metadata.get("status"),
            "loss": h.metadata.get("estimated_loss_usd"),
            "cause": h.metadata.get("damage_cause"),
            "crop": h.metadata.get("crop_type"),
            "phone": h.metadata.get("farmer_phone"),
        }
        for h in hits
    ]


@st.cache_data(show_spinner=False)
def _cached_fraud(claim_id: str, status_key: str) -> list[dict]:
    claim = claims_repo.get(claim_id)
    if claim is None:
        return []
    flags = fraud_check.check(claim)
    return [
        {
            "severity": f.severity,
            "message": f.message,
            "related": f.related_claim_id,
            "similarity": f.similarity,
        }
        for f in flags
    ]

st.set_page_config(
    page_title="ClaimFarm Adjuster",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ----------------------------------------------------------
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.6rem; }
      .cf-card {
        background: #161B23;
        border: 1px solid #232934;
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 10px;
      }
      .cf-card.selected { border-color: #7C5CFF; box-shadow: 0 0 0 1px #7C5CFF66; }
      .cf-pill {
        display: inline-block; padding: 2px 9px; border-radius: 999px;
        font-size: 11px; font-weight: 600; letter-spacing: 0.02em;
        text-transform: uppercase;
      }
      .pill-pending { background: #2c2410; color: #F2C463; }
      .pill-approved { background: #0f2a20; color: #5ED99B; }
      .pill-rejected { background: #2a1416; color: #F26C6C; }
      .pill-submitted { background: #1a2230; color: #7C9CFF; }
      .pill-paid { background: #1c2a16; color: #B5E66A; }
      .cf-label { color: #8E96A6; font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; }
      .cf-value { font-size: 15px; color: #E6E8EE; font-weight: 500; }
      .cf-id { font-family: ui-monospace, "SF Mono", monospace; color: #B6BCC9; font-size: 12px; }
      .cf-evidence {
        background: #0E1014; border-left: 3px solid #7C5CFF; padding: 8px 12px;
        font-style: italic; color: #B6BCC9; margin: 8px 0;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header --------------------------------------------------------------
st.markdown("## ClaimFarm — Adjuster Review")
st.caption(
    "Smallholder farmer crop-insurance claims, triaged by Qwen-VL + Open-Meteo + Qwen-Max."
)

# --- Sidebar -------------------------------------------------------------
with st.sidebar:
    st.markdown("### Filters")
    status_filter = st.selectbox(
        "Status",
        options=["all", "pending_review", "approved", "rejected", "submitted", "paid"],
        index=1,
    )
    if st.button("Refresh"):
        st.rerun()

    st.divider()
    st.markdown("### Stats")
    total = len(claims_repo.list_by_status())
    pending = len(claims_repo.list_by_status(ClaimStatus.pending_review))
    approved = len(claims_repo.list_by_status(ClaimStatus.approved))
    rejected = len(claims_repo.list_by_status(ClaimStatus.rejected))
    st.metric("Total", total)
    st.metric("Pending", pending)
    st.metric("Approved", approved)
    st.metric("Rejected", rejected)

# --- Data load -----------------------------------------------------------
status_arg = None if status_filter == "all" else ClaimStatus(status_filter)
rows = claims_repo.list_by_status(status_arg)

if not rows:
    st.info(
        "No claims yet. Seed one via `uv run python scripts/seed_demo_claim.py`."
    )
    st.stop()

# --- Selection state -----------------------------------------------------
if "selected_claim_id" not in st.session_state:
    st.session_state.selected_claim_id = rows[0].claim_id

list_col, detail_col = st.columns([1, 2], gap="medium")


def _status_pill(status: str) -> str:
    cls = {
        "pending_review": "pill-pending",
        "approved": "pill-approved",
        "rejected": "pill-rejected",
        "submitted": "pill-submitted",
        "paid": "pill-paid",
    }.get(status, "pill-pending")
    return f'<span class="cf-pill {cls}">{status.replace("_", " ")}</span>'


with list_col:
    st.markdown("#### Queue")
    for row in rows:
        selected = row.claim_id == st.session_state.selected_claim_id
        klass = "cf-card selected" if selected else "cf-card"
        st.markdown(
            f"""
            <div class="{klass}">
              <div class="cf-id">{row.claim_id}</div>
              <div style="margin: 4px 0 6px 0; font-weight: 600;">
                {row.farmer_name} &middot; {row.crop_type}
              </div>
              <div style="font-size: 12px; color: #8E96A6; margin-bottom: 6px;">
                ${row.estimated_loss_usd:,.0f} &middot;
                {row.created_at.strftime("%Y-%m-%d %H:%M")}
              </div>
              {_status_pill(row.status)}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            "Select" if not selected else "Selected",
            key=f"sel-{row.claim_id}",
            use_container_width=True,
            disabled=selected,
        ):
            st.session_state.selected_claim_id = row.claim_id
            st.rerun()

# --- Detail view ---------------------------------------------------------
claim = claims_repo.get(st.session_state.selected_claim_id)
row = claims_repo.get_row(st.session_state.selected_claim_id)

with detail_col:
    if claim is None or row is None:
        st.warning("Selected claim not found.")
        st.stop()

    st.markdown(f"#### {claim.farmer.name}'s {claim.crop_type} claim")
    st.markdown(
        f'<div class="cf-id">{claim.claim_id} &middot; '
        f"{claim.farmer.phone} &middot; lang {claim.farmer.language}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(_status_pill(claim.status.value), unsafe_allow_html=True)
    st.write("")

    photo_col, summary_col = st.columns([1, 1], gap="medium")
    with photo_col:
        st.markdown("**Submitted photo**")
        candidate_paths = [
            Path("data/eval/sample_drought_corn.jpg"),
        ]
        shown = False
        for u in claim.photo_urls:
            if u.startswith(("http://", "https://")):
                st.image(u, use_container_width=True)
                shown = True
                break
        if not shown:
            for p in candidate_paths:
                if p.exists():
                    st.image(str(p), use_container_width=True)
                    st.caption(f"(local sample — {p.name})")
                    shown = True
                    break
        if not shown:
            st.info("No photo attached.")

    with summary_col:
        st.markdown("**AI damage assessment**")
        st.markdown(
            f"<div><span class='cf-label'>Crop</span><br>"
            f"<span class='cf-value'>{claim.damage.crop_type}</span></div>",
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Cause", claim.damage.damage_cause.value)
        c2.metric("Severity", f"{claim.damage.severity}/100")
        c3.metric("Affected", f"{claim.damage.affected_area_pct}%")
        st.caption(f"Model confidence {int(claim.damage.confidence * 100)}%")
        if claim.damage.visible_indicators:
            st.markdown("**Visible indicators**")
            st.markdown("\n".join(f"- {x}" for x in claim.damage.visible_indicators))

    st.markdown("**Weather corroboration**")
    w = claim.weather
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precip (30d)", f"{w.total_precip_mm} mm")
    c2.metric("Days > 35°C", w.days_above_35c)
    c3.metric("Heavy-rain days", w.days_with_heavy_rain)
    c4.metric("Dry-day run", f"{w.consecutive_dry_days}d")
    corr = claim.corroboration
    pill_color = "#5ED99B" if corr.corroborated else "#F26C6C"
    st.markdown(
        f"<div class='cf-evidence' style='border-left-color: {pill_color}'>"
        f"<strong>{'Corroborated' if corr.corroborated else 'Not corroborated'}</strong> "
        f"(strength {corr.strength:.2f}) — {corr.evidence}</div>",
        unsafe_allow_html=True,
    )
    if corr.flags:
        st.markdown("**Flags**")
        for f in corr.flags:
            st.markdown(f"- :red[{f}]")

    if row.pdf_path and Path(row.pdf_path).exists():
        with open(row.pdf_path, "rb") as fh:
            st.download_button(
                "Download claim PDF",
                data=fh.read(),
                file_name=Path(row.pdf_path).name,
                mime="application/pdf",
            )

    st.divider()
    st.markdown("**Similar past claims** _(RAG over DashVector/Chroma)_")
    similar = _cached_similar(claim.claim_id, claim.status.value)
    if not similar:
        st.caption("No comparable claims yet — this one is the baseline.")
    else:
        for s in similar:
            st.markdown(
                f"""
                <div class="cf-card">
                  <div class="cf-id">{s["id"]}</div>
                  <div style="margin-top: 4px;">
                    {s["crop"]} / {s["cause"]} &middot; loss ${s["loss"]:,.0f}
                    &middot; {_status_pill(s["status"])} &middot; sim {s["score"]:.2f}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    flags = _cached_fraud(claim.claim_id, claim.status.value)
    if flags:
        st.markdown("**Risk flags**")
        for f in flags:
            color = "#F26C6C" if f["severity"] == "block" else "#F2C463"
            st.markdown(
                f"<div class='cf-evidence' style='border-left-color: {color}'>"
                f"<strong>{f['severity'].upper()}</strong> — {f['message']}</div>",
                unsafe_allow_html=True,
            )

    st.divider()
    st.markdown("**Adjuster decision**")
    notes = st.text_area("Notes", value=claim.adjuster_notes, height=80)
    b_approve, b_reject, b_info = st.columns(3)

    def _send_to_insurer(decision: ClaimStatus) -> None:
        claims_repo.update_status(claim.claim_id, decision, adjuster_notes=notes)
        if decision is ClaimStatus.approved:
            record = insurer.submit(claim)
            claims_repo.update_status(
                claim.claim_id,
                ClaimStatus.submitted,
                adjuster_notes=notes,
                insurer_claim_id=record["insurer_claim_id"],
            )
            terminal = record["status"]
            if terminal == "approved":
                claims_repo.update_status(
                    claim.claim_id, ClaimStatus.approved, adjuster_notes=notes
                )
            elif terminal == "rejected":
                claims_repo.update_status(
                    claim.claim_id, ClaimStatus.rejected, adjuster_notes=notes
                )
            st.success(
                f"Insurer responded {terminal} (id {record['insurer_claim_id']})"
            )

    if b_approve.button("Approve & submit", type="primary", use_container_width=True):
        _send_to_insurer(ClaimStatus.approved)
        st.rerun()

    if b_reject.button("Reject", use_container_width=True):
        claims_repo.update_status(
            claim.claim_id, ClaimStatus.rejected, adjuster_notes=notes
        )
        st.rerun()

    if b_info.button("Request more info", use_container_width=True):
        claims_repo.update_status(
            claim.claim_id, ClaimStatus.pending_review, adjuster_notes=notes
        )
        st.rerun()

    st.divider()
    st.markdown("**Localized farmer message preview**")
    try:
        msg = status_message(claim)
        st.markdown(f"<div class='cf-evidence'>{msg}</div>", unsafe_allow_html=True)
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Could not generate localized message: {exc}")

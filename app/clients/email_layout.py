"""Branded HTML layout for ClaimFarm transactional email.

Email clients are stuck in ~2005-era HTML/CSS — no flexbox/grid, many strip
`<style>` blocks, Gmail/Outlook block inline SVG. So this renders table-based
markup with fully-inline styles and a hosted PNG logo. One wrapper produces a
consistent ClaimFarm header (forest band + mark), body copy, an optional
"bulletproof" CTA button, and a footer, for every transactional message.
"""

from __future__ import annotations

import html as _html
import re

from app.config import get_settings

# Verdant Ledger palette (mirrors the web UI tokens).
FOREST = "#195B40"
FOREST_DEEP = "#0B2F22"
HARVEST = "#F4C95D"
IVORY = "#FFFCF5"
INK = "#1A2B22"
MUTED = "#5B6B62"
BORDER = "#E7E2D6"

_URL_RE = re.compile(r"^https?://\S+$")


def logo_url() -> str:
    """Absolute URL to the hosted PNG mark (SVG is blocked by Gmail/Outlook)."""
    base = get_settings().frontend_base_url.rstrip("/")
    return f"{base}/claimfarm-mark.png"


def _button(label: str, url: str) -> str:
    # VML fallback keeps the button shape in Outlook desktop.
    return f"""
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:24px 0;">
      <tr><td align="center" bgcolor="{FOREST}" style="border-radius:10px;">
        <a href="{_html.escape(url, quote=True)}"
           style="display:inline-block;padding:13px 28px;font-family:Inter,Segoe UI,Helvetica,Arial,sans-serif;
                  font-size:15px;font-weight:600;color:{IVORY};text-decoration:none;border-radius:10px;">
          {_html.escape(label)}
        </a>
      </td></tr>
    </table>"""


def render_email(
    *,
    heading: str,
    blocks: list[str],
    button: tuple[str, str] | None = None,
    footnote: str | None = None,
) -> str:
    """Render a full branded HTML email.

    `blocks` are paragraphs of already-trusted copy (we escape them). A `button`
    is an optional (label, url) rendered as a centered CTA. `footnote` is small
    muted text under the body (e.g. "didn't request this? ignore it").
    """
    body_parts: list[str] = []
    for b in blocks:
        body_parts.append(
            f'<p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:{INK};">'
            f"{_html.escape(b)}</p>"
        )
    if button is not None:
        body_parts.append(_button(button[0], button[1]))

    footer_extra = ""
    if footnote:
        footer_extra = (
            f'<p style="margin:20px 0 0;font-size:13px;line-height:1.5;color:{MUTED};">'
            f"{_html.escape(footnote)}</p>"
        )

    inner = "\n".join(body_parts)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only">
<title>{_html.escape(heading)}</title></head>
<body style="margin:0;padding:0;background:{IVORY};">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:{IVORY};">
 <tr><td align="center" style="padding:32px 16px;">
  <table role="presentation" width="560" cellspacing="0" cellpadding="0" border="0"
         style="width:560px;max-width:100%;background:#FFFFFF;border:1px solid {BORDER};border-radius:16px;overflow:hidden;">
   <!-- header band -->
   <tr><td style="background:{FOREST};padding:22px 32px;">
     <table role="presentation" cellspacing="0" cellpadding="0" border="0"><tr>
       <!-- Real brand mark embedded inline (cid attachment) so it renders
            without the client's "display images" prompt. The yellow cell is a
            backdrop in case the image is stripped. -->
       <td width="36" height="36"
           style="width:36px;height:36px;background:{HARVEST};border-radius:9px;
                  text-align:center;vertical-align:middle;">
         <img src="cid:claimfarm-logo" width="36" height="36" alt="ClaimFarm"
              style="display:block;border:0;border-radius:9px;">
       </td>
       <td style="vertical-align:middle;padding-left:10px;font-family:Inter,Segoe UI,Helvetica,Arial,sans-serif;
                  font-size:20px;font-weight:700;letter-spacing:-0.02em;color:{IVORY};">
         claimfarm
       </td>
     </tr></table>
   </td></tr>
   <!-- body -->
   <tr><td style="padding:32px;font-family:Inter,Segoe UI,Helvetica,Arial,sans-serif;">
     <h1 style="margin:0 0 18px;font-size:21px;line-height:1.3;font-weight:700;color:{FOREST_DEEP};">
       {_html.escape(heading)}
     </h1>
     {inner}
     {footer_extra}
   </td></tr>
   <!-- footer -->
   <tr><td style="padding:20px 32px;border-top:1px solid {BORDER};
                  font-family:Inter,Segoe UI,Helvetica,Arial,sans-serif;">
     <p style="margin:0;font-size:12px;line-height:1.5;color:{MUTED};">
       ClaimFarm · Photo-first crop insurance for smallholder farmers.<br>
       This is an automated message; please don't reply directly.
     </p>
   </td></tr>
  </table>
 </td></tr>
</table>
</body></html>"""


def render_plaintext(heading: str, blocks: list[str], button: tuple[str, str] | None) -> str:
    """Plain-text fallback (always include one — spam filters and some clients
    prefer it)."""
    lines = [heading, ""]
    lines.extend(blocks)
    if button is not None:
        lines += ["", f"{button[0]}: {button[1]}"]
    lines += ["", "ClaimFarm"]
    return "\n".join(lines)


def auto_blocks_from_text(body: str) -> tuple[list[str], tuple[str, str] | None]:
    """Turn an existing plain-text template body into (paragraphs, button).

    A line that is just a URL becomes the CTA button; everything else becomes
    paragraphs split on blank lines. Lets legacy TEMPLATES render branded
    without rewriting each one.
    """
    button: tuple[str, str] | None = None
    text_lines: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if _URL_RE.match(stripped) and button is None:
            button = ("Open ClaimFarm", stripped)
        else:
            text_lines.append(line)
    # Collapse into paragraphs on blank lines.
    blocks: list[str] = []
    buf: list[str] = []
    for line in text_lines:
        if line.strip():
            buf.append(line.strip())
        elif buf:
            blocks.append(" ".join(buf))
            buf = []
    if buf:
        blocks.append(" ".join(buf))
    return blocks, button

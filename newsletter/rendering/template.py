from __future__ import annotations

import html
from datetime import datetime

from newsletter.processing.ranker import ScoredItem
from newsletter.rendering.styles import COLORS, FONTS, CATEGORY_TAG_STYLES

NEWSLETTER_NAME = "Signal AI"


def _esc(text: str) -> str:
    return html.escape(text)


def _tag_pill(category: str) -> str:
    bg, fg = CATEGORY_TAG_STYLES.get(category, ("#f3f4f6", "#374151"))
    return (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:9999px;'
        f'font-size:11px;font-weight:600;letter-spacing:.3px;'
        f'background:{bg};color:{fg};">{_esc(category)}</span>'
    )


def _story_card(item: ScoredItem, compact: bool = False) -> str:
    date_str = item.published.strftime("%-d %b") if item.published else ""
    tag = _tag_pill(item.category_tag)

    if compact:
        return f"""
<tr>
  <td style="padding:12px 0;border-bottom:1px solid {COLORS['border']};">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="padding-bottom:4px;">{tag}</td>
        <td align="right" style="font-size:11px;color:{COLORS['text_muted']};">{_esc(date_str)}</td>
      </tr>
    </table>
    <p style="margin:4px 0 2px;font-size:14px;font-weight:600;line-height:1.4;">
      <a href="{_esc(item.url)}" style="color:{COLORS['text_primary']};text-decoration:none;">{_esc(item.title)}</a>
    </p>
    <p style="margin:0;font-size:13px;color:{COLORS['text_secondary']};line-height:1.5;">
      {_esc(item.summary)}
    </p>
    <p style="margin:6px 0 0;font-size:12px;color:{COLORS['text_muted']};">
      via <strong>{_esc(item.source)}</strong>
    </p>
  </td>
</tr>"""

    why_block = ""
    if item.why_it_matters:
        why_block = f"""
    <div style="margin-top:10px;padding:8px 12px;background:{COLORS['why_bg']};
                border-left:3px solid {COLORS['accent']};border-radius:0 4px 4px 0;">
      <p style="margin:0;font-size:12px;color:{COLORS['text_secondary']};font-style:italic;">
        <strong style="color:{COLORS['text_primary']};font-style:normal;">Why it matters:</strong> {_esc(item.why_it_matters)}
      </p>
    </div>"""

    return f"""
<tr>
  <td style="padding:16px;background:{COLORS['card_bg']};border-radius:8px;
             border:1px solid {COLORS['border']};margin-bottom:12px;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="padding-bottom:8px;">{tag}</td>
        <td align="right" style="font-size:11px;color:{COLORS['text_muted']};vertical-align:top;">
          {_esc(item.source)} &middot; {_esc(date_str)}
        </td>
      </tr>
    </table>
    <h3 style="margin:0 0 8px;font-size:15px;font-weight:700;line-height:1.4;">
      <a href="{_esc(item.url)}" style="color:{COLORS['text_primary']};text-decoration:none;">{_esc(item.title)}</a>
    </h3>
    <p style="margin:0;font-size:13px;color:{COLORS['text_secondary']};line-height:1.6;">
      {_esc(item.summary)}
    </p>
    {why_block}
  </td>
</tr>
<tr><td style="height:10px;"></td></tr>"""


def _top_story_block(item: ScoredItem) -> str:
    date_str = item.published.strftime("%-d %b") if item.published else ""
    tag = _tag_pill(item.category_tag)

    why_block = ""
    if item.why_it_matters:
        why_block = f"""
    <div style="margin-top:12px;padding:10px 14px;background:{COLORS['card_bg']};
                border-left:3px solid {COLORS['accent']};border-radius:0 4px 4px 0;">
      <p style="margin:0;font-size:13px;color:{COLORS['text_secondary']};font-style:italic;">
        <strong style="color:{COLORS['text_primary']};font-style:normal;">Why it matters:</strong> {_esc(item.why_it_matters)}
      </p>
    </div>"""

    return f"""
<tr>
  <td style="padding:20px;background:{COLORS['top_story_bg']};
             border:2px solid {COLORS['top_story_border']};border-radius:8px;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td>
          <span style="font-size:10px;font-weight:700;letter-spacing:1px;
                       color:{COLORS['accent']};text-transform:uppercase;">TOP STORY</span>
          &nbsp;&nbsp;{tag}
        </td>
        <td align="right" style="font-size:11px;color:{COLORS['text_muted']};">
          {_esc(item.source)} &middot; {_esc(date_str)}
        </td>
      </tr>
    </table>
    <h2 style="margin:10px 0 10px;font-size:18px;font-weight:800;line-height:1.3;">
      <a href="{_esc(item.url)}" style="color:{COLORS['text_primary']};text-decoration:none;">{_esc(item.title)}</a>
    </h2>
    <p style="margin:0;font-size:14px;color:{COLORS['text_secondary']};line-height:1.7;">
      {_esc(item.summary)}
    </p>
    {why_block}
    <p style="margin:14px 0 0;">
      <a href="{_esc(item.url)}"
         style="display:inline-block;padding:8px 16px;background:{COLORS['accent']};
                color:#ffffff;font-size:13px;font-weight:600;text-decoration:none;
                border-radius:6px;">Read more &rarr;</a>
    </p>
  </td>
</tr>
<tr><td style="height:14px;"></td></tr>"""


def _section_header(title: str) -> str:
    return f"""
<tr>
  <td style="padding:16px 0 8px;">
    <p style="margin:0;font-size:11px;font-weight:700;letter-spacing:1.5px;
              text-transform:uppercase;color:{COLORS['text_muted']};">{_esc(title)}</p>
    <hr style="margin:6px 0 0;border:none;border-top:2px solid {COLORS['border']};">
  </td>
</tr>"""


def build_email_html(items: list[ScoredItem], intro: str, date_str: str) -> str:
    # Partition items into sections
    top_story = next((i for i in items if i.score >= 9), None)
    main_items = [i for i in items if i != top_story and i.score >= 7]
    quick_hits = [i for i in items if i != top_story and i.score < 7]
    research_items = [i for i in items if i.is_arxiv]
    # Remove research items from main/quick if they have their own section
    if research_items:
        main_items = [i for i in main_items if not i.is_arxiv]
        quick_hits = [i for i in quick_hits if not i.is_arxiv]

    rows = ""

    if top_story:
        rows += _section_header("Top Story")
        rows += _top_story_block(top_story)

    if main_items:
        rows += _section_header("Main Stories")
        for item in main_items:
            rows += _story_card(item)

    if quick_hits:
        rows += _section_header("Quick Hits")
        rows += '<tr><td><table width="100%" cellpadding="0" cellspacing="0">'
        for item in quick_hits:
            rows += _story_card(item, compact=True)
        rows += "</table></td></tr>"

    if research_items:
        rows += _section_header("Research Spotlight")
        rows += '<tr><td><table width="100%" cellpadding="0" cellspacing="0">'
        for item in research_items[:4]:
            rows += _story_card(item, compact=True)
        rows += "</table></td></tr>"

    intro_html = "".join(f"<p>{_esc(p)}</p>" for p in intro.split("\n\n") if p.strip())

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{NEWSLETTER_NAME}</title>
</head>
<body style="margin:0;padding:0;background:{COLORS['bg']};font-family:{FONTS};">
<table width="100%" cellpadding="0" cellspacing="0" style="background:{COLORS['bg']};">
  <tr>
    <td align="center" style="padding:24px 16px;">
      <table width="600" cellpadding="0" cellspacing="0"
             style="max-width:600px;width:100%;">

        <!-- Header -->
        <tr>
          <td style="padding:20px 0 16px;border-bottom:2px solid {COLORS['border']};">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <h1 style="margin:0;font-size:22px;font-weight:800;
                             color:{COLORS['text_primary']};letter-spacing:-0.5px;">
                    {NEWSLETTER_NAME}
                  </h1>
                  <p style="margin:2px 0 0;font-size:12px;color:{COLORS['text_muted']};">
                    High-signal AI, daily.
                  </p>
                </td>
                <td align="right">
                  <p style="margin:0;font-size:12px;color:{COLORS['text_muted']};">{_esc(date_str)}</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Editor's Note -->
        <tr>
          <td style="padding:16px;margin-top:16px;background:{COLORS['card_bg']};
                     border-radius:8px;border-left:4px solid {COLORS['accent']};">
            <p style="margin:0 0 6px;font-size:10px;font-weight:700;letter-spacing:1px;
                      text-transform:uppercase;color:{COLORS['accent']};">Editor's Note</p>
            <div style="font-size:13px;color:{COLORS['text_secondary']};line-height:1.7;">
              {intro_html}
            </div>
          </td>
        </tr>
        <tr><td style="height:16px;"></td></tr>

        <!-- Stories -->
        {rows}

        <!-- Footer -->
        <tr>
          <td style="padding:20px 0;border-top:1px solid {COLORS['border']};
                     text-align:center;">
            <p style="margin:0;font-size:11px;color:{COLORS['text_muted']};">
              {NEWSLETTER_NAME} &middot; Powered by Claude API &amp; GitHub Actions
            </p>
            <p style="margin:4px 0 0;font-size:11px;color:{COLORS['text_muted']};">
              You're receiving this because you set it up. No unsubscribe needed.
            </p>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
</body>
</html>"""


def build_plain_text(items: list[ScoredItem], intro: str, date_str: str) -> str:
    lines = [
        f"{NEWSLETTER_NAME} — {date_str}",
        "=" * 50,
        "",
        intro,
        "",
    ]
    for i, item in enumerate(items, 1):
        lines += [
            f"{i}. [{item.category_tag}] {item.title}",
            f"   {item.summary}",
        ]
        if item.why_it_matters:
            lines.append(f"   Why it matters: {item.why_it_matters}")
        lines += [f"   Source: {item.source}", f"   {item.url}", ""]

    lines += ["—", f"{NEWSLETTER_NAME} · Powered by Claude API & GitHub Actions"]
    return "\n".join(lines)


def build_subject(items: list[ScoredItem], date_str: str) -> str:
    top = items[0] if items else None
    rest = len(items) - 1
    if top and rest > 0:
        short_title = top.title[:60] + ("..." if len(top.title) > 60 else "")
        return f"{NEWSLETTER_NAME} | {short_title} + {rest} more — {date_str}"
    elif top:
        return f"{NEWSLETTER_NAME} | {top.title[:70]} — {date_str}"
    return f"{NEWSLETTER_NAME} — {date_str}"

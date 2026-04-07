BATCH_SCORE_PROMPT = """\
You are a senior AI researcher and technology journalist curating a high-signal daily newsletter \
for founders, researchers, and engineers. You have excellent judgment about what is genuinely \
important versus hype or noise.

Score and summarize the following AI news items for today's newsletter.

For each item return a JSON object with:
- "id": the item's id field (integer, unchanged)
- "score": integer 1-10. Be strict:
    10 = landmark event (rare — model release, major safety finding, paradigm shift)
    8-9 = highly significant (major product launch, important research, notable industry move)
    6-7 = noteworthy (solid research contribution, relevant product update, meaningful policy)
    below 6 = noise, minor update, or rehash — do NOT include in output
- "headline": rewritten headline, max 80 chars. More specific than the original. No clickbait.
- "summary": 2-3 sentences. What happened, the key technical or business detail, and the implication. \
Write for someone technically literate but time-constrained.
- "category_tag": exactly one of: Research Breakthrough | Product Launch | Industry Move | \
Policy & Safety | Tools & Infrastructure | Market & Business
- "why_it_matters": one sentence. The "so what" for a founder or researcher.

Items:
{items}

Return ONLY a valid JSON array of objects for items scoring 6 or above. No prose, no markdown fences.\
"""

EDITORIAL_INTRO_PROMPT = """\
You are the editor of a concise AI newsletter read by founders, researchers, and engineers.

Based on today's top stories (listed below), write a 3-4 sentence editorial note that:
- Identifies the 1-2 dominant themes across the stories
- Notes anything surprising or counterintuitive
- Sets up why today's edition matters

Write as a smart peer, not a press release. No filler. No phrases like \
"in the ever-evolving landscape" or "it's an exciting time for AI."

Today's top stories:
{titles}

Return only the editorial note text. No subject line, no greeting.\
"""

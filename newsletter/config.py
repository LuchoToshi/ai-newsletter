from __future__ import annotations

CLAUDE_MODEL = "claude-sonnet-4-6"
MAX_ITEMS_PER_SOURCE = 10
ARXIV_MAX_ITEMS = 5
LOOKBACK_HOURS = 90  # ~3.5 days + buffer
TOP_N_FINAL = 20
MIN_RELEVANCE_SCORE = 6
MAX_TOKENS_PER_BATCH = 4000
CLAUDE_BATCH_SIZE = 15

# Keywords used to pre-filter ArXiv abstracts (case-insensitive)
ARXIV_KEYWORDS = [
    "language model",
    "reasoning",
    "agent",
    "alignment",
    "multimodal",
    "reinforcement learning",
    "foundation model",
    "llm",
    "transformer",
    "fine-tuning",
    "rlhf",
    "diffusion",
    "vision language",
    "chain of thought",
    "in-context learning",
    "autonomous agent",
    "tool use",
    "agentic",
    "retrieval augmented",
    "inference optimization",
    "model routing",
    "workflow automation",
]

RSS_SOURCES: list[dict] = [
    # Research labs
    {"name": "OpenAI Blog",          "url": "https://openai.com/blog/rss.xml",                                         "category": "lab"},
    {"name": "DeepMind Blog",        "url": "https://deepmind.google/blog/rss.xml",                                    "category": "lab"},
    {"name": "Google AI Blog",       "url": "https://blog.google/technology/ai/rss/",                                  "category": "lab"},
    {"name": "Meta AI Blog",         "url": "https://engineering.fb.com/category/ml-applications/feed/",              "category": "lab"},
    {"name": "HuggingFace Blog",     "url": "https://huggingface.co/blog/feed.xml",                                    "category": "tools"},
    # Research feeds
    {"name": "ArXiv cs.AI",          "url": "https://rss.arxiv.org/rss/cs.AI",                                        "category": "research", "arxiv": True},
    {"name": "ArXiv cs.LG",          "url": "https://rss.arxiv.org/rss/cs.LG",                                        "category": "research", "arxiv": True},
    {"name": "ArXiv cs.CL",          "url": "https://rss.arxiv.org/rss/cs.CL",                                        "category": "research", "arxiv": True},
    {"name": "The Gradient",         "url": "https://thegradient.pub/rss/",                                           "category": "research"},
    {"name": "Papers With Code",     "url": "https://paperswithcode.com/latest/rss",                                  "category": "research"},
    # Media
    {"name": "MIT Tech Review AI",   "url": "https://www.technologyreview.com/feed/",                                 "category": "media"},
    {"name": "TechCrunch AI",        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",          "category": "media"},
    {"name": "VentureBeat AI",       "url": "https://venturebeat.com/category/ai/feed/",                              "category": "media"},
    # Builders & thinkers
    {"name": "Latent Space",         "url": "https://www.latent.space/feed",                                          "category": "builders"},
    {"name": "swyx",                 "url": "https://swyx.io/rss.xml",                                                "category": "builders"},
    {"name": "Andrej Karpathy",      "url": "https://karpathy.github.io/feed.xml",                                    "category": "builders"},
    {"name": "Pieter Levels",        "url": "https://levels.io/rss/",                                                 "category": "builders"},
    {"name": "Daniel Gross",         "url": "https://danielgross.substack.com/feed",                                  "category": "builders"},
    {"name": "Logan Kilpatrick",     "url": "https://logankilpatrick.substack.com/feed",                              "category": "builders"},
    # Strategy
    {"name": "Stratechery",          "url": "https://stratechery.com/feed/",                                          "category": "strategy"},
]

# Hacker News Algolia search queries (stories with >50 points in last 24h)
HN_QUERIES = [
    "AI agents autonomous",
    "LLM infrastructure tooling",
    "AI startup founder",
    "multimodal model",
]
HN_MIN_POINTS = 50

"""Synthetic feedback generator for a fictional recipe app.

Themes are seeded so the demo always produces meaningful clusters:
- Payment failures (high negative)
- Slow onboarding (mixed)
- Recipe generation issues (mixed)
- Search bugs (negative)
- Missing dark mode (mild requests)
- Sync issues across devices (negative)
- Praise for AI recipe suggestions (positive)
- Pricing complaints (negative)
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class SyntheticFeedback:
    text: str
    source: str
    rating: int | None
    user_segment: str
    author: str
    created_at: datetime


SOURCES = ["app_store", "play_store", "zendesk", "nps", "interview"]
SEGMENTS = ["new_user", "power_user", "enterprise", "smb", "free_tier"]

# (template, sentiment_hint, rating_range)
PAYMENT_TEMPLATES = [
    ("Tried to subscribe to Pro but the payment {failed}. {extra}", "neg", (1, 2)),
    ("Card was charged but Pro features didn't unlock for {hours} hours. Support never replied.", "neg", (1, 2)),
    ("Got a 'payment declined' error even though my card works everywhere else. {extra}", "neg", (1, 2)),
    ("The subscribe button just spins forever. Tried on iOS and web, same thing.", "neg", (1, 3)),
    ("Charged twice for the same month — {extra}", "neg", (1, 2)),
]
ONBOARDING_TEMPLATES = [
    ("Took me {minutes} minutes to get past the dietary preferences screen. Way too many questions.", "neg", (2, 3)),
    ("Loved the recipes but the signup flow asks for my address?? Why?", "neg", (2, 3)),
    ("Onboarding is slow and asks for too much info before I can even try the app.", "neg", (1, 3)),
    ("Skipped most of the onboarding and now the app keeps prompting me to finish it.", "neg", (2, 3)),
    ("First-time experience felt confusing — I wasn't sure what the app actually did until step 4.", "neutral", (3, 3)),
]
RECIPE_GEN_TEMPLATES = [
    ("Asked for a vegan dinner with chickpeas, got a recipe with chicken. {extra}", "neg", (1, 3)),
    ("Recipe generator keeps suggesting the same 3 meals over and over.", "neg", (2, 3)),
    ("AI suggestions are great when they work but maybe 30% of the time the ingredients don't make sense.", "neutral", (3, 3)),
    ("Generated recipe had no measurements for half the ingredients.", "neg", (1, 3)),
    ("Love the AI recipe feature when it nails it — but it hallucinates ingredients I don't have.", "neutral", (3, 4)),
]
SEARCH_TEMPLATES = [
    ("Search doesn't find recipes I've literally saved. {extra}", "neg", (1, 3)),
    ("Searching for 'pasta' returns desserts. Something's broken.", "neg", (1, 2)),
    ("The search bar doesn't accept Unicode characters — can't search for crème brûlée.", "neg", (2, 3)),
    ("Filters in search don't actually filter. Vegan + under 30min still shows steak.", "neg", (1, 3)),
    ("Search is way too slow on Android — takes 5+ seconds.", "neg", (2, 3)),
]
DARK_MODE_TEMPLATES = [
    ("Please add dark mode, my eyes hurt at night cooking.", "neutral", (3, 4)),
    ("Dark mode would be a huge upgrade.", "neutral", (3, 4)),
    ("Why is there no dark theme in 2025?", "neg", (2, 3)),
    ("Loving the app overall, only wish: dark mode!", "pos", (4, 5)),
]
SYNC_TEMPLATES = [
    ("Saved recipes on iPhone don't sync to my iPad. {extra}", "neg", (1, 3)),
    ("Meal plan I built on the web is missing from the mobile app.", "neg", (1, 3)),
    ("Sync between devices is unreliable — sometimes works, sometimes silent failure.", "neg", (2, 3)),
    ("Lost my shopping list when I switched phones. No way to recover.", "neg", (1, 2)),
]
PRAISE_TEMPLATES = [
    ("The AI recipe suggestions are genuinely brilliant. Saved me so much time this week.", "pos", (5, 5)),
    ("Best meal planning app I've used. Recommended to my whole family.", "pos", (4, 5)),
    ("Love how it adapts to my pantry. Real game changer.", "pos", (5, 5)),
    ("The new weekly meal plan feature is fantastic.", "pos", (4, 5)),
    ("App is beautiful and easy to use. 5 stars.", "pos", (5, 5)),
]
PRICING_TEMPLATES = [
    ("$15/month for what is essentially a recipe app is too much.", "neg", (1, 2)),
    ("Free tier is so limited it's basically useless. Either make it free or be clear it's paid.", "neg", (1, 2)),
    ("Pricing went up without warning — felt sneaky.", "neg", (1, 2)),
    ("Pro features should include grocery integration at this price.", "neg", (2, 3)),
]

ALL_TEMPLATES: list[tuple[list, str]] = [
    (PAYMENT_TEMPLATES, "Payment failures"),
    (ONBOARDING_TEMPLATES, "Slow onboarding"),
    (RECIPE_GEN_TEMPLATES, "Recipe generation quality"),
    (SEARCH_TEMPLATES, "Search bugs"),
    (DARK_MODE_TEMPLATES, "Missing dark mode"),
    (SYNC_TEMPLATES, "Cross-device sync"),
    (PRAISE_TEMPLATES, "Praise for AI suggestions"),
    (PRICING_TEMPLATES, "Pricing complaints"),
]

# Approximate distribution weights so clusters have realistic relative sizes
WEIGHTS = [0.20, 0.12, 0.18, 0.14, 0.07, 0.10, 0.12, 0.07]

FILLERS = {
    "failed": ["failed silently", "timed out", "returned an error", "wouldn't go through"],
    "extra": [
        "Really frustrating.",
        "Please fix.",
        "Contacted support, no reply yet.",
        "Happens every time.",
        "Made me cancel.",
        "",
    ],
    "hours": ["6", "12", "24", "48"],
    "minutes": ["10", "15", "20", "25"],
}

FIRST_NAMES = ["Alex", "Sam", "Priya", "Jordan", "Maya", "Chen", "Riley", "Noor", "Diego", "Yuki"]
LAST_INITIALS = list("ABCDEFGHJKLMNPQRSTUVWXYZ")


def _fill(template: str) -> str:
    out = template
    for key, options in FILLERS.items():
        if "{" + key + "}" in out:
            out = out.replace("{" + key + "}", random.choice(options))
    return out.replace(" .", ".").replace("  ", " ").strip()


def _rand_author() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_INITIALS)}."


def generate(n: int = 500, seed: int | None = 42) -> list[SyntheticFeedback]:
    if seed is not None:
        random.seed(seed)

    out: list[SyntheticFeedback] = []
    now = datetime.now(timezone.utc)

    for _ in range(n):
        bucket_idx = random.choices(range(len(ALL_TEMPLATES)), weights=WEIGHTS, k=1)[0]
        templates, _theme = ALL_TEMPLATES[bucket_idx]
        template, _hint, (lo, hi) = random.choice(templates)
        text = _fill(template)

        source = random.choice(SOURCES)
        # NPS items often have no rating; interviews never; reviews always
        rating: int | None
        if source in {"app_store", "play_store"}:
            rating = random.randint(lo, hi)
        elif source == "nps":
            rating = random.randint(lo, hi) if random.random() < 0.5 else None
        else:
            rating = None

        days_ago = random.randint(0, 120)
        created = now - timedelta(days=days_ago, hours=random.randint(0, 23))

        out.append(
            SyntheticFeedback(
                text=text,
                source=source,
                rating=rating,
                user_segment=random.choice(SEGMENTS),
                author=_rand_author(),
                created_at=created,
            )
        )

    return out

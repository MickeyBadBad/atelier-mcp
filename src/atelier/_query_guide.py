"""Query format guide for asset search and AI generation services.

Each service has different query semantics — what the API actually
accepts, how it ranks results, what "no results" really means. An LLM
client driving this server can call ``asset_query_help`` to get a
service-specific cheat sheet before composing search queries, instead
of guessing and burning calls on bad inputs.

The guide for every service includes:

- ``how_it_searches``  — what backend the query string actually hits
- ``query_format``     — concrete advice: short noun phrases, single
                         keyword, prompt-style sentence, etc.
- ``categories``       — the canonical category taxonomy (if any)
- ``pitfalls``         — common mistakes that produce zero results
- ``examples``         — input → expected behavior, taken from real
                         calls during this fork's development
- ``fallback_ladder``  — what to try when the first query returns 0
"""
from __future__ import annotations
from typing import Any


_GUIDE: dict[str, dict[str, Any]] = {
    "polyhaven": {
        "kind": "PBR asset library (CC0, ~600 HDRIs / textures / models)",
        "how_it_searches": (
            "PolyHaven's /assets endpoint does NOT support free-text "
            "search. Only `categories` filtering. Pass a curated tag "
            "from the canonical taxonomy; everything else is ignored."
        ),
        "query_format": (
            "Use `categories=` with one canonical tag. Get the live "
            "list via `get_polyhaven_categories(asset_type=...)` first. "
            "Multiple categories can be comma-separated to AND-filter "
            "(e.g. `wood,floor`)."
        ),
        "categories": {
            "hdris": [
                "outdoor", "indoor", "studio", "skies", "sunrise-sunset",
                "night", "urban", "nature", "industrial",
            ],
            "textures": [
                "wood", "brick", "stone", "concrete", "metal", "fabric",
                "plaster", "tiles", "ceramic", "asphalt", "leaves",
                "wall", "floor", "roof",
            ],
            "models": [
                "decorative", "furniture", "indoor", "outdoor",
                "architectural", "vehicles", "natural", "props",
            ],
        },
        "pitfalls": [
            "Sending free text like 'dark walnut floor' returns nothing. "
            "It's not a search engine — it's a category filter.",
            "PolyHaven doesn't have many fabrics or leather. For those, "
            "fall through to ambientCG.",
            "Some categories combine poorly (e.g. `wood,outdoor` returns "
            "few results). Try one category first, then narrow.",
        ],
        "examples": [
            {
                "user_intent": "oak parquet floor for living room",
                "do": (
                    "search_polyhaven_assets(asset_type='textures', "
                    "categories='wood,floor')"
                ),
                "do_not": (
                    "search_polyhaven_assets(asset_type='textures', "
                    "categories='light oak parquet floor')  # not a category"
                ),
            },
            {
                "user_intent": "amber sunset HDRI for warm interior light",
                "do": (
                    "search_polyhaven_assets(asset_type='hdris', "
                    "categories='sunrise-sunset')"
                ),
            },
        ],
        "fallback_ladder": [
            "1. Try the most specific category match.",
            "2. If 0 results, drop to the parent category (`wood` instead "
            "of `wood,floor`).",
            "3. Still nothing → switch to ambientCG (more breadth on "
            "fabrics, leather, ceramics).",
            "4. Material genuinely missing → fall through to "
            "`apply_archviz_material` which auto-maps generic genres to "
            "the best-available PolyHaven asset.",
        ],
    },

    "ambientcg": {
        "kind": "PBR material library (CC0, ~2000 materials + HDRIs)",
        "how_it_searches": (
            "Free-text search across asset names, descriptions, and tags. "
            "Plus optional `category` filter and `asset_type` filter."
        ),
        "query_format": (
            "Short noun phrase or single material word: 'velvet', "
            "'terracotta', 'corduroy', 'rusted metal', 'concrete cracked'. "
            "Avoid color adjectives — ambientCG names tend to be "
            "color-neutral (apply tint via shader after download)."
        ),
        "categories": [
            "Bricks", "Wood", "Fabric", "Concrete", "Metal", "Plaster",
            "Plastic", "Stone", "Tiles", "Ceramic", "Leather", "Carpet",
            "Asphalt", "Roof", "Ground", "Plants",
        ],
        "pitfalls": [
            "Color adjectives rarely help: 'green velvet' → 0 hits, "
            "'velvet' → many. Apply color via shader.",
            "Don't pass a sentence: 'soft fabric for sofa upholstery' "
            "→ overspecified, ambient ranks badly.",
            "`asset_type` defaults to 'Material'; switch to 'HDRI' or "
            "'3DModel' when needed — these have far fewer assets.",
        ],
        "examples": [
            {
                "user_intent": "velvet upholstery for green sofa",
                "do": "search_ambientcg_assets(query='velvet')",
                "do_not": (
                    "search_ambientcg_assets(query='deep emerald green "
                    "velvet sofa upholstery')  # overspecified"
                ),
            },
            {
                "user_intent": "weathered red brick for accent wall",
                "do": (
                    "search_ambientcg_assets(query='brick', "
                    "category='Bricks')"
                ),
            },
        ],
        "fallback_ladder": [
            "1. Single material noun: 'velvet'.",
            "2. Try category filter alone: `category='Fabric'` no query.",
            "3. Switch `asset_type` (e.g. Material → HDRI).",
            "4. Cross-check PolyHaven if the material is structural "
            "(wood, brick, concrete) — PolyHaven often has higher-res.",
        ],
    },

    "sketchfab": {
        "kind": "Crowd-sourced 3D model marketplace (mixed licensing)",
        "how_it_searches": (
            "Full-text search over titles, descriptions, tags. "
            "ML-ranked. Many models are NOT downloadable — most users "
            "want `downloadable=True` to filter, but that drops ~70% "
            "of results."
        ),
        "query_format": (
            "Short noun phrase, 2-4 words, in English. Object-first: "
            "'leather sofa' beats 'a sofa made of leather'. Skip "
            "color adjectives unless central to the search ('crystal "
            "chandelier' yes, 'green chair' usually loses)."
        ),
        "categories": [
            "architecture", "art-abstract", "characters-creatures",
            "cultural-heritage-history", "electronics-gadgets", "fashion-style",
            "food-drink", "furniture-home", "music", "nature-plants",
            "news-politics", "people", "places-travel", "science-technology",
            "sports-fitness", "weapons-military",
        ],
        "pitfalls": [
            "Long queries return 0: 'mid-century walnut sideboard with "
            "tapered legs and brass pulls' → nothing. Drop to 'walnut "
            "sideboard'.",
            "`downloadable=True` is the default and is opinionated. "
            "Set False to widen the pool when zero downloadable results.",
            "Brand names rarely match (copyright-cleansed). Use generic "
            "noun: 'gaming chair' not 'Herman Miller'.",
            "Sketchfab credits the creator — check `license` on results "
            "before using commercially.",
        ],
        "examples": [
            {
                "user_intent": "linen sectional sofa for living room",
                "do": (
                    "search_sketchfab_models(query='linen sectional sofa', "
                    "categories='furniture-home', downloadable=True)"
                ),
                "do_not": (
                    "search_sketchfab_models(query='charcoal grey linen "
                    "modern sectional sofa with chaise')  # too long"
                ),
            },
            {
                "user_intent": "geometric wall sculpture for accent wall",
                "do": "search_sketchfab_models(query='geometric wall sculpture')",
            },
        ],
        "fallback_ladder": [
            "1. Short noun phrase + relevant category + downloadable=True.",
            "2. Drop downloadable=True (widens pool ~3x; check license "
            "manually).",
            "3. Drop the category (semantic mismatch is common).",
            "4. Drop the adjectives, keep the noun. 'sofa' alone returns "
            "thousands; pick by `view_count` or `like_count` from result.",
            "5. Switch strategy: AI-generate via `generate_3d_smart` if "
            "Sketchfab is empty.",
        ],
    },

    "tripo3d": {
        "kind": "AI text-to-3D / image-to-3D (paid credits, ~$0.03-$0.10/gen)",
        "how_it_searches": (
            "Not a search engine — generates from your prompt. Quality "
            "depends entirely on prompt craft."
        ),
        "query_format": (
            "Prompt-style English noun phrase with descriptive "
            "adjectives. Single object beats scenes. Style cues "
            "('photorealistic', 'low-poly', 'stylized') help. PBR "
            "is on by default for archviz."
        ),
        "categories": None,
        "pitfalls": [
            "Scene prompts ('a chair in a room') generate ONE mesh that "
            "looks like a chair-room hybrid. Always ask for ONE object.",
            "Color & material in prompt: Tripo3D bakes them into the "
            "PBR texture. Be specific: 'walnut wood' beats 'brown wood'.",
            "Polygon budget defaults to 30k. Drop to 10k for blockouts, "
            "raise to 50k+ for hero objects.",
            "Free-trial Hyper3D is cheaper for blockouts — use "
            "`generate_3d_smart(quality='fast', max_credits=0)` if "
            "you don't care about provider.",
        ],
        "examples": [
            {
                "user_intent": "ceramic vase for shelf styling",
                "do": (
                    "generate_tripo3d_text_to_3d(prompt='hand-thrown "
                    "ceramic vase with raku glaze, photorealistic', "
                    "pbr=True, target_size=0.25)"
                ),
            },
            {
                "user_intent": "low-poly background tree for matte painting",
                "do": (
                    "generate_tripo3d_text_to_3d(prompt='low-poly oak "
                    "tree, stylized, game-ready', model_version='P1-"
                    "20260311', face_limit=5000, target_size=4.0)"
                ),
            },
        ],
        "fallback_ladder": [
            "1. Refine prompt with material + style modifiers.",
            "2. Drop face_limit if model looks blobby.",
            "3. Switch model_version (v3.1 ↔ v2.5 give different "
            "aesthetic priors).",
            "4. If 3 attempts fail → switch to Meshy (different "
            "training data) or generate a 2D reference via "
            "`generate_image_openai` first then image-to-3D.",
        ],
    },

    "meshy": {
        "kind": "AI text-to-3D / image-to-3D (paid credits, two-stage refine)",
        "how_it_searches": (
            "Not a search engine — generates from prompt. Two-stage: "
            "preview generates fast, refine takes longer for higher "
            "quality + textures."
        ),
        "query_format": (
            "Prompt-style English. Meshy responds well to texture "
            "descriptors and can take longer prompts than Tripo3D. "
            "Topology hints ('quad-based', 'low-poly') affect output."
        ),
        "categories": None,
        "pitfalls": [
            "Multi-object / scene prompts ('a chair and a table') "
            "produce ONE hybrid mesh. ONE object per prompt — same "
            "rule as Tripo3D / Hyper3D.",
            "Skipping `enable_pbr` defaults to non-PBR — looks flat in "
            "Cycles.",
            "Negative prompts are silently ignored.",
            "Meshy preview-only is cheap but blobby; always refine for "
            "client-facing renders.",
            "Refine doubles cost. For quick iterations, do 3 previews "
            "and only refine the chosen one.",
        ],
        "examples": [
            {
                "user_intent": "Persian rug for floor",
                "do": (
                    "generate_meshy_text_to_3d(prompt='intricate Persian "
                    "rug, deep red and gold pattern, woven texture, "
                    "rectangular', enable_pbr=True, target_size=2.5)"
                ),
            },
        ],
        "fallback_ladder": [
            "1. Refine the prompt; add texture + topology hints.",
            "2. Drop to Tripo3D (different priors).",
            "3. Image-to-3D: generate a reference image first via "
            "`generate_image_openai`, then `generate_meshy_image_to_3d`.",
        ],
    },

    "hyper3d": {
        "kind": "AI text-to-3D / image-to-3D (free trial + paid tiers)",
        "how_it_searches": (
            "Not a search engine — generates from prompt or image. "
            "Has a generous free-trial key (no credit card) good for "
            "blockouts and prototyping."
        ),
        "query_format": (
            "Short prompt-style English. Hyper3D works best on simple, "
            "single-object prompts. Material descriptors land but are "
            "less important than topology cues."
        ),
        "categories": None,
        "pitfalls": [
            "Free-trial quota is shared globally; rate-limited at busy "
            "times (you'll see RATE_LIMITED ErrorCode).",
            "Multi-object prompts produce mesh hybrids — even worse "
            "than Tripo3D in this regard. Always single-object.",
            "Output topology is often dense; always run `mesh_cleanup` "
            "after import.",
        ],
        "examples": [
            {
                "user_intent": "blockout brass cube for layout",
                "do": (
                    "generate_hyper3d_text_to_3d(text_prompt='small "
                    "brass cube, simple geometry')"
                ),
            },
        ],
        "fallback_ladder": [
            "1. Wait + retry on RATE_LIMITED.",
            "2. Switch to Tripo3D (paid but reliable).",
            "3. For premium quality, use `generate_3d_smart"
            "(quality='best')` — it picks the best provider per "
            "your remaining budget.",
        ],
    },
}


def asset_query_help_data(service: str | None = None) -> dict[str, Any]:
    """Return a cheat sheet for one or all asset services.

    Parameters
    ----------
    service
        Lowercase service name: 'polyhaven', 'sketchfab', 'ambientcg',
        'tripo3d', 'meshy', 'hyper3d'. ``None`` or 'all' returns the
        full guide for every service.

    Returns
    -------
    dict with keys:
        - ``service``: the service requested (or 'all')
        - ``guide``: the cheat-sheet contents
        - ``available_services``: list of services with detailed guides
    """
    if service is None or service.lower() in {"all", "*", ""}:
        return {
            "service": "all",
            "guide": _GUIDE,
            "available_services": list(_GUIDE.keys()),
            "tip": (
                "Call asset_query_help(service='polyhaven') etc. for the "
                "full per-service guide. The most common pitfall: passing "
                "free-text prompts to PolyHaven (it only takes "
                "categories) and passing long sentences to Sketchfab "
                "(short noun phrases rank better)."
            ),
        }
    key = service.lower().strip()
    if key not in _GUIDE:
        return {
            "service": key,
            "guide": None,
            "available_services": list(_GUIDE.keys()),
            "error": (
                f"Unknown service '{service}'. Available: "
                f"{', '.join(_GUIDE.keys())}. Use service='all' for "
                f"the full guide."
            ),
        }
    return {
        "service": key,
        "guide": _GUIDE[key],
        "available_services": list(_GUIDE.keys()),
    }

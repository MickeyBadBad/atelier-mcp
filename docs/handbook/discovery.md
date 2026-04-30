# Discovery Questionnaire

> Sources: Norman — *The Design of Everyday Things*, revised edition (Basic Books, 2013); Norman — *Emotional Design: Why We Love (or Hate) Everyday Things* (Basic Books, 2004); Weinschenk — *100 Things Every Designer Needs to Know About People* (New Riders, 2011) and *100 MORE Things…* (New Riders, 2016); IDEO — *Method Cards: 51 Ways to Inspire Design* (William Stout Publishers, 2003); Fink — *How to Conduct Surveys: A Step-by-Step Guide*, 6th ed. (SAGE, 2016); Krosnick & Presser — "Question and Questionnaire Design", in *Handbook of Survey Research*, 2nd ed. (Emerald, 2010); Krosnick — "Response strategies for coping with the cognitive demands of attitude measures in surveys", *Applied Cognitive Psychology* 5 (1991), 213–236; Haire — "Projective Techniques in Marketing Research", *Journal of Marketing* 14 (1950), 649–656; Green & Rao — "Conjoint Measurement for Quantifying Judgmental Data", *Journal of Marketing Research* 8 (1971), 355–363; Wikipedia — *Likert scale* and *Projective test*.
> Last updated: 2026-04-29

## Purpose

The user is assumed to have **zero formal interior design background** (see project spec, "User Profile"). They cannot pick a Kelvin temperature, name a style, or rank materials by hand. They CAN, however, react: "I like this", "this feels too cold", "I want to feel hugged when I walk in". The Discovery questionnaire is the bridge — it converts that reactive vocabulary into a structured `taste-profile.json` that downstream tools (moodboard, materials, lighting, furniture placement) can act on without further user clarification. Discovery runs once at project start and is consumed by the `interior-discovery-intake` skill.

## The 5 question types

Each question may combine single-select, multi-select, and a free-text input, but its **type** is determined by what it elicits, not its UI shape. Every question type appears in the bank because direct questions alone systematically miss what non-experts actually want — Weinschenk (2011, "What people say they want is not always what they want") and Haire (1950) both show that direct self-report under-samples the unconscious drivers of preference (per Weinschenk 2011 §"People Self-Report"; per Haire 1950 instant-coffee shopping-list study).

### Type 1 — Direct preference

Hard constraints and demographic facts: who uses the space, hours of operation, budget ceiling, allergies, fixed equipment to keep. Use single-select for mutually exclusive options ("I rent / I own"), multi-select for taste-adjacent items, and free-text for anything the preset list might miss (per Fink 2016 §"Writing Questions" — open-ended fallbacks are recommended whenever the closed-set may be incomplete).

Direct questions are honest about hard facts (occupancy, budget) but unreliable for taste — so we rely on Types 2-5 for taste and reserve Type 1 for things the user can answer literally (per Norman 2013 §"The Seven Stages of Action": users can report goals reliably, but not the abstract attribute weights that determine what satisfies the goal).

### Type 2 — Projective ("how do you want to feel?")

Instead of "what style do you want?" we ask "walking in, what do you want to feel in the first second?" with answer chips like *warm-hugged · orderly · curious · relaxed · energized · professional* plus free input. This taps Norman's **visceral level** of emotional response — the pre-cognitive, first-second reaction (per Norman 2004 *Emotional Design*, ch. 1, "Three Levels of Processing: Visceral, Behavioral, Reflective"). Visceral answers are easier for non-experts to produce because they don't require style vocabulary, and they predict whether a finished space will feel right far better than self-reported style labels (per Weinschenk 2011 §"People Often Don't Know What They Want — They Have to Experience It").

The classic empirical anchor for projective questioning is Haire's 1950 instant-coffee shopping-list study: women asked directly about Nescafé gave neutral answers, but when asked to describe the *kind of person* who would shop a list containing Nescafé, they projected "lazy, disorganized" — preferences that direct questions missed entirely (per Haire 1950, *Journal of Marketing* 14:649–656). The same dynamic applies here: "do you like Japanese 侘寂?" is the direct question that fails; "what do you want to feel when you walk in?" is the projective question that works.

### Type 3 — Metaphor / scenario

"If this space were a movie, which? *Grand Budapest · Crouching Tiger · Interstellar · 1900 · Kikujiro · free-text*." Or "If this space were a drink, which?" Metaphor questions outsource the hard work of style mapping to **shared cultural shorthand**: the user doesn't need to know "1900s Wes Anderson maximalism" to pick *Grand Budapest*; the AI knows the mapping.

This pattern is documented in IDEO's *Method Cards* under the **Ask** category — cards such as *Word-Concept Association* and *Scenarios* are explicitly designed to surface cultural reference points users cannot articulate in the abstract (per IDEO Method Cards, "Ask" suit, 2003 ed.). It is also a textbook **projective technique** in the qualitative-research sense: the stimulus is ambiguous, so the user projects their preference onto it (per Wikipedia "Projective test"; per Haire 1950).

### Type 4 — Sensory / haptic

"Pick 3 textures you want to touch: *terracotta · linen · leather · velvet · polished marble · rough wood · brushed brass · concrete · fur rug · free-text*." Body memory beats visual memory for non-experts because the visual catalog is enormous and culturally biased ("Scandinavian" means different things in Beijing vs. Stockholm), but the haptic catalog is grounded in personal physical experience — everyone has touched linen and leather (per Weinschenk 2011 §"People Have Strong Sensory and Embodied Memories"; per Weinschenk 2016 *100 MORE Things*, ch. on **embodied cognition**). Haptic answers also constrain materials and finishes downstream more tightly than visual answers do — "I want to touch linen" rules out vinyl upholstery in a way that "I like cozy" does not.

### Type 5 — Visual A/B paired comparisons

Twelve pairs covering the project's style axes: warm/cool · sparse/full · wood/stone · high-contrast/soft · aged/new · symmetric/asymmetric · matte/glossy · ornate/plain · deep-color/pale · curved/rectilinear · natural-light/lamp-lit · open-plan/cellular. The user picks A or B per pair (with "neither" as a third option to prevent forced-choice noise).

Paired comparison is the workhorse of **conjoint analysis** (per Green & Rao 1971, *J. Marketing Research* 8:355–363; per Rao 2010, "Conjoint Analysis" review chapter). Conjoint asks people to express preference over multi-attribute alternatives instead of rating attributes one at a time, which avoids the well-known unreliability of direct attribute rating. It's the right tool here because (a) two side-by-side images are easy for non-experts to react to, (b) twelve pairs is enough to triangulate the six style axes used in `taste-profile.json`, and (c) the answers map directly to numeric axis values via simple weighted voting (see *Scoring algorithm* below).

## Free-input fallback (per question)

Every question — including A/B pairs — exposes a free-text input. This is mandated by Fink: closed-response sets always risk omitting the answer the respondent actually holds, and the open-ended fallback is the recognised remedy (per Fink 2016 §"Open-Ended vs. Closed-Ended Questions"). Free-text answers are concatenated into `free_text_notes` in the output and surfaced verbatim to downstream skills, so the user's own words ("reminds me of my grandfather's library") survive into moodboard prompts.

## Multi-select default for taste questions

Taste questions (Types 2-4) default to multi-select, not single-select. Forcing one answer ("pick the ONE feeling you want") induces what Krosnick calls **strong satisficing** — the respondent picks a plausible-looking option and abandons the introspection that would surface their real preferences (per Krosnick 1991, *Applied Cognitive Psychology* 5:213-236; per Krosnick & Presser 2010, *Handbook of Survey Research* ch. 9). Multi-select lets users mark every chip that resonates; the scoring step (below) treats each selection as a partial-credit vote.

Type 1 (hard facts) and Type 5 (paired A/B) keep single-select because the underlying construct is single-valued.

## Adaptive depth

| Mode | Length | When to use | Source |
|---|---|---|---|
| **Quick** | 5–7 q | "I just want to play / explore" — user is reluctant to commit | Shortest-acceptable-survey principle (per Fink 2016 §"How Long Should the Survey Be?": prefer the minimum that still answers the research question) |
| **Standard** | 12–15 q | Default for residential single-room or small commercial | Typical survey-research target of 10–15 minutes before measurable fatigue effects (per Krosnick & Presser 2010 §"Questionnaire Length"; per Jeong et al. 2023, *J. Development Economics*, who measured a 8–17% drop in reporting quality after a 15-minute load increase) |
| **Deep** | 25–30 q | Multi-space residential or full commercial fit-out — must justify the burden | Acceptable when user is highly motivated and stakes are high; Krosnick 1991 notes motivation modulates the satisficing threshold (per Krosnick 1991) |
| **Adaptive** | escape on convergence | Default wrapper around any mode | If the top style match exceeds 0.75 after question 12, AI offers to skip remaining questions — this prevents fatigue-driven satisficing on the tail (per Krosnick & Presser 2010 §"Satisficing"; the cure for satisficing is shortening the task, not exhorting the respondent) |

Default for new projects is **Deep** with the Adaptive escape valve enabled. The user can downgrade at any point ("just give me 5 questions").

## Mid-questionnaire feedback

Around question 12, the AI surfaces an inferred-style hypothesis to the user:

> "Based on your answers so far, you seem to lean toward 日式侘寂 (78%) and 北欧 (62%). Does that feel right, or am I missing something? *[Yes · Sort of, but X · No, redo]*"

Two reasons:

1. **Feedback principle** (per Norman 2013 ch. 1, "Six Fundamental Design Principles" — feedback). Norman: "Feedback must be immediate… Feedback also has to be informative." Letting a 30-question survey run silently and only revealing the result at the end gives the user no way to detect misalignment until it's too late to course-correct cheaply. Surfacing a tentative hypothesis at the half-way point is an instance of conversational feedback in the system-image-vs-user-mental-model loop (per Norman 2013 ch. 2, "The Gulf of Evaluation").

2. **Fatigue mitigation** (per Fink 2016 and Krosnick & Presser 2010). The mid-point check converts the second half of the survey from a fatigue-prone monologue into a refining dialogue — the user is now answering "is this hypothesis right?" rather than enduring more questions in the abstract, which reduces strong satisficing on the back half (per Krosnick 1991 §"Determinants of Satisficing").

If the user picks "No, redo", we treat questions 1-12 as noise and re-run with explicit-style flag set; if "Sort of, but X", we treat X as a free-text override that biases the remaining questions.

## Conflict trigger

When user statements within Discovery (or, later, anywhere in the project) contradict each other — e.g. user picked *Japanese 侘寂* on a metaphor question but later asks for *"more gold shine on the bar top"* — the AI fires a 1-2 question mid-stream clarifier rather than silently picking one.

The pattern is from IDEO's *Method Cards* under **Ask · Iterative Interviewing**: when a participant's stated preference and observed behavior diverge, the interviewer's job is to surface the divergence and ask a focused follow-up rather than averaging the two (per IDEO Method Cards, "Ask" suit, 2003 ed.). It also follows Norman's conceptual-model alignment principle: the user's mental model of the space drifts as they see options, and the AI's conceptual model must be updated explicitly, not silently averaged (per Norman 2013 ch. 1, "The Conceptual Model").

The clarifier is short (1-2 questions, not a re-questionnaire) and writes a free-text note into `taste-profile.json` rather than overwriting earlier answers — branching at this granularity is left to the L4 loop (see workflow spec).

## Output schema (taste-profile.json)

Schema version 1. The `interior-discovery-intake` skill writes this file at the project root; downstream skills read it.

```json
{
  "version": 1,
  "created_at": "2026-04-29T14:32:11Z",
  "project": "example-project",
  "depth": "deep",
  "explicit_style": null,
  "feeling_anchors": ["温暖", "想发呆", "安静"],
  "style_axes": {
    "warmth": 0.85,
    "complexity": 0.30,
    "natural_vs_polished": 0.70,
    "contrast": 0.40,
    "aged_vs_new": 0.60,
    "symmetric_vs_organic": 0.55
  },
  "material_pull": ["木", "亚麻", "粗陶"],
  "material_avoid": ["镀铬", "亮面瓷砖"],
  "style_match": {
    "日式侘寂": 0.78,
    "北欧": 0.62,
    "新中式": 0.41
  },
  "recommended_style": "日式侘寂",
  "free_text_notes": "用户提到喜欢京都旅行回忆；不喜欢上一家店里那种白光。"
}
```

| Field | Type | Source of derivation |
|---|---|---|
| `version` | int | Hard-coded by writer; bumped on schema change |
| `created_at` | ISO-8601 str | Writer timestamp |
| `project` | str | Project name passed by `interior-discovery-intake` |
| `depth` | enum: `quick` \| `standard` \| `deep` | User choice or default (`deep`) |
| `explicit_style` | str \| null | Set when user invokes the trigger-B skip ("I want Japanese 侘寂"); when non-null, downstream tools may bypass `style_match` |
| `feeling_anchors` | list[str] | Direct selections + free-text from Type 2 (projective) questions; preserved verbatim, no normalization |
| `style_axes` | object: 6 floats in [0, 1] | Computed from Type 5 paired comparisons via weighted voting (see *Scoring algorithm*); values closer to 1 lean toward the second pole listed in §"Type 5" (e.g. `warmth=0.85` means strongly warm; `complexity=0.30` means leans sparse) |
| `material_pull` | list[str] | Type 4 selections marked positive + Type 5 pairs that picked a wood/stone/fabric pole |
| `material_avoid` | list[str] | Type 4 chips left unselected when displayed and explicit "avoid" mentions in free text; never inferred silently — a chip not picked is not the same as a chip rejected |
| `style_match` | object: style_name → float in [0, 1] | Computed by nearest-neighbor matching of `style_axes` against the axis vectors stored in `docs/handbook/styles/<name>.md` frontmatter (see *Scoring algorithm*) |
| `recommended_style` | str | The argmax of `style_match`, or `explicit_style` when set |
| `free_text_notes` | str | Concatenation of every free-text input across the questionnaire, preserved verbatim, joined by ` · ` |

Schema is forward-compatible: extra keys MAY appear and consumers MUST ignore unknown keys.

## Scoring algorithm (high-level)

The pipeline runs in three stages once all answers are collected.

**Stage 1: Type 5 paired comparisons → `style_axes`.**
Each of the 12 paired-comparison questions maps to one or more style axes (a pair like "warm-amber lamp / cool-daylight room" maps purely to `warmth`; "ornate molding / plain wall" splits across `complexity` and `aged_vs_new`). Each pick contributes a +1 vote toward the chosen pole; "neither" contributes 0. Per-axis votes are summed and rescaled to [0, 1] via a simple linear normalization. This is a deliberately reduced form of conjoint analysis with a fixed additive part-worth model and unit weights — full conjoint estimation (per Green & Rao 1971) is overkill for 12 pairs, but the additive structure is the same.

**Stage 2: `style_axes` → `style_match`.**
Every style file in `docs/handbook/styles/<name>.md` carries a frontmatter axis vector — e.g. 日式侘寂 declares `{warmth: 0.7, complexity: 0.2, natural_vs_polished: 0.85, contrast: 0.25, aged_vs_new: 0.8, symmetric_vs_organic: 0.7}`. The user's `style_axes` vector is compared to each style vector via cosine similarity, then rescaled to [0, 1]. The result is `style_match`. This is a project-specific heuristic — there is no published benchmark for "interior-style matching from preference axes", and we deliberately avoid claiming validation; the choice is documented here so future maintainers can replace it with something better.

**Stage 3: Tie-breaking + recommendation.**
`recommended_style` is `argmax(style_match)` unless (a) `explicit_style` is set (user-declared override always wins), or (b) the top two scores are within 0.05 of each other, in which case the AI surfaces the tie to the user as part of mid-questionnaire feedback or final review rather than picking silently. Surfacing-on-tie is the same conceptual-model-alignment principle from the conflict-trigger section (per Norman 2013 ch. 2).

`feeling_anchors`, `material_pull`, and `material_avoid` are NOT used in the score — they ride along as constraints for downstream tools (moodboard generation, material palette, lighting Kelvin selection). Keeping them out of the style score prevents double-counting since the style files already correlate feeling and material vocabulary with their axis values.

## See also

- `project-types.md` — drives Type-1 questions (occupancy, hours, hard constraints)
- `styles/*.md` — style-axes ground truth used in Stage 2
- `materials.md` — Type-4 vocabulary source (material chip list)
- `space-types/*.md` — per-space mini-questionnaire content (trigger C)
- Workflow spec, `docs/dev/specs/2026-04-29-interior-design-workflow-design.md` §"Discovery Questionnaire — Detailed Spec" — upstream design intent

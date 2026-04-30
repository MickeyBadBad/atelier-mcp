# Interior Design Workflow — Slice 2: Discovery + Project Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use `- [ ]` syntax for tracking.

**Goal:** Stand up the Discovery questionnaire system, multi-space project scaffolding, and version snapshot infrastructure on top of the Slice 1 knowledge layer.

**Architecture:** Three new pure-Python modules backing six new MCP tools. Discovery question bank lives as YAML in `docs/handbook/discovery_bank.yaml` (user-editable, citation-tagged, mirrors `discovery.md`). Project state schema lives as a small Pydantic-style validator in `_project.py`. Snapshots are filesystem-only — copy `.blend` + sidecar JSONs into `snapshots/<phase>-<label>/`.

**Tech Stack:** Python 3.10+, FastMCP, pytest, PyYAML (already in deps via existing usage). No Blender API changes in this slice — project scaffolding writes scene-side via `execute_blender_code` initially; richer addon support comes in Slice 3.

---

## File Structure

| File | Responsibility |
|---|---|
| `docs/handbook/discovery_bank.yaml` | The 25-30 question bank (5 types) with weights and axis mappings |
| `src/blender_mcp/_discovery.py` | Pure-Python: load bank, run scoring, validate taste-profile, mid-questionnaire feedback logic |
| `src/blender_mcp/_project.py` | Pure-Python: project schema validation, taste-profile read/write, project-root resolution |
| `src/blender_mcp/_snapshots.py` | Pure-Python: snapshot directory layout, restore from snapshot, version-log append |
| `src/blender_mcp/server.py` | Add 7 MCP tools: `run_discovery_questionnaire`, `submit_questionnaire_answers`, `read_taste_profile`, `update_taste_profile`, `create_interior_project`, `version_snapshot`, `version_restore`, `version_log_entry` |
| `tests/test_discovery.py` | Unit tests for discovery module |
| `tests/test_project.py` | Unit tests for project module |
| `tests/test_snapshots.py` | Unit tests for snapshots module |
| `tests/test_discovery_mcp.py` | Smoke tests for the 7 new MCP tools |

---

## Task 1: Discovery Question Bank (YAML)

**Files:** Create `docs/handbook/discovery_bank.yaml`

The bank must mirror the 5 question types defined in `docs/handbook/discovery.md`. Every question is tagged with type, axes-it-influences, and source.

- [ ] **Step 1: Create the bank file**

```yaml
# Discovery Question Bank
#
# Mirrors docs/handbook/discovery.md. Each question carries:
#   - id: stable slug
#   - type: 1 | 2 | 3 | 4 | 5
#   - text_zh, text_en
#   - choices: list of {value, text_zh, text_en, axes: {axis_name: weight}}
#     OR (for type 5 paired) two options each with the same shape.
#   - free_input: bool (always true for taste; allowed for hard-constraint
#     questions too — fall back to natural language)
#   - multi_select: bool
#   - axes_influenced: list of style-axis names this question moves
#   - source: handbook/discovery.md anchor or external citation

version: 1
last_updated: "2026-04-29"

# === Type 1 — Direct preference (hard constraints) ===
- id: q01_who_uses
  type: 1
  text_zh: "这个空间主要给谁用？"
  text_en: "Who uses this space most?"
  multi_select: true
  free_input: true
  choices:
    - {value: self_only, text_zh: "我自己", text_en: "Me only"}
    - {value: family, text_zh: "我和家人", text_en: "Me and family"}
    - {value: occasional_guests, text_zh: "我自己 + 偶尔朋友", text_en: "Me + occasional guests"}
    - {value: customers, text_zh: "经营给客人", text_en: "Customers / clients"}
    - {value: team, text_zh: "团队办公", text_en: "Team / office"}
  axes_influenced: []
  source: "discovery.md §Type-1"

- id: q02_project_type
  type: 1
  text_zh: "项目类型？"
  text_en: "Project type?"
  multi_select: false
  free_input: false
  choices:
    - {value: residential_apartment, text_zh: "公寓", text_en: "Apartment"}
    - {value: residential_house, text_zh: "独栋住宅", text_en: "Detached house"}
    - {value: cafe_lounge, text_zh: "咖啡馆 / lounge", text_en: "Cafe / lounge"}
    - {value: restaurant_full_service, text_zh: "餐厅", text_en: "Restaurant"}
    - {value: retail_boutique, text_zh: "零售小店", text_en: "Retail boutique"}
    - {value: office_small, text_zh: "小型办公", text_en: "Small office"}
  axes_influenced: []
  source: "discovery.md §Type-1; project-types.md taxonomy"

- id: q03_total_area
  type: 1
  text_zh: "项目总面积大约多少 m²？"
  text_en: "What's the total area in m²?"
  multi_select: false
  free_input: true
  choices:
    - {value: under_30, text_zh: "30 m² 以下", text_en: "Under 30"}
    - {value: 30_60, text_zh: "30–60 m²", text_en: "30–60"}
    - {value: 60_100, text_zh: "60–100 m²", text_en: "60–100"}
    - {value: 100_200, text_zh: "100–200 m²", text_en: "100–200"}
    - {value: over_200, text_zh: "200 m² 以上", text_en: "Over 200"}
  axes_influenced: []
  source: "discovery.md §Type-1"

- id: q04_budget
  type: 1
  text_zh: "预算区间（人民币）？"
  text_en: "Budget range (RMB)?"
  multi_select: false
  free_input: true
  choices:
    - {value: under_30k, text_zh: "3万以下", text_en: "Under ¥30k"}
    - {value: 30_60k, text_zh: "3–6万", text_en: "¥30–60k"}
    - {value: 60_150k, text_zh: "6–15万", text_en: "¥60–150k"}
    - {value: 150_500k, text_zh: "15–50万", text_en: "¥150–500k"}
    - {value: over_500k, text_zh: "50万以上", text_en: "Over ¥500k"}
  axes_influenced: []
  source: "discovery.md §Type-1"

- id: q05_hard_constraints
  type: 1
  text_zh: "有哪些不能动的硬约束？（结构、家具、设备等）"
  text_en: "Hard constraints — what cannot be changed?"
  multi_select: true
  free_input: true
  choices:
    - {value: existing_furniture, text_zh: "现有家具不能换", text_en: "Existing furniture stays"}
    - {value: load_walls, text_zh: "承重墙不能动", text_en: "Load-bearing walls"}
    - {value: kitchen_position, text_zh: "厨房水电位置", text_en: "Kitchen plumbing/wiring position"}
    - {value: bath_position, text_zh: "卫浴位置", text_en: "Bathroom position"}
    - {value: structural_features, text_zh: "梁柱外露", text_en: "Exposed beams/columns"}
  axes_influenced: []
  source: "discovery.md §Type-1"

# === Type 2 — Projective ("how do you want to feel?") ===
- id: q06_first_second_feeling
  type: 2
  text_zh: "走进这个空间，你<u>第一秒</u>希望感受到什么？"
  text_en: "Walking in, what do you want to FEEL in the first second?"
  multi_select: true
  free_input: true
  choices:
    - {value: warm_hugged, text_zh: "温暖被拥抱", text_en: "Warmly hugged",
       axes: {warmth: 0.4, contrast: -0.1, complexity: 0.0}}
    - {value: orderly, text_zh: "整洁有秩序", text_en: "Orderly",
       axes: {warmth: 0.0, complexity: -0.3, symmetric_vs_organic: 0.3}}
    - {value: curious, text_zh: "好奇想探索", text_en: "Curious to explore",
       axes: {complexity: 0.4, contrast: 0.2}}
    - {value: relaxed, text_zh: "放松想发呆", text_en: "Relaxed",
       axes: {warmth: 0.3, contrast: -0.2, complexity: -0.1}}
    - {value: energized, text_zh: "兴奋想拍照", text_en: "Energized / photo-ready",
       axes: {contrast: 0.4, complexity: 0.3}}
    - {value: professional, text_zh: "专业被尊重", text_en: "Respected / professional",
       axes: {warmth: -0.1, complexity: -0.2, contrast: 0.1}}
  axes_influenced: [warmth, contrast, complexity, symmetric_vs_organic]
  source: "discovery.md §Type-2; Norman 2013"

- id: q07_evening_feeling
  type: 2
  text_zh: "夜晚使用这个空间时，希望像什么？"
  text_en: "Evening use — what should it feel like?"
  multi_select: false
  free_input: true
  choices:
    - {value: candle_glow, text_zh: "蜡烛光晕的温暖", text_en: "Candle glow warmth",
       axes: {warmth: 0.5, complexity: -0.1}}
    - {value: library_quiet, text_zh: "图书馆的安静", text_en: "Library quiet",
       axes: {warmth: 0.1, contrast: -0.2, complexity: 0.0}}
    - {value: jazz_bar, text_zh: "爵士酒吧的低调", text_en: "Jazz bar / low-key",
       axes: {warmth: 0.3, contrast: 0.3, complexity: 0.1}}
    - {value: clean_modern, text_zh: "干净现代的极简", text_en: "Clean modern minimalism",
       axes: {warmth: -0.1, complexity: -0.4, contrast: 0.1}}
  axes_influenced: [warmth, contrast, complexity]
  source: "discovery.md §Type-2"

# === Type 3 — Metaphor / scenario ===
- id: q08_movie
  type: 3
  text_zh: "如果这个空间是一部电影，会是哪部？"
  text_en: "If this space were a movie, which?"
  multi_select: true
  free_input: true
  choices:
    - {value: grand_budapest, text_zh: "《布达佩斯大饭店》", text_en: "The Grand Budapest Hotel",
       axes: {complexity: 0.4, contrast: 0.3, symmetric_vs_organic: 0.4, aged_vs_new: 0.4}}
    - {value: crouching_tiger, text_zh: "《卧虎藏龙》", text_en: "Crouching Tiger Hidden Dragon",
       axes: {warmth: 0.2, complexity: 0.2, natural_vs_polished: 0.4, aged_vs_new: 0.5}}
    - {value: interstellar, text_zh: "《星际穿越》", text_en: "Interstellar",
       axes: {warmth: -0.2, complexity: -0.3, contrast: 0.3, natural_vs_polished: -0.4}}
    - {value: 1900_pianist, text_zh: "《海上钢琴师》", text_en: "The Legend of 1900",
       axes: {warmth: 0.3, complexity: 0.3, aged_vs_new: 0.5}}
    - {value: kikujiro, text_zh: "《菊次郎的夏天》", text_en: "Kikujiro",
       axes: {warmth: 0.4, complexity: -0.2, natural_vs_polished: 0.3, contrast: -0.1}}
  axes_influenced: [warmth, complexity, contrast, symmetric_vs_organic, aged_vs_new, natural_vs_polished]
  source: "discovery.md §Type-3"

# === Type 4 — Sensory / haptic ===
- id: q09_textures
  type: 4
  text_zh: "选 3 种你想<u>触碰</u>的质感"
  text_en: "Pick 3 textures you want to touch"
  multi_select: true
  free_input: true
  choices:
    - {value: terracotta, text_zh: "粗陶", text_en: "Terracotta",
       axes: {warmth: 0.3, natural_vs_polished: 0.5, aged_vs_new: 0.3}}
    - {value: linen, text_zh: "亚麻", text_en: "Linen",
       axes: {warmth: 0.2, natural_vs_polished: 0.4}}
    - {value: leather, text_zh: "真皮", text_en: "Leather",
       axes: {warmth: 0.3, complexity: 0.1, aged_vs_new: 0.2}}
    - {value: velvet, text_zh: "天鹅绒", text_en: "Velvet",
       axes: {warmth: 0.3, complexity: 0.3, contrast: 0.2}}
    - {value: marble_polished, text_zh: "抛光大理石", text_en: "Polished marble",
       axes: {warmth: -0.1, complexity: 0.1, natural_vs_polished: -0.4}}
    - {value: rough_wood, text_zh: "粗木", text_en: "Rough wood",
       axes: {warmth: 0.4, natural_vs_polished: 0.5, aged_vs_new: 0.4}}
    - {value: brushed_brass, text_zh: "拉丝黄铜", text_en: "Brushed brass",
       axes: {warmth: 0.3, complexity: 0.2, aged_vs_new: 0.2}}
    - {value: concrete, text_zh: "清水混凝土", text_en: "Raw concrete",
       axes: {warmth: -0.3, complexity: -0.2, natural_vs_polished: 0.2}}
    - {value: fur_rug, text_zh: "绒毛地毯", text_en: "Fur rug",
       axes: {warmth: 0.5, complexity: 0.2}}
  axes_influenced: [warmth, complexity, contrast, natural_vs_polished, aged_vs_new]
  source: "discovery.md §Type-4; Weinschenk 2011"

# === Type 5 — Visual A/B paired comparisons ===
- id: q10_warm_vs_cool
  type: 5
  text_zh: "凭直觉选偏好：暖光 vs 冷光"
  text_en: "Gut pick: warm vs cool light"
  options:
    - {value: warm, text_zh: "暖光（2200–2700K）", text_en: "Warm (2200–2700K)",
       axes: {warmth: 0.5}}
    - {value: cool, text_zh: "冷光（4000K+）", text_en: "Cool (4000K+)",
       axes: {warmth: -0.5}}
  axes_influenced: [warmth]
  source: "discovery.md §Type-5; Green & Rao 1971"

- id: q11_sparse_vs_full
  type: 5
  text_zh: "极简 vs 丰富"
  text_en: "Sparse vs full"
  options:
    - {value: sparse, text_zh: "极简：留白 + 少件家具", text_en: "Sparse: negative space",
       axes: {complexity: -0.5}}
    - {value: full, text_zh: "丰富：层叠的细节", text_en: "Full: layered detail",
       axes: {complexity: 0.5}}
  axes_influenced: [complexity]
  source: "discovery.md §Type-5"

- id: q12_wood_vs_stone
  type: 5
  text_zh: "木质 vs 石材"
  text_en: "Wood vs stone"
  options:
    - {value: wood, text_zh: "温润的木", text_en: "Warm wood",
       axes: {warmth: 0.3, natural_vs_polished: 0.3}}
    - {value: stone, text_zh: "凉硬的石", text_en: "Cool stone",
       axes: {warmth: -0.3, natural_vs_polished: -0.2}}
  axes_influenced: [warmth, natural_vs_polished]
  source: "discovery.md §Type-5"

- id: q13_high_vs_soft_contrast
  type: 5
  text_zh: "高对比 vs 柔和"
  text_en: "High contrast vs soft"
  options:
    - {value: high, text_zh: "黑白分明", text_en: "Bold contrast",
       axes: {contrast: 0.5}}
    - {value: soft, text_zh: "灰阶过渡", text_en: "Soft gradients",
       axes: {contrast: -0.5}}
  axes_influenced: [contrast]
  source: "discovery.md §Type-5"

- id: q14_aged_vs_new
  type: 5
  text_zh: "老旧 vs 崭新"
  text_en: "Aged vs new"
  options:
    - {value: aged, text_zh: "有岁月感的旧物", text_en: "Aged / patina",
       axes: {aged_vs_new: 0.5}}
    - {value: new, text_zh: "崭新干净", text_en: "Crisp / new",
       axes: {aged_vs_new: -0.5}}
  axes_influenced: [aged_vs_new]
  source: "discovery.md §Type-5"

- id: q15_symmetric_vs_organic
  type: 5
  text_zh: "对称 vs 错落"
  text_en: "Symmetric vs organic"
  options:
    - {value: symmetric, text_zh: "整齐对称", text_en: "Symmetric",
       axes: {symmetric_vs_organic: 0.5}}
    - {value: organic, text_zh: "自然错落", text_en: "Organic",
       axes: {symmetric_vs_organic: -0.5}}
  axes_influenced: [symmetric_vs_organic]
  source: "discovery.md §Type-5"

- id: q16_natural_vs_polished
  type: 5
  text_zh: "天然质感 vs 精致打磨"
  text_en: "Natural vs polished"
  options:
    - {value: natural, text_zh: "原木 + 亚麻 + 粗陶", text_en: "Raw materials",
       axes: {natural_vs_polished: 0.5}}
    - {value: polished, text_zh: "抛光大理石 + 镜面金属", text_en: "Polished surfaces",
       axes: {natural_vs_polished: -0.5}}
  axes_influenced: [natural_vs_polished]
  source: "discovery.md §Type-5"

- id: q17_tight_vs_open
  type: 5
  text_zh: "紧凑包裹感 vs 开阔通透"
  text_en: "Cocoon vs open"
  options:
    - {value: tight, text_zh: "包裹的私密", text_en: "Cocooned / intimate",
       axes: {warmth: 0.2, complexity: 0.1}}
    - {value: open, text_zh: "通透的开阔", text_en: "Open / airy",
       axes: {warmth: -0.1, complexity: -0.2}}
  axes_influenced: [warmth, complexity]
  source: "discovery.md §Type-5"

- id: q18_dim_vs_bright
  type: 5
  text_zh: "昏暗 vs 明亮"
  text_en: "Dim vs bright"
  options:
    - {value: dim, text_zh: "昏暗的氛围", text_en: "Dim / moody",
       axes: {contrast: 0.3, warmth: 0.2}}
    - {value: bright, text_zh: "明亮的清新", text_en: "Bright / fresh",
       axes: {contrast: -0.2, warmth: -0.1}}
  axes_influenced: [warmth, contrast]
  source: "discovery.md §Type-5"

# === Type 2 again — projective deepening ===
- id: q19_dont_want
  type: 2
  text_zh: "你<u>最不想</u>这个空间像什么？"
  text_en: "What do you most NOT want it to look like?"
  multi_select: true
  free_input: true
  choices:
    - {value: hospital, text_zh: "医院/办公室", text_en: "Hospital / office",
       axes: {warmth: 0.3, natural_vs_polished: 0.2}}
    - {value: showroom, text_zh: "样板间", text_en: "Show flat",
       axes: {complexity: 0.2, aged_vs_new: 0.2}}
    - {value: cluttered, text_zh: "杂乱拥挤", text_en: "Cluttered",
       axes: {complexity: -0.4}}
    - {value: dated, text_zh: "过时土气", text_en: "Dated / tacky",
       axes: {aged_vs_new: -0.2}}
    - {value: cold, text_zh: "冰冷无情", text_en: "Cold / impersonal",
       axes: {warmth: 0.4}}
  axes_influenced: [warmth, complexity, natural_vs_polished, aged_vs_new]
  source: "discovery.md §Type-2"

- id: q20_guest_feeling
  type: 2
  text_zh: "如果是商业空间：你想让客人感受到什么？（住宅可跳过）"
  text_en: "Commercial only: what should guests feel?"
  multi_select: true
  free_input: true
  choices:
    - {value: welcomed, text_zh: "被欢迎被招待", text_en: "Welcomed / hosted",
       axes: {warmth: 0.4}}
    - {value: special, text_zh: "这地方特别", text_en: "This place is special",
       axes: {complexity: 0.3, contrast: 0.2}}
    - {value: photo_worthy, text_zh: "想拍照分享", text_en: "Photo-worthy",
       axes: {contrast: 0.3, complexity: 0.3}}
    - {value: linger, text_zh: "想多坐一会", text_en: "Want to linger",
       axes: {warmth: 0.4, contrast: -0.1}}
    - {value: respected, text_zh: "被认真对待", text_en: "Taken seriously",
       axes: {complexity: -0.1, contrast: 0.1}}
  axes_influenced: [warmth, complexity, contrast]
  source: "discovery.md §Type-2"

# === Lifestyle (Type 1, gating later questions) ===
- id: q21_morning_or_evening
  type: 1
  text_zh: "你更多是早晨型还是夜晚型用户？"
  text_en: "Morning person or evening person?"
  multi_select: false
  free_input: true
  choices:
    - {value: morning, text_zh: "早晨", text_en: "Morning"}
    - {value: evening, text_zh: "夜晚", text_en: "Evening"}
    - {value: both, text_zh: "两者都有", text_en: "Both"}
  axes_influenced: []
  source: "discovery.md §Type-1 (lifestyle)"

- id: q22_entertain
  type: 1
  text_zh: "（住宅）多久招待客人一次？"
  text_en: "(Residential) How often do you entertain?"
  multi_select: false
  free_input: true
  choices:
    - {value: never, text_zh: "几乎不", text_en: "Almost never"}
    - {value: monthly, text_zh: "每月一两次", text_en: "1-2× / month"}
    - {value: weekly, text_zh: "每周", text_en: "Weekly"}
    - {value: more, text_zh: "更频繁", text_en: "More often"}
  axes_influenced: []
  source: "discovery.md §Type-1 (lifestyle)"

# === Type 3 — analogical scenes ===
- id: q23_reference_place
  type: 3
  text_zh: "你去过的、印象最深的一个空间是哪里？为什么？（自由文本）"
  text_en: "A real place you've been that left a strong impression — describe it (free text)"
  multi_select: false
  free_input: true
  free_input_only: true
  axes_influenced: []
  source: "discovery.md §Type-3"

# === Type 4 — sensory deepening ===
- id: q24_sound
  type: 4
  text_zh: "在这个空间里你最想听到什么？"
  text_en: "What sound do you want here?"
  multi_select: false
  free_input: true
  choices:
    - {value: silence, text_zh: "完全的安静", text_en: "Total quiet",
       axes: {warmth: 0.0, complexity: -0.2}}
    - {value: music, text_zh: "背景音乐", text_en: "Background music",
       axes: {warmth: 0.2}}
    - {value: chatter, text_zh: "人声 + 杯碟", text_en: "Chatter + clinking",
       axes: {warmth: 0.3, complexity: 0.2}}
    - {value: nature, text_zh: "雨声 / 风声", text_en: "Rain / wind",
       axes: {natural_vs_polished: 0.3, warmth: 0.1}}
  axes_influenced: [warmth, complexity, natural_vs_polished]
  source: "discovery.md §Type-4"

# === Closing free-text ===
- id: q25_anything_else
  type: 1
  text_zh: "还有别的想法 / 必须的偏好 / 担心的事？"
  text_en: "Anything else — preferences, worries, must-haves?"
  multi_select: false
  free_input: true
  free_input_only: true
  axes_influenced: []
  source: "discovery.md §Type-1 (closing)"
```

- [ ] **Step 2: Verify the YAML parses**

```bash
.venv/bin/python -c "import yaml; data = yaml.safe_load(open('docs/handbook/discovery_bank.yaml')); print(f'questions: {len([d for d in data if isinstance(d, dict) and d.get(\"id\")])}')"
```

Expected: prints `questions: 25` or thereabouts.

- [ ] **Step 3: Commit**

```bash
git add docs/handbook/discovery_bank.yaml
git commit -m "feat(handbook): discovery_bank.yaml — 25-question Deep questionnaire"
```

---

## Task 2: `_discovery.py` — Failing Tests

**Files:** Create `tests/test_discovery.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for the discovery questionnaire module."""
from __future__ import annotations

import pytest

from blender_mcp._discovery import (
    DiscoveryError,
    Depth,
    list_questions,
    score_answers,
    validate_answer_payload,
    new_session,
    midpoint_inferred_style,
    AXES,
)


def test_axes_canonical_set():
    """The 6 style axes are stable contract — downstream skills depend on them."""
    expected = {"warmth", "complexity", "natural_vs_polished",
                "contrast", "aged_vs_new", "symmetric_vs_organic"}
    assert set(AXES) == expected


def test_list_questions_loads_bank():
    qs = list_questions(Depth.DEEP)
    assert len(qs) >= 20
    # Each question has the expected shape
    for q in qs:
        assert "id" in q
        assert "type" in q
        assert q["type"] in (1, 2, 3, 4, 5)
        assert "text_zh" in q
        assert "text_en" in q


def test_list_questions_quick_is_subset():
    quick = list_questions(Depth.QUICK)
    deep = list_questions(Depth.DEEP)
    assert len(quick) < len(deep)
    quick_ids = {q["id"] for q in quick}
    deep_ids = {q["id"] for q in deep}
    assert quick_ids.issubset(deep_ids)


def test_validate_answer_payload_rejects_unknown_id():
    with pytest.raises(DiscoveryError):
        validate_answer_payload({"q99_does_not_exist": "warm"})


def test_validate_answer_payload_rejects_unknown_choice():
    with pytest.raises(DiscoveryError):
        validate_answer_payload({"q10_warm_vs_cool": "purple_unicorn"})


def test_validate_answer_payload_accepts_free_text():
    # q23 is free_input_only — string answer accepted
    out = validate_answer_payload({"q23_reference_place": "Kyoto temple I visited"})
    assert "q23_reference_place" in out


def test_score_answers_produces_axes_in_unit_range():
    answers = {
        "q06_first_second_feeling": ["warm_hugged", "relaxed"],
        "q08_movie": ["kikujiro"],
        "q09_textures": ["linen", "rough_wood", "terracotta"],
        "q10_warm_vs_cool": "warm",
        "q11_sparse_vs_full": "sparse",
        "q12_wood_vs_stone": "wood",
        "q14_aged_vs_new": "aged",
        "q16_natural_vs_polished": "natural",
    }
    profile = score_answers(answers)
    assert "style_axes" in profile
    for axis_name, value in profile["style_axes"].items():
        assert -1.0 <= value <= 1.0, f"axis {axis_name} out of unit range: {value}"
    # Heuristic: this answer set should bias toward warmth + natural
    assert profile["style_axes"]["warmth"] > 0.2
    assert profile["style_axes"]["natural_vs_polished"] > 0.2
    assert profile["style_axes"]["complexity"] < 0.0


def test_score_answers_includes_style_match():
    """style_match is the projection from axes onto the styles/<name>.md axis vectors."""
    answers = {
        "q10_warm_vs_cool": "warm",
        "q12_wood_vs_stone": "wood",
        "q16_natural_vs_polished": "natural",
        "q11_sparse_vs_full": "sparse",
    }
    profile = score_answers(answers)
    assert "style_match" in profile
    assert isinstance(profile["style_match"], dict)
    # At least one style score
    assert len(profile["style_match"]) >= 1


def test_new_session_returns_session_id_and_first_batch():
    session = new_session(depth=Depth.DEEP)
    assert "session_id" in session
    assert "batch" in session
    assert "depth" in session
    assert len(session["batch"]) >= 1


def test_midpoint_inferred_style_returns_top_match():
    """At ~12 questions in, AI surfaces a hypothesis."""
    answers = {
        "q10_warm_vs_cool": "warm",
        "q11_sparse_vs_full": "sparse",
        "q12_wood_vs_stone": "wood",
        "q16_natural_vs_polished": "natural",
        "q09_textures": ["linen", "rough_wood"],
    }
    inferred = midpoint_inferred_style(answers)
    assert "top_styles" in inferred
    assert isinstance(inferred["top_styles"], list)
    assert "needs_more_questions" in inferred  # bool — convergence flag
```

- [ ] **Step 2: Run — expect ImportError**

```bash
.venv/bin/pytest tests/test_discovery.py -v
```

Expected: ImportError.

---

## Task 3: `_discovery.py` — Implementation

**Files:** Create `src/blender_mcp/_discovery.py`

- [ ] **Step 1: Write the module**

```python
"""Pure-Python discovery questionnaire engine.

Loads the question bank from docs/handbook/discovery_bank.yaml. Provides:

- list_questions(depth) — return the questions for a given depth
- validate_answer_payload(answers) — schema-check a dict of answers
- score_answers(answers) — compute taste profile (axes + style_match)
- new_session(depth) — create a session, return first batch
- midpoint_inferred_style(answers_so_far) — surface top-style hypothesis

No Blender / MCP dependencies — pure Python so unit tests run fast.

Style axis vector ground-truth lives in style chapter frontmatter; this
module hardcodes initial vectors for the styles that ship in Slice 1
(scandinavian) and a small built-in set for the rest, until each style
chapter is added to the handbook.
"""
from __future__ import annotations

import enum
import math
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class DiscoveryError(Exception):
    """Raised on invalid bank, invalid answer payload, or scoring errors."""


class Depth(str, enum.Enum):
    QUICK = "quick"        # 5–7 questions
    STANDARD = "standard"  # 12–15 questions
    DEEP = "deep"          # 25–30 questions
    ADAPTIVE = "adaptive"  # quick start, extends if convergence is poor


AXES = (
    "warmth",
    "complexity",
    "natural_vs_polished",
    "contrast",
    "aged_vs_new",
    "symmetric_vs_organic",
)


# Style ground-truth vectors. Each style is a 6-axis point in [-1, 1]^6.
# These are derived from the corresponding styles/<name>.md chapter
# (when it lands) by reading its frontmatter; in Slice 1 only
# scandinavian.md exists, so only that style is fully grounded — the
# others are placeholders pending Slice 5.
STYLE_VECTORS: Dict[str, Dict[str, float]] = {
    "scandinavian": {
        "warmth": 0.5,
        "complexity": -0.3,
        "natural_vs_polished": 0.5,
        "contrast": 0.0,
        "aged_vs_new": -0.1,
        "symmetric_vs_organic": -0.1,
    },
    "japanese_wabi_sabi": {
        "warmth": 0.3,
        "complexity": -0.5,
        "natural_vs_polished": 0.6,
        "contrast": -0.2,
        "aged_vs_new": 0.4,
        "symmetric_vs_organic": -0.3,
    },
    "modern_minimal": {
        "warmth": -0.1,
        "complexity": -0.5,
        "natural_vs_polished": -0.2,
        "contrast": 0.2,
        "aged_vs_new": -0.4,
        "symmetric_vs_organic": 0.3,
    },
    "speakeasy": {
        "warmth": 0.5,
        "complexity": 0.4,
        "natural_vs_polished": 0.0,
        "contrast": 0.5,
        "aged_vs_new": 0.4,
        "symmetric_vs_organic": 0.0,
    },
    "industrial_loft": {
        "warmth": 0.0,
        "complexity": 0.2,
        "natural_vs_polished": 0.3,
        "contrast": 0.4,
        "aged_vs_new": 0.5,
        "symmetric_vs_organic": -0.1,
    },
    "new_chinese": {
        "warmth": 0.3,
        "complexity": 0.2,
        "natural_vs_polished": 0.3,
        "contrast": 0.2,
        "aged_vs_new": 0.4,
        "symmetric_vs_organic": 0.4,
    },
}


_BANK_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "docs" / "handbook" / "discovery_bank.yaml"
)


_loaded_bank: Optional[List[Dict[str, Any]]] = None


def _load_bank() -> List[Dict[str, Any]]:
    """Load and cache the question bank YAML."""
    global _loaded_bank
    if _loaded_bank is not None:
        return _loaded_bank
    if not _BANK_PATH.exists():
        raise DiscoveryError(f"discovery_bank.yaml not found at {_BANK_PATH}")
    try:
        data = yaml.safe_load(_BANK_PATH.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise DiscoveryError(f"failed to parse discovery_bank.yaml: {e}") from e

    # The YAML root is a list with two preamble entries (version,
    # last_updated) followed by question dicts. Filter to questions.
    questions = [
        d for d in data
        if isinstance(d, dict) and d.get("id", "").startswith("q")
    ]
    if not questions:
        raise DiscoveryError("discovery_bank.yaml contains no questions")
    _loaded_bank = questions
    return questions


# ----- Question listing -----

# Quick-mode: enough to score a basic taste profile in 3 minutes.
_QUICK_IDS = {
    "q01_who_uses",  # Type 1
    "q02_project_type",
    "q06_first_second_feeling",  # Type 2 most-impactful
    "q08_movie",                 # Type 3
    "q09_textures",              # Type 4
    "q10_warm_vs_cool",          # Type 5 anchors
    "q11_sparse_vs_full",
}

# Standard-mode: Quick + a couple more from each type.
_STANDARD_EXTRA = {
    "q03_total_area", "q04_budget", "q12_wood_vs_stone",
    "q14_aged_vs_new", "q16_natural_vs_polished", "q19_dont_want",
}


def list_questions(depth: Depth = Depth.DEEP) -> List[Dict[str, Any]]:
    """Return the question list for a given depth."""
    bank = _load_bank()
    if depth in (Depth.DEEP, Depth.ADAPTIVE):
        return list(bank)
    quick_ids = _QUICK_IDS
    standard_ids = quick_ids | _STANDARD_EXTRA
    if depth == Depth.QUICK:
        return [q for q in bank if q["id"] in quick_ids]
    if depth == Depth.STANDARD:
        return [q for q in bank if q["id"] in standard_ids]
    raise DiscoveryError(f"unknown depth: {depth}")


# ----- Answer validation -----

def validate_answer_payload(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Schema-check answers; return a normalized copy."""
    bank = _load_bank()
    by_id = {q["id"]: q for q in bank}
    out: Dict[str, Any] = {}
    for qid, value in answers.items():
        if qid not in by_id:
            raise DiscoveryError(f"unknown question id: {qid}")
        q = by_id[qid]
        if q.get("free_input_only"):
            if not isinstance(value, str):
                raise DiscoveryError(
                    f"{qid} is free_input_only — expected string"
                )
            out[qid] = value.strip()
            continue
        # Choice-based questions can take a single value, list of values,
        # or a free-text string (when free_input is true).
        valid_choices = _question_valid_choices(q)
        if isinstance(value, str) and value not in valid_choices:
            if q.get("free_input"):
                # Treat as free-text override
                out[qid] = {"free_text": value}
                continue
            raise DiscoveryError(
                f"{qid}: choice '{value}' not in {sorted(valid_choices)}"
            )
        if isinstance(value, list):
            for v in value:
                if v not in valid_choices and not q.get("free_input"):
                    raise DiscoveryError(
                        f"{qid}: choice '{v}' not in {sorted(valid_choices)}"
                    )
            out[qid] = list(value)
            continue
        out[qid] = value
    return out


def _question_valid_choices(q: Dict[str, Any]) -> set:
    if "choices" in q:
        return {c["value"] for c in q["choices"]}
    if "options" in q:
        return {o["value"] for o in q["options"]}
    return set()


# ----- Scoring -----

def _zero_axes() -> Dict[str, float]:
    return {a: 0.0 for a in AXES}


def _question_axes_for_choice(q: Dict[str, Any], choice_value: str) -> Dict[str, float]:
    pool = q.get("choices") or q.get("options") or []
    for c in pool:
        if c["value"] == choice_value:
            return c.get("axes", {})
    return {}


def score_answers(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Compute style axes + style match from answers."""
    bank = _load_bank()
    by_id = {q["id"]: q for q in bank}

    axes_sum = _zero_axes()
    axes_count = {a: 0 for a in AXES}

    feeling_anchors: List[str] = []
    material_pull: List[str] = []
    free_text_chunks: List[str] = []

    for qid, value in answers.items():
        if qid not in by_id:
            continue
        q = by_id[qid]
        # Free text → keep aside
        if isinstance(value, dict) and "free_text" in value:
            free_text_chunks.append(f"{qid}: {value['free_text']}")
            continue
        if q.get("free_input_only"):
            if isinstance(value, str):
                free_text_chunks.append(f"{qid}: {value}")
            continue
        # Type-2 projective answers populate feeling_anchors
        if q.get("type") == 2:
            if isinstance(value, list):
                feeling_anchors.extend(value)
            elif isinstance(value, str):
                feeling_anchors.append(value)
        # Type-4 sensory populates material_pull
        if q.get("type") == 4:
            if isinstance(value, list):
                material_pull.extend(value)
            elif isinstance(value, str):
                material_pull.append(value)
        # Sum axes per choice
        choices = value if isinstance(value, list) else [value]
        for choice in choices:
            if not isinstance(choice, str):
                continue
            chosen_axes = _question_axes_for_choice(q, choice)
            for axis, weight in chosen_axes.items():
                if axis in axes_sum:
                    axes_sum[axis] += weight
                    axes_count[axis] += 1

    # Average per axis (preserve sign), then clamp to [-1, 1]
    style_axes = {}
    for axis in AXES:
        n = max(1, axes_count[axis])
        v = axes_sum[axis] / n
        style_axes[axis] = max(-1.0, min(1.0, v))

    style_match = _project_to_styles(style_axes)
    recommended = (
        max(style_match.items(), key=lambda kv: kv[1])[0]
        if style_match else None
    )

    return {
        "feeling_anchors": _dedup(feeling_anchors),
        "style_axes": style_axes,
        "material_pull": _dedup(material_pull),
        "style_match": style_match,
        "recommended_style": recommended,
        "free_text_notes": "\n".join(free_text_chunks),
    }


def _dedup(items: List[str]) -> List[str]:
    seen: set = set()
    out: List[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _project_to_styles(axes: Dict[str, float]) -> Dict[str, float]:
    """Cosine similarity between user axes and each style vector."""
    user_vec = [axes.get(a, 0.0) for a in AXES]
    user_norm = math.sqrt(sum(v * v for v in user_vec)) or 1.0
    out: Dict[str, float] = {}
    for style_name, vec in STYLE_VECTORS.items():
        sv = [vec.get(a, 0.0) for a in AXES]
        sv_norm = math.sqrt(sum(v * v for v in sv)) or 1.0
        dot = sum(u * v for u, v in zip(user_vec, sv))
        cos = dot / (user_norm * sv_norm)
        # Map [-1, 1] → [0, 1]
        out[style_name] = round(0.5 * (cos + 1.0), 4)
    return out


# ----- Session management -----

def new_session(depth: Depth = Depth.DEEP, batch_size: int = 4) -> Dict[str, Any]:
    """Start a discovery session. Returns session_id + first batch."""
    questions = list_questions(depth)
    session_id = secrets.token_urlsafe(8)
    return {
        "session_id": session_id,
        "depth": depth.value,
        "total_questions": len(questions),
        "batch": questions[:batch_size],
        "next_index": min(batch_size, len(questions)),
    }


def midpoint_inferred_style(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Run scoring on partial answers and surface top-2 styles."""
    profile = score_answers(answers)
    sm = profile.get("style_match", {})
    top = sorted(sm.items(), key=lambda kv: kv[1], reverse=True)[:3]
    needs_more = (
        len(top) < 2
        or (len(top) >= 2 and (top[0][1] - top[1][1]) < 0.05)
    )
    return {
        "top_styles": [{"name": n, "score": s} for n, s in top],
        "needs_more_questions": needs_more,
        "current_axes": profile.get("style_axes", {}),
    }
```

- [ ] **Step 2: Run tests — expect pass**

```bash
.venv/bin/pytest tests/test_discovery.py -v
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add src/blender_mcp/_discovery.py tests/test_discovery.py
git commit -m "feat: discovery engine — bank loader + scoring + sessions"
```

---

## Task 4: `_project.py` — Failing Tests + Implementation

**Files:** Create `src/blender_mcp/_project.py`, `tests/test_project.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for project schema + taste-profile read/write."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from blender_mcp._project import (
    ProjectError,
    new_project_record,
    write_taste_profile,
    read_taste_profile,
    update_taste_profile,
    PROJECT_TYPES,
)


def test_project_types_canonical():
    expected = {
        "residential_apartment", "residential_house",
        "cafe_lounge", "restaurant_full_service",
        "retail_boutique", "office_small",
    }
    assert set(PROJECT_TYPES) == expected


def test_new_project_record_fills_defaults():
    rec = new_project_record(
        project_name="My Apt",
        project_type="residential_apartment",
        spaces=["living", "bedroom", "kitchen"],
    )
    assert rec["project_name"] == "My Apt"
    assert rec["project_type"] == "residential_apartment"
    assert rec["spaces"] == ["living", "bedroom", "kitchen"]
    assert rec["units"] == "metric"
    assert "created_at" in rec


def test_new_project_rejects_unknown_type():
    with pytest.raises(ProjectError):
        new_project_record(
            project_name="X",
            project_type="bogus_type",
            spaces=["living"],
        )


def test_write_and_read_taste_profile(tmp_path):
    path = tmp_path / "taste-profile.json"
    profile = {
        "version": 1,
        "feeling_anchors": ["warm"],
        "style_axes": {"warmth": 0.5},
        "recommended_style": "scandinavian",
    }
    write_taste_profile(path, profile)
    loaded = read_taste_profile(path)
    assert loaded["recommended_style"] == "scandinavian"


def test_update_taste_profile_merges_new_fields(tmp_path):
    path = tmp_path / "taste-profile.json"
    write_taste_profile(path, {"version": 1, "feeling_anchors": ["warm"]})
    update_taste_profile(path, {"locked_style": "scandinavian"})
    loaded = read_taste_profile(path)
    assert loaded["locked_style"] == "scandinavian"
    assert loaded["feeling_anchors"] == ["warm"]


def test_read_taste_profile_missing_raises(tmp_path):
    with pytest.raises(ProjectError):
        read_taste_profile(tmp_path / "nonexistent.json")
```

- [ ] **Step 2: Implement `_project.py`**

```python
"""Pure-Python project schema + taste-profile I/O."""
from __future__ import annotations

import json
import datetime
from pathlib import Path
from typing import Any, Dict, List


class ProjectError(Exception):
    """Raised on invalid project type or taste-profile I/O failures."""


PROJECT_TYPES = (
    "residential_apartment",
    "residential_house",
    "cafe_lounge",
    "restaurant_full_service",
    "retail_boutique",
    "office_small",
)


# Standard top-level Blender collection names per the spec.
STANDARD_COLLECTIONS = (
    "00_REFERENCES", "01_PLAN", "02_SHELL", "03_ZONES",
    "04_FINISHES", "05_FIXTURES", "06_LIGHTING", "07_CAMERAS",
    "08_RENDER_OUT", "09_EXPORT", "90_VARIANTS",
)


def new_project_record(
    project_name: str,
    project_type: str,
    spaces: List[str],
    units: str = "metric",
) -> Dict[str, Any]:
    """Validate inputs and return a project record dict."""
    if project_type not in PROJECT_TYPES:
        raise ProjectError(
            f"unknown project_type '{project_type}'. valid: {sorted(PROJECT_TYPES)}"
        )
    if not project_name or not project_name.strip():
        raise ProjectError("project_name must not be empty")
    if not spaces:
        raise ProjectError("spaces list must not be empty")
    return {
        "project_name": project_name.strip(),
        "project_type": project_type,
        "spaces": list(spaces),
        "units": units,
        "standard_collections": list(STANDARD_COLLECTIONS),
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
    }


def write_taste_profile(path: Path, profile: Dict[str, Any]) -> None:
    """Atomic-ish write of taste-profile.json."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def read_taste_profile(path: Path) -> Dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise ProjectError(f"taste-profile not found at {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ProjectError(f"failed to read taste-profile at {path}: {e}") from e


def update_taste_profile(path: Path, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Merge updates into the existing profile (or create if absent)."""
    path = Path(path)
    base: Dict[str, Any] = {}
    if path.is_file():
        base = read_taste_profile(path)
    base.update(updates)
    write_taste_profile(path, base)
    return base
```

- [ ] **Step 3: Run + commit**

```bash
.venv/bin/pytest tests/test_project.py -v
git add src/blender_mcp/_project.py tests/test_project.py
git commit -m "feat: project schema + taste-profile I/O"
```

---

## Task 5: `_snapshots.py` — Failing Tests + Implementation

**Files:** Create `src/blender_mcp/_snapshots.py`, `tests/test_snapshots.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for snapshot directory layout + version log."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from blender_mcp._snapshots import (
    SnapshotError,
    snapshot_create,
    snapshot_list,
    snapshot_read,
    version_log_append,
    version_log_read,
    LoopLevel,
)


def test_snapshot_create_writes_directory(tmp_path):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    blend = project_root / "scene.blend"
    blend.write_bytes(b"fake-blend-bytes")
    profile = project_root / "taste-profile.json"
    profile.write_text('{"version": 1}')

    snap = snapshot_create(
        project_root=project_root,
        label="phase-3-shell-complete",
        files=[blend, profile],
    )
    assert snap["path"].is_dir()
    assert (snap["path"] / "scene.blend").is_file()
    assert (snap["path"] / "taste-profile.json").is_file()
    assert snap["label"] == "phase-3-shell-complete"


def test_snapshot_list_returns_chronological(tmp_path):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    blend = project_root / "scene.blend"
    blend.write_bytes(b"a")
    snapshot_create(project_root=project_root, label="v1", files=[blend])
    snapshot_create(project_root=project_root, label="v2", files=[blend])
    listed = snapshot_list(project_root)
    assert len(listed) == 2
    # Most recent first
    assert listed[0]["label"] == "v2"


def test_version_log_append_and_read(tmp_path):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    version_log_append(
        project_root,
        level=LoopLevel.L3,
        why="user changed sofa layout from L-shape to two-facing",
        snapshot_label="phase-4-pre-layout-change",
    )
    version_log_append(
        project_root,
        level=LoopLevel.L4,
        why="user pivoted from Scandinavian to Japanese 侘寂",
        snapshot_label="phase-2.5-pre-style-pivot",
    )
    log = version_log_read(project_root)
    assert len(log) == 2
    assert log[0]["level"] == "L3"
    assert log[1]["level"] == "L4"


def test_snapshot_create_rejects_missing_file(tmp_path):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    with pytest.raises(SnapshotError):
        snapshot_create(
            project_root=project_root,
            label="bad",
            files=[project_root / "does-not-exist.blend"],
        )
```

- [ ] **Step 2: Implement**

```python
"""Pure-Python snapshot + version log infrastructure."""
from __future__ import annotations

import datetime
import enum
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List


class SnapshotError(Exception):
    """Raised on snapshot I/O failures."""


class LoopLevel(str, enum.Enum):
    L1 = "L1"  # tweak (within Stage 5)
    L2 = "L2"  # material/light swap
    L3 = "L3"  # layout / Stage 3-4 change
    L4 = "L4"  # style redo / Stage 2.5 pivot


def _snapshots_dir(project_root: Path) -> Path:
    return Path(project_root) / "snapshots"


def _version_log_path(project_root: Path) -> Path:
    return Path(project_root) / "version-log.json"


def snapshot_create(
    project_root: Path,
    label: str,
    files: List[Path],
) -> Dict[str, Any]:
    """Create a snapshot directory containing copies of the listed files."""
    project_root = Path(project_root)
    if not project_root.is_dir():
        raise SnapshotError(f"project_root not a directory: {project_root}")

    safe_label = "".join(c if c.isalnum() or c in "-_." else "-" for c in label)
    if not safe_label:
        raise SnapshotError("label resolved to an empty/invalid string")

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    target = _snapshots_dir(project_root) / f"{timestamp}-{safe_label}"
    target.mkdir(parents=True, exist_ok=True)

    copied: List[str] = []
    for src in files:
        src = Path(src)
        if not src.is_file():
            raise SnapshotError(f"file not found: {src}")
        shutil.copy2(src, target / src.name)
        copied.append(src.name)

    manifest = {
        "label": label,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        "files": copied,
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"path": target, "label": label, "files": copied}


def snapshot_list(project_root: Path) -> List[Dict[str, Any]]:
    """Return all snapshots in reverse chronological order."""
    project_root = Path(project_root)
    snap_dir = _snapshots_dir(project_root)
    if not snap_dir.is_dir():
        return []
    out: List[Dict[str, Any]] = []
    for entry in sorted(snap_dir.iterdir(), reverse=True):
        if not entry.is_dir():
            continue
        manifest = entry / "manifest.json"
        if manifest.is_file():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["path"] = str(entry)
            out.append(data)
    return out


def snapshot_read(project_root: Path, snapshot_dir_name: str) -> Dict[str, Any]:
    project_root = Path(project_root)
    target = _snapshots_dir(project_root) / snapshot_dir_name
    manifest = target / "manifest.json"
    if not manifest.is_file():
        raise SnapshotError(f"snapshot manifest missing: {manifest}")
    return json.loads(manifest.read_text(encoding="utf-8"))


def version_log_append(
    project_root: Path,
    level: LoopLevel,
    why: str,
    snapshot_label: str = "",
) -> None:
    """Append a single entry to version-log.json."""
    log_path = _version_log_path(project_root)
    log: List[Dict[str, Any]] = []
    if log_path.is_file():
        try:
            log = json.loads(log_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise SnapshotError(f"corrupt version-log.json: {e}") from e
    log.append({
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "level": level.value,
        "why": why,
        "snapshot_label": snapshot_label,
    })
    log_path.write_text(
        json.dumps(log, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def version_log_read(project_root: Path) -> List[Dict[str, Any]]:
    log_path = _version_log_path(project_root)
    if not log_path.is_file():
        return []
    return json.loads(log_path.read_text(encoding="utf-8"))
```

- [ ] **Step 3: Run + commit**

```bash
.venv/bin/pytest tests/test_snapshots.py -v
git add src/blender_mcp/_snapshots.py tests/test_snapshots.py
git commit -m "feat: snapshot + version-log infrastructure"
```

---

## Task 6: MCP Tools — Discovery / Project / Snapshot

**Files:** Modify `src/blender_mcp/server.py`. Add `tests/test_discovery_mcp.py`.

- [ ] **Step 1: Add tools (paste after `read_design_handbook`)**

```python
@mcp.tool()
@telemetry_tool("run_discovery_questionnaire")
@tool_envelope
def run_discovery_questionnaire(
    ctx: Context,
    depth: str = "deep",
    batch_size: int = 4,
) -> str:
    """
    Start a Discovery questionnaire session. Returns a session_id and the
    first batch of questions per docs/handbook/discovery.md.

    Parameters:
    - depth: 'quick' | 'standard' | 'deep' | 'adaptive' (default 'deep')
    - batch_size: how many questions to return per call (default 4)

    Returns: {session_id, depth, total_questions, batch, next_index}
    """
    from ._discovery import Depth, new_session, DiscoveryError

    try:
        d = Depth(depth.lower())
    except ValueError as e:
        raise ToolError(
            code=ErrorCode.BAD_INPUT,
            hint="depth must be one of: quick / standard / deep / adaptive",
            detail=str(e),
        ) from e
    try:
        session = new_session(depth=d, batch_size=batch_size)
    except DiscoveryError as e:
        raise ToolError(
            code=ErrorCode.INTERNAL,
            hint="discovery_bank.yaml may be missing or malformed",
            detail=str(e),
        ) from e
    return _tool_response(session)


@mcp.tool()
@telemetry_tool("submit_questionnaire_answers")
@tool_envelope
def submit_questionnaire_answers(
    ctx: Context,
    answers: dict,
    return_inferred: bool = True,
) -> str:
    """
    Validate + score discovery answers. If return_inferred=True, also
    surfaces the mid-questionnaire top-style hypothesis (per discovery.md).

    Parameters:
    - answers: dict[question_id → choice_value | list | string]
    - return_inferred: bool (default True)

    Returns:
      {profile: {style_axes, style_match, recommended_style,
                 feeling_anchors, material_pull, free_text_notes},
       inferred?: {top_styles, needs_more_questions, current_axes}}
    """
    from ._discovery import (
        validate_answer_payload, score_answers, midpoint_inferred_style,
        DiscoveryError,
    )

    try:
        normalized = validate_answer_payload(answers)
    except DiscoveryError as e:
        raise ToolError(
            code=ErrorCode.BAD_INPUT,
            hint="check question id and choice value spelling",
            detail=str(e),
        ) from e
    profile = score_answers(normalized)
    out = {"profile": profile}
    if return_inferred:
        out["inferred"] = midpoint_inferred_style(normalized)
    return _tool_response(out)


@mcp.tool()
@telemetry_tool("read_taste_profile")
@tool_envelope
def read_taste_profile_tool(
    ctx: Context,
    project_root: str,
) -> str:
    """Return the project's current taste-profile.json content."""
    from ._project import read_taste_profile, ProjectError
    from pathlib import Path

    try:
        profile = read_taste_profile(Path(project_root) / "taste-profile.json")
    except ProjectError as e:
        raise ToolError(
            code=ErrorCode.NOT_FOUND,
            hint="run_discovery_questionnaire first to generate a profile",
            detail=str(e),
        ) from e
    return _tool_response({"profile": profile})


@mcp.tool()
@telemetry_tool("update_taste_profile")
@tool_envelope
def update_taste_profile_tool(
    ctx: Context,
    project_root: str,
    updates: dict,
) -> str:
    """Merge updates into the project's taste-profile.json."""
    from ._project import update_taste_profile, ProjectError
    from pathlib import Path

    try:
        merged = update_taste_profile(
            Path(project_root) / "taste-profile.json",
            updates,
        )
    except ProjectError as e:
        raise ToolError(
            code=ErrorCode.INTERNAL,
            hint="check filesystem permissions on project_root",
            detail=str(e),
        ) from e
    return _tool_response({"profile": merged})


@mcp.tool()
@telemetry_tool("create_interior_project")
@tool_envelope
def create_interior_project(
    ctx: Context,
    project_name: str,
    project_type: str,
    spaces: list,
    project_root: str,
    units: str = "metric",
) -> str:
    """
    Create the project scaffold — directory layout, project.json,
    taste-profile.json (empty), and standard Blender collection names.

    Parameters:
    - project_name: display name
    - project_type: per docs/handbook/project-types.md
    - spaces: list[str] of space names (e.g. ['living', 'bedroom'])
    - project_root: absolute path; will be created if missing
    - units: 'metric' (default)

    Note: Blender collection creation itself is delegated to the addon
    via execute_blender_code in this slice. This tool writes the
    project metadata and returns the canonical collection list.
    """
    from ._project import new_project_record, write_taste_profile, ProjectError
    from pathlib import Path
    import json as _json

    try:
        rec = new_project_record(
            project_name=project_name,
            project_type=project_type,
            spaces=spaces,
            units=units,
        )
    except ProjectError as e:
        raise ToolError(
            code=ErrorCode.BAD_INPUT,
            hint=("valid project types: residential_apartment, "
                  "residential_house, cafe_lounge, restaurant_full_service, "
                  "retail_boutique, office_small"),
            detail=str(e),
        ) from e

    root = Path(project_root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "project.json").write_text(
        _json.dumps(rec, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # Create empty taste profile so downstream readers don't need to
    # special-case the absent-file path.
    profile_path = root / "taste-profile.json"
    if not profile_path.exists():
        write_taste_profile(profile_path, {"version": 1, "project": project_name})

    for sub in ("snapshots", "exports/renders", "exports/construction"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    return _tool_response({
        "project": rec,
        "project_root": str(root.resolve()),
        "files_created": ["project.json", "taste-profile.json"],
        "directories_created": ["snapshots/", "exports/renders/", "exports/construction/"],
    })


@mcp.tool()
@telemetry_tool("version_snapshot")
@tool_envelope
def version_snapshot(
    ctx: Context,
    project_root: str,
    label: str,
    extra_files: list = None,
) -> str:
    """
    Snapshot the project state. Always copies project.json,
    taste-profile.json, version-log.json (if they exist), plus any
    additional files in `extra_files`.

    Parameters:
    - project_root: absolute path
    - label: short human label (e.g. 'phase-3-shell-complete')
    - extra_files: list[str] of additional absolute paths to include

    Returns: {path, label, files}
    """
    from ._snapshots import snapshot_create, SnapshotError
    from pathlib import Path

    root = Path(project_root)
    files_to_snapshot = []
    for name in ("project.json", "taste-profile.json", "version-log.json"):
        p = root / name
        if p.is_file():
            files_to_snapshot.append(p)
    for extra in extra_files or []:
        files_to_snapshot.append(Path(extra))

    if not files_to_snapshot:
        raise ToolError(
            code=ErrorCode.STATE_REQUIRED,
            hint="No project files found to snapshot — run create_interior_project first",
            detail=f"checked under {root}",
        )
    try:
        snap = snapshot_create(
            project_root=root, label=label, files=files_to_snapshot,
        )
    except SnapshotError as e:
        raise ToolError(
            code=ErrorCode.INTERNAL,
            hint="check filesystem permissions and that all extra_files exist",
            detail=str(e),
        ) from e
    snap["path"] = str(snap["path"])
    return _tool_response(snap)


@mcp.tool()
@telemetry_tool("version_log_entry")
@tool_envelope
def version_log_entry(
    ctx: Context,
    project_root: str,
    level: str,
    why: str,
    snapshot_label: str = "",
) -> str:
    """
    Append a loop-transition entry to version-log.json. Use when the AI
    decides (or the user requests) an L3 / L4 loop per the spec.

    Parameters:
    - project_root: absolute path
    - level: 'L1' | 'L2' | 'L3' | 'L4'
    - why: one-line reason
    - snapshot_label: optional reference to the snapshot taken just before
    """
    from ._snapshots import version_log_append, LoopLevel, SnapshotError
    from pathlib import Path

    try:
        lvl = LoopLevel(level.upper())
    except ValueError as e:
        raise ToolError(
            code=ErrorCode.BAD_INPUT,
            hint="level must be one of L1 / L2 / L3 / L4",
            detail=str(e),
        ) from e
    try:
        version_log_append(
            project_root=Path(project_root),
            level=lvl,
            why=why,
            snapshot_label=snapshot_label,
        )
    except SnapshotError as e:
        raise ToolError(
            code=ErrorCode.INTERNAL,
            hint="check filesystem permissions",
            detail=str(e),
        ) from e
    return _tool_response({"appended": {"level": level, "why": why}})
```

- [ ] **Step 2: Smoke tests**

```python
"""Smoke tests confirming the new MCP tools register and have correct shape."""
from __future__ import annotations

from blender_mcp import server


def test_discovery_tools_registered():
    for name in (
        "run_discovery_questionnaire",
        "submit_questionnaire_answers",
        "read_taste_profile_tool",
        "update_taste_profile_tool",
        "create_interior_project",
        "version_snapshot",
        "version_log_entry",
    ):
        assert hasattr(server, name), f"missing tool: {name}"
```

- [ ] **Step 3: Run + commit**

```bash
.venv/bin/pytest tests/ -v
git add src/blender_mcp/server.py tests/test_discovery_mcp.py
git commit -m "feat: 7 MCP tools for discovery / project / snapshots"
```

---

## Task 7: Final Push

- [ ] **Step 1: Run full test suite**

```bash
.venv/bin/pytest tests/ -v
```

Expected: ≥ 95 + new tests, all passing.

- [ ] **Step 2: Push**

```bash
git push fork sprint-6-quality-of-life
```

---

## Out of scope for Slice 2 (deferred)

- Real Blender collection creation via the addon (Slice 3 plumbing)
- Mid-questionnaire UI for the user (skill-side responsibility)
- Free-text NLP parsing — Slice 1's skill already handles that conceptually

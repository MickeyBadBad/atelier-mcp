# Synthesis Log

Running ledger of project changes triggered by video analyses. Append a new section per synthesis round.

Format per round:

```markdown
## YYYY-MM-DD — Round N: <topic>

**Analyses synthesized**:
- analyses/<date>-<slug-1>.md
- analyses/<date>-<slug-2>.md
- ...

**Cross-tutorial agreement** (techniques that appeared in 2+ analyses):
- <technique 1> — appeared in N/M analyses
- ...

**Project changes applied**:
- ADD-RULE `docs/handbook/<chapter>.md`: "<rule>" (because: cited by N tutorials)
- TUNE-GATE `src/atelier/_gates.py:<function>`: <old> → <new> (because: ...)
- EDIT-SKILL `.claude/skills/<name>.md`: "<edit>" (because: ...)
- ADD-TOOL `src/atelier/server.py`: <tool> (because: ...)

**Single-tutorial findings (recorded but not yet applied — waiting for second source)**:
- <technique> from analyses/<slug>.md — needs corroboration before encoding

**Tests**: pytest result + handbook acceptance gate result
**Commit**: <git hash>
```

---

## (No rounds yet — first synthesis lands when 3+ analyses on a coherent topic exist)

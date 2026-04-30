---
description: Start a new Atelier interior design project. Runs discovery + scaffolds the project directory + writes initial taste-profile.json. The first command you run when starting a new design.
---

You are starting a new Atelier interior design project for the user.

## Process

1. **Confirm project type** with a single question (residential apartment / detached house / cafe-lounge / restaurant / retail / small office / other).
2. **Confirm project name + root path** (default: `./<project_name>` in current working directory).
3. **Confirm the spaces inside the project** — comma-separated list of room/zone names. For residential: typical "Living, Bedroom, Kitchen, Bathroom"; for cafe: "Entry, Bar, Seating, Restroom".
4. **Invoke the discovery questionnaire** by calling the `interior-discovery-intake` skill. Run the Deep depth (25 questions) per the handbook.
5. **Create the project on disk** — call `create_interior_project_native` if Blender is connected, otherwise `create_interior_project` (writes `project.json` + `taste-profile.json` + 11 standard collection scaffolding).
6. **Surface the recommended_style + top 3 style_match scores** to the user and suggest the next step: `/atelier-style` to lock a moodboard direction.

## Cite the handbook

Before asking any of the 25 discovery questions, call `read_design_handbook(chapter="discovery")` and `read_design_handbook(chapter="project-types")` to ground the question rationale.

If the user is impatient, offer the Quick (5-7q) or Standard (12-15q) depth — but flag that the spec recommends Deep for projects worth 20 minutes of attention up-front.

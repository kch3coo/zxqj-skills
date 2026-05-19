---
name: frontend-slide-remotion
description: Use when creating slide-like videos, animated course clips, narrated decks, product explainers, or social videos that should combine frontend-slides presentation design with Remotion video rendering.
---

# Frontend Slide Remotion

Use this skill when the requested output is both slide-structured and video-oriented.

Assume these skills are already available:

- `frontend-slides` for deck structure, visual style, slide density, typography, and browser-preview quality.
- `remotion` or `remotion-best-practices` for React video composition, sequencing, frame-based animation, media, captions, and rendering checks.

## Core Workflow

1. Shape the content as a slide deck first.
   - Use `frontend-slides` standards for narrative flow, slide count, visual direction, density limits, viewport fit, and asset selection.
   - Prefer a clear sequence of scenes over a single long animated canvas.

2. Convert the deck into a Remotion composition.
   - Treat each slide as a scene or `Sequence`.
   - Use frame-based animation with `useCurrentFrame()`, `interpolate()`, `spring()`, and `Easing`.
   - Do not use CSS transitions, CSS keyframe animations, or Tailwind animation utilities for video timing.

3. Preserve slide design constraints in video form.
   - Keep all text within the video frame at the target resolution.
   - Split dense slides into multiple scenes instead of shrinking text.
   - Use stable dimensions for charts, images, captions, and visual panels so motion does not cause layout jumps.

4. Add video-native elements only after the slide structure works.
   - Voiceover, subtitles, sound effects, music, transitions, or b-roll should support the slide sequence.
   - Captions should be synchronized through Remotion timing, not browser-only effects.

5. Verify with Remotion.
   - Run a preview or at least a one-frame still render when practical.
   - Check representative frames near scene starts, transitions, and dense text moments.
   - If the user requests a final video, render using the project’s package manager and Remotion CLI conventions.

## Practical Defaults

- Default format: 16:9 landscape unless the user asks for vertical/social format.
- Vertical social format: 1080x1920, with fewer words per scene and larger caption-safe zones.
- Course/explainer format: use a slide-by-slide script with optional voiceover and captions.
- Product/demo format: use short sections with one key visual or screenshot per scene.

## Common Mistakes

- Do not build the Remotion video first and then try to invent slide structure afterward.
- Do not copy the full `frontend-slides` or `remotion` skill content into this skill; load those skills when details are needed.
- Do not rely on browser animation behavior that Remotion cannot render deterministically.

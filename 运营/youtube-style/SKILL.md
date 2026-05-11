---
name: youtube-style
description: Use when writing or rewriting Chinese YouTube scripts, spoken teaching scripts, beginner-friendly technical video narration, or course-style video copy that should sound natural, explain why first, stay practical, and avoid AI-sounding prose.
---

# YouTube Style

Use this skill when the user wants a Chinese technical video script that reads like a real person speaking to beginners, not like notes, docs, or generic AI copy.

## When to Use

Use this skill for:

- Chinese YouTube scripts
- spoken video narration
- technical lesson scripts
- beginner-friendly course copy
- rewrites of stiff or overly written drafts
- script polishing when the user wants clearer spoken rhythm

Do not use this skill for:

- API docs
- expert-only deep dives
- formal product copy
- entertainment-first comedy writing
- sales-only ad copy

## Defaults

Unless the user asks otherwise, output should be:

- Chinese
- natural spoken paragraphs
- beginner-friendly
- technical or teaching oriented
- structured around `why -> what -> example -> steps -> pitfalls -> takeaway`
- ready for further editing rather than locked to teleprompter formatting

## Source Priority

Apply rules in this order:

1. Course production clarity and beginner comprehension come first.
2. Video-style expression patterns come second.

This skill is not for imitating a specific creator. It is for reproducing a reliable style of explanation.

## Task Modes

First decide which mode applies:

1. `New script mode`: the user wants a script from scratch.
2. `Rewrite mode`: the user already has a draft and wants it rewritten in this style.

Before writing substantial content, read [references/task-modes.md](references/task-modes.md).

Before finalizing substantial content, read [references/style-rules.md](references/style-rules.md).

## Minimum Inputs

If the user does not give enough information, ask only for the missing minimum needed to do the job well.

For `New script mode`, try to lock these inputs:

- topic
- target audience
- video goal
- desired length or target duration
- source material or must-cover points

For `Rewrite mode`, try to lock these inputs:

- original draft
- what must stay unchanged
- target audience
- whether to keep or tighten the current structure

Do not ask a long questionnaire if a reasonable default is safe.

## Writing Flow

### New Script Mode

Use this order by default:

1. Open with why this matters, what problem it solves, or why the viewer should care now.
2. Give a plain-language definition only after the value is clear.
3. Move quickly into one concrete example, scenario, or real operation.
4. Expand into steps, logic, or explanation in a beginner-safe order.
5. Call out easy-to-miss details, confusion points, and likely mistakes.
6. Close with a short takeaway, next step, or transition.

### Rewrite Mode

When rewriting:

1. Preserve the original meaning unless the user asks to change the substance.
2. Rebuild the opening if it starts with definition, background dumping, or vague framing.
3. Replace written-language phrasing with spoken Chinese.
4. Add plain-language explanations where a beginner would stall.
5. Compress filler, repetition, and fake emphasis.
6. Keep the result in natural paragraphs by default.

## Core Style Rules

- Explain `why learn this` or `why watch this` before heavy definition.
- If a term may block a beginner, explain it immediately in plain language.
- Keep concepts close to examples.
- Keep syntax, code, and explanation close together when code is involved.
- Prefer practical scenes, browser actions, product examples, or real operating context over abstract talk.
- Sound relaxed and human, but do not force jokes or persona.
- Prefer `我们` / `咱们` / `你可以这样理解`.
- Keep normal paragraph structure. Do not force one-sentence-per-line output unless asked.
- Keep the draft concise. Cut filler that does not improve understanding.

## Hard Bans

- Do not open with dry definitions when the user needs motivation first.
- Do not introduce extra concepts that are not required for the current teaching goal.
- Do not write in documentation tone, customer-service tone, or academic tone.
- Do not stack empty rhetorical contrasts such as `不是……而是……` as a default pattern.
- Do not overuse parallel slogans, hype, or dramatic claims.
- Do not produce vague paragraphs that sound smooth but teach nothing.
- Do not show only the final result when the explanation should feel operational.

## Final Self-Check

Before returning the script, verify:

1. The opening tells the viewer why they should care.
2. Definitions do not arrive before motivation.
3. Any blocking term is translated into plain speech.
4. Examples appear close to the concept they explain.
5. The draft reads like spoken Chinese, not a document.
6. The paragraphs are natural and not chopped into artificial line breaks.
7. Filler, repetition, and AI-sounding phrasing have been cut.
8. The output stays faithful to the user's source material in rewrite tasks.

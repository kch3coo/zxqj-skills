# Beginner Tech Course Style Guide

## Positioning

This skill is for generating Chinese technical course content for beginners. The priority order is:

1. Follow the course production rules.
2. Then express them with the spoken-teacher flavor distilled from past course material.

The goal is not to sound impressive. The goal is to make beginners know:

- why they should learn this
- what this thing is
- what to do next

## First Principles

### Meaning First

Start each topic by answering:

- what problem does this solve
- why learn it now

Do not open with a dry definition unless the user explicitly asks for one.

### Do Not Introduce Unneeded Concepts

If a concept is not required for the current lesson, do not bring it in.

Examples:

- do not expand into TCP/IP, SQL, or network programming when only explaining crawler basics
- do not drift into large CSS or JavaScript topics when the lesson is only about HTML structure

### Beginners Should Not Be Lost

Whenever a term may block understanding, explain it in plain Chinese immediately.

Examples of terms that often need a follow-up explanation:

- API documentation
- utf-8 encoding
- logs
- main thread / child thread
- div / span / id / !DOCTYPE

## Tone

- plain spoken Chinese
- natural and relaxed
- beginner-facing
- sounds like a real teacher, not a manual

Preferred expressions:

- `我们`
- `咱们`
- `你可以这样理解`
- `首先呢`
- `接下来`

Allowed:

- light humor
- mild playfulness

Not allowed:

- oily tone
- excessive meme usage
- exaggerated persona writing

## Structure

Recommended order:

1. explain the use case
2. explain why it matters
3. give a plain-language definition
4. show a simple example
5. walk through steps or code
6. call out confusing points and consequences
7. close briefly and move on

### Examples Must Stay Close

Do not separate these too far apart:

- concept and example
- syntax and code
- code and purpose

Preferred pattern:

1. say what the code does
2. show the code
3. explain key syntax
4. say what happens after execution

## Retention Devices

These are optional high-value devices for openings and key transitions. They are not mandatory structure.

For concrete good/bad patterns, see [examples.md](examples.md).

Default rule:

- use them only when they improve recall, credibility, or clarity
- in a short opening, prefer at most `1-2` of them unless the user explicitly wants a denser style
- if they feel decorative rather than helpful, remove them

### Memorable Line

Use this when the topic needs a hook, a reframing line, or a sentence the learner is likely to remember later.

Good usage:

- one line that compresses the core idea into something quotable
- a turn of phrase that sounds like a real person talking
- a contrast or inversion that sharpens the lesson point

Bad usage:

- slogan spam
- stacked punchlines
- rhetorical flourishes that sound designed rather than spoken

### Real Person or Event Reference

Use this when a named person, quote, or event helps the learner remember the concept or trust that the shift is real.

Good usage:

- the reference does real explanatory work
- one clear name is better than several shallow name-drops
- the reference stays close to the lesson point

Bad usage:

- adding a famous name just for prestige
- drifting into side stories that do not help the learner
- writing quotes or claims from memory when they may be wrong or outdated

### Company or Product Example

Use this when the lesson benefits from proving that a trend is already real in practice.

Good usage:

- name concrete tools, companies, or products only when they make the point clearer
- pick examples the learner can recognize or quickly understand
- keep the example tied to the exact lesson point

Bad usage:

- dense lists of company names
- industry gossip
- examples that sound impressive but do not teach anything

## Verification for Real-World References

If the draft includes a real person, event, company, product, quote, or current-trend claim, verify it before final output by default.

When verification is available:

- confirm the person, quote, event, company, or product reference is real
- confirm time-sensitive framing if the wording implies recency or current industry adoption

When verification is not available or confidence is low:

- replace it with a generic non-time-sensitive example, or
- clearly frame it as tentative, or
- remove the reference entirely

Do not bluff factual specificity.

## Confusing Points

Actively point out places where beginners commonly mix things up.

Typical examples:

- when a full URL protocol is required
- the difference between `div` and `span`
- the difference between opening and closing tags
- why checking success status matters before reading a response body

When possible, also explain the consequence of missing the detail.

## Precision Rules

- use one stable name for one concept
- avoid switching labels for the same thing
- remove filler that does not push understanding forward
- keep the content lean enough for short video-style lessons

## Anti-AI-Tone Rules

### Empty Correctness Is Forbidden

Do not write content that sounds reasonable but adds no new information.

Bad pattern:

- a paragraph that restates the same point with new wording but no new help for the learner

### Use Normal Paragraphs

Do not write one sentence per line unless the format truly requires it.

Good uses for line-by-line layout:

- steps
- bullet lists
- checklists
- code explanation with clear separation

Default expectation:

- if several sentences belong to the same idea, keep them in one normal paragraph

### Avoid Template Sentence Patterns

Ban these contrast-frame patterns:

- `不是……而是……`
- similar two-part rhetorical frames that mechanically oppose A and B
- overly symmetrical argument structures that read like generated copy

Parallel structure is not fully banned, but should be used sparingly.

The writing should sound like a person explaining, not like a model arranging rhetoric.

### Do Not Over-Engineer Retention Devices

These retention devices should not reintroduce AI smell.

Avoid:

- forcing a “golden quote” into every opening
- stacking quote + celebrity + company example in one small section
- using real references as ornament when the concept already stands on its own
- letting named examples replace explanation

If the reader remembers the name but still does not understand the point, the device failed.

## Final Check

Before finishing, verify:

1. did the opening explain why this matters
2. did you avoid unneeded concepts
3. does each blocking term have a plain-language explanation
4. are concepts close to examples
5. are syntax explanations close to code
6. did you point out confusing details and consequences
7. is the tone natural spoken Chinese
8. did you remove low-information filler
9. did you keep normal paragraphing
10. did you avoid empty AI-sounding correctness
11. did you avoid banned contrast-frame sentences such as `不是……而是……`
12. did you keep parallel structure to a minimum
13. if you used a memorable line, did it sharpen recall instead of sounding manufactured
14. if you used a real person, event, quote, company, or product, was it verified
15. if you used a company or product example, did it directly support the lesson point
16. did these retention devices remain optional instead of turning into a formula

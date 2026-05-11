# Task Modes

Use this file to decide how `youtube-style` should operate on the user's request.

## Mode 1: New Script

Use this when the user wants a script from scratch.

### Minimum useful inputs

- topic
- audience
- goal
- target duration or rough length
- must-cover points or source material

### Default behavior

- choose a beginner-friendly structure
- open with why the topic matters
- define only after context is established
- keep the script in natural spoken paragraphs
- prefer one running example when possible

### If inputs are incomplete

Ask for only the missing information that would materially change the output. If the missing detail is low risk, assume a sensible beginner-friendly default.

## Mode 2: Rewrite

Use this when the user already has a draft and wants it polished into this style.

### Minimum useful inputs

- original draft
- target audience if not obvious
- anything that must not change

### Default behavior

- keep the meaning
- fix the opening if it starts too abstractly
- make the wording more spoken and more beginner-safe
- remove repetition and dead weight
- keep normal paragraph formatting unless the user asks for line-by-line output

### Rewrite priorities

1. preserve substance
2. improve structure
3. improve readability aloud
4. reduce AI tone

## Decision Rule

If the request mixes both modes, do this:

1. first stabilize the structure from the user's material
2. then fill missing sections in the same style

## Output Defaults

Unless explicitly requested otherwise, do not output:

- teleprompter one-line formatting
- production notes
- shot lists
- title thumbnail options

Return the spoken script itself first.

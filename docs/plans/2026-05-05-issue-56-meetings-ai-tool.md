# Plan: AI tool for meetings — voice → summary (#56)

- Issue: https://github.com/vamseeachanta/assetutilities/issues/56
- Tier: T3 (out-of-scope; recommend close or re-route)
- Repo: assetutilities (proposed: close)
- Status: plan-review

## Context

Issue #56 is a one-line stub: "Develop an AI tool for meetings,
recognizing voice and giving summary out of it."

assetutilities is a Python utility library, not a place for full
SaaS-style features. Voice transcription + summarization tools exist
both as commercial products (Otter, Fireflies, Granola) and as recent
Anthropic / OpenAI features. Reinventing this in assetutilities is not
a good investment.

**Re-routing recommendation:** close #56. If the maintainer still wants
to track exploration of meeting tools, file as a workspace-hub research
note rather than an assetutilities issue.

In-scope here: triage + close. No code.

## Plan

1. **Comment on #56.** Recommend evaluating commercial options
   (Granola, Otter, Anthropic-native call summarization features) as a
   research task rather than a build task. Note assetutilities is not
   the right home for an audio pipeline.
2. **Close #56** with `wontfix` or transfer to workspace-hub if the
   maintainer wants to keep evaluating.

## Acceptance criteria

- [ ] Comment on #56 with recommendation.
- [ ] #56 closed.

## Open questions

- Is there a private repo where the team already evaluates productivity
  SaaS? If yes, transfer the issue there instead of close.

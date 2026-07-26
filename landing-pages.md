# Landing Page Generation

Turns a single product photo and a short set of preferences into a complete, on-brand landing
page - no template picking, no manual copywriting pass.

## Pipeline

```
Product photo + preferences
        │
        ▼
Vision analysis (image → structured product attributes: category, colors, apparent
                  quality tier, notable features)
        │
        ▼
Copy generation (headline, body, calls to action - localized to the target script:
                  Arabic / French / Darija)
        │
        ▼
Compliance review (checks generated claims against basic advertising-standards rules
                    before anything reaches the page)
        │
        ▼
Server-side template render → sandboxed iframe preview
```

Three separate LLM passes rather than one large prompt: vision analysis, copywriting, and
compliance review each have a narrow job and a narrow failure mode. A bad compliance check
doesn't silently corrupt the copy, and a bad copy pass doesn't need to re-run vision analysis -
each stage can be retried or swapped independently.

## Why a sandboxed iframe

Generated HTML is rendered server-side from a fixed template, not executed as arbitrary
user-facing code. The preview iframe is sandboxed so nothing in a generated page can reach
outside its own frame - model-generated markup is untrusted input by default, the same way any
other LLM output is treated in this system.

## State

Three fields carry a landing page request through the graph: the uploaded product image
reference, the user's stated preferences, and the pipeline's output once all three passes
complete. See [`samples/state.py`](../samples/state.py) for the exact shape.

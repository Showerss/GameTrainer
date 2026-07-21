Build me a single interactive artifact (a React component is ideal) that gently
teaches a total beginner how computer vision works, one brick at a time.

WHO IT'S FOR
I'm heading into a PhD in this area but I'm a complete beginner to computer
vision and I get overwhelmed fast. I learn slowly and well — brick by brick.
Rules: introduce ONE idea per screen, minimal text per screen, define every new
term the first time it appears in one plain sentence, no math, no jargon dumps.
Keep the truth accurate but the pacing gentle.

FORMAT
- Stepped and interactive: Next / Back buttons, a progress indicator, one concept
  per screen.
- Use simple box-and-arrow diagrams (SVG) with clear labels and gentle animation
  on transitions. No walls of text.
- Keep a persistent legend for a "shared language": eyes = the vision part,
  brain = the reasoning part, hands = actions.
- Let me hover any bolded term to see its definition (build a small glossary).
- At a few milestones, add a tiny "check your understanding" click question with
  friendly feedback.

THE STORYLINE (screens, in this order)
1. What an image is to a computer: just a grid of numbers (pixels).
2. The EYES = a Vision Transformer (ViT): chop the image into small patches,
   turn each patch into a vector, and combine them into one "meaning vector"
   (an embedding). Define: encoder, patch, embedding.
3. Embedding space: a map where similar things sit close together. Let me drag a
   photo and watch matching words light up nearby.
4. The SEAM: the eyes hand their vector to a BRAIN. Show the fork clearly —
   the same eyes can feed a LANGUAGE brain (which talks) OR an ACTION brain
   (which does). This fork matters to me, make it a highlight.
5. The big modern idea: connect pixels to WORDS. Contrast old computer vision
   (a fixed list of labels) with modern CV (language = an open, flexible label
   list). Define: open-vocabulary.
6. The model FAMILY as siblings on ONE spectrum, all built from "connect pixels
   to words," differing only in how far toward talking they go:
      MATCH (CLIP, ALIGN) -> LOCATE (GLIP) -> DESCRIBE (BLIP) -> CONVERSE (LLaVA)
   Let me click each sibling and see its different OUTPUT on the same house photo
   (a match, a box on the image, a caption, a conversation).
7. Myth-busting screen with interactive "myth vs reality" toggles:
   - MYTH: it's a pipeline, CLIP -> GLIP -> BLIP feeding each other.
     REALITY: they're separate, complete models by different labs. Pick the one
     whose output you want; you don't chain them.
   - MYTH: Claude runs CLIP+GLIP+BLIP as a swarm and merges their answers.
     REALITY: image chat is ONE encoder -> ONE brain -> ONE answer. A soloist who
     learned every instrument, not an orchestra being conducted.
   - MYTH: CLIP/GLIP/BLIP are named regions inside Claude working together.
     REALITY: a multimodal model usually has ONE set of eyes; those are separate
     outside models.
   - Foundation model: a base trained first on huge data, then REUSED whole
     (e.g., a CLIP encoder reused as the eyes inside LLaVA).
   - MYTH: a better CLIP gets hot-swapped into today's model.
     REALITY: eyes and brain are trained together and share a private language;
     improvements arrive in the NEXT generation, trained fresh — not an organ
     transplant.
8. How real image-chat works end to end: my house photo -> one encoder -> image
   vectors placed next to my words -> one brain -> one answer.
9. Recap + a glossary of every bolded term + a short self-check.

Start simple and get slightly deeper each screen. Prioritize clarity and gentle
pacing over covering everything at once.

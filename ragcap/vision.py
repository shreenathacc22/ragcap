"""Step 24: drawings into the index. A vision model turns a P&ID image into plain sentences (tags, valves and what
they sit between, instruments and what they measure), and those sentences are embedded like any document chunk.
The image path is kept in the chunk's meta so an answer can point back to the drawing."""
import base64
import mimetypes
import os
import time

from .llm import client

VISION_MODEL = os.getenv("VISION_MODEL", "qwen2.5vl:3b")
VISION_MAX_TOKENS = int(os.getenv("VISION_MAX_TOKENS", "700"))
LEGEND = ("Tag conventions (ISA-5.1): first letter L=level, P=pressure, T=temperature, F=flow; the letters after it "
          "T=transmitter, I=indicator, C=controller. FCV=flow control valve, HV=hand isolation valve. "
          "Equipment prefixes: P-=pump, T-=tank, E-=heat exchanger.")
PROMPT = ("Describe this P&ID for a search index, one fact per sentence, using the exact tags as printed:\n"
          "1) The drawing number and title from the title block.\n"
          "2) Every equipment tag and its type.\n"
          "3) Every valve tag and which two items it sits between on the line.\n"
          "4) Every instrument tag, what it measures or controls, and which equipment or line it is on.")


def describe_image(path: str, model: str = VISION_MODEL, max_tokens: int = VISION_MAX_TOKENS) -> tuple[str, float]:
    b64 = base64.b64encode(open(path, "rb").read()).decode()
    mime = mimetypes.guess_type(path)[0] or "image/png"
    t0 = time.perf_counter()
    r = client().chat.completions.create(model=model, temperature=0, max_tokens=max_tokens, messages=[
        {"role": "system", "content": "You read engineering P&ID drawings carefully. " + LEGEND},
        {"role": "user", "content": [{"type": "text", "text": PROMPT},
                                     {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]}])
    return (r.choices[0].message.content or ""), time.perf_counter() - t0

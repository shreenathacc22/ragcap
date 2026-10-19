"""Synthetic P&ID drawings with ground truth, for the multimodal branch (step 24).

Real P&IDs are confidential, so three small drawings are generated from one template: a tank feeding a pump,
through a heat exchanger, into a second tank, with isolation valves, a control valve and five instruments
tagged by ISA-5.1 convention. Every tag and relation is recorded in ground_truth.json, and 12 golden questions
are written from it. Deterministic: re-running reproduces the same files.

    .venv/bin/python pid/make_pid.py      # writes pid/drawings/PID-00k.png, pid/ground_truth.json, pid/golden_pid.jsonl
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
UNITS = {1: "Cooling Water Circuit", 2: "Feed Transfer", 3: "Reflux Return"}
W, H = 1400, 900


def font(size):
    for f in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


F, FS, FT = font(26), font(20), font(30)


def label(d, xy, text, f=F, anchor="mm"):
    d.text(xy, text, fill="black", font=f, anchor=anchor)


def tank(d, x, y, tag):
    d.rectangle([x - 70, y - 110, x + 70, y + 110], outline="black", width=4)
    label(d, (x, y - 140), tag)


def pump(d, x, y, tag):
    d.ellipse([x - 45, y - 45, x + 45, y + 45], outline="black", width=4)
    d.polygon([(x - 20, y + 30), (x + 20, y + 30), (x, y - 10)], outline="black", width=3)
    label(d, (x, y + 80), tag)


def exchanger(d, x, y, tag):
    d.rectangle([x - 90, y - 50, x + 90, y + 50], outline="black", width=4)
    d.line([x - 90, y - 50, x + 90, y + 50], fill="black", width=3)
    label(d, (x, y - 85), tag)


def valve(d, x, y, tag, control=False):
    d.polygon([(x - 22, y - 18), (x + 22, y + 18), (x + 22, y - 18), (x - 22, y + 18)], outline="black", width=4)
    if control:
        d.line([x, y, x, y - 45], fill="black", width=3)
        d.arc([x - 22, y - 70, x + 22, y - 30], 0, 180, fill="black", width=3)
    label(d, (x, y + 45), tag)


def instrument(d, x, y, tag, attach=None):
    # run 1 used radius 32: a 7-character tag overlapped the circle edge and the vision model read "FIC-10".
    r = 46
    d.ellipse([x - r, y - r, x + r, y + r], outline="black", width=3)
    label(d, (x, y), tag, FS)
    if attach:
        d.line([x, y + r, attach[0], attach[1]], fill="black", width=2)


def pipe(d, pts):
    d.line(pts, fill="black", width=5)
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    if x2 > x1:
        d.polygon([(x2, y2), (x2 - 18, y2 - 9), (x2 - 18, y2 + 9)], fill="black")


def draw(k: int) -> dict:
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, W - 10, H - 10], outline="black", width=3)
    t1, p1, e1, t2 = f"T-{k}01", f"P-{k}01", f"E-{k}01", f"T-{k}02"
    hv1, hv2, fcv = f"HV-{k}01", f"HV-{k}02", f"FCV-{k}01"
    lt, pi, tt, fic, lic = f"LT-{k}01", f"PI-{k}01", f"TT-{k}01", f"FIC-{k}01", f"LIC-{k}02"
    y = 470
    # main line left to right
    pipe(d, [(190, y), (370, y)]); valve(d, 300, y, hv1)
    pump(d, 440, y, p1)
    pipe(d, [(485, y), (700, y)]); valve(d, 600, y, hv2)
    exchanger(d, 790, y, e1)
    pipe(d, [(880, y), (1130, y)]); valve(d, 1010, y, fcv, control=True)
    tank(d, 120, y, t1); tank(d, 1200, y, t2)
    # instruments
    instrument(d, 120, 250, lt, (120, 360)); instrument(d, 540, 300, pi, (540, 465)); instrument(d, 930, 300, tt, (930, 465))
    instrument(d, 1010, 250, fic, (1010, 400)); instrument(d, 1200, 250, lic, (1200, 360))
    d.line([(1010, 296), (1010, 400)], fill="black", width=2)
    # legend and title block
    d.rectangle([40, 640, 700, 860], outline="black", width=2)
    legend = ["LEGEND (ISA-5.1)", "LT level transmitter   PI pressure indicator   TT temperature transmitter",
              "FIC flow indicating controller   LIC level indicating controller", "HV hand (isolation) valve   FCV flow control valve",
              "T- tank   P- pump   E- heat exchanger"]
    for i, line in enumerate(legend):
        label(d, (60, 660 + i * 38), line, FS if i else F, anchor="lm")
    d.rectangle([900, 760, W - 40, 860], outline="black", width=3)
    label(d, (1130, 790), f"P&ID-00{k}", FT); label(d, (1130, 835), f"{UNITS[k]}    Rev B    Sheet 1 of 1", FS)
    img.save(HERE / "drawings" / f"PID-00{k}.png")
    return {"drawing": f"P&ID-00{k}", "file": f"PID-00{k}.png", "unit": UNITS[k],
            "equipment": [{"tag": t1, "type": "tank"}, {"tag": p1, "type": "pump"}, {"tag": e1, "type": "heat exchanger"}, {"tag": t2, "type": "tank"}],
            "lines": [[t1, p1], [p1, e1], [e1, t2]],
            "valves": [{"tag": hv1, "type": "hand isolation valve", "between": [t1, p1], "role": f"suction isolation of {p1}"},
                       {"tag": hv2, "type": "hand isolation valve", "between": [p1, e1], "role": f"discharge isolation of {p1}"},
                       {"tag": fcv, "type": "flow control valve", "between": [e1, t2], "controlled_by": fic}],
            "instruments": [{"tag": lt, "measures": "level", "on": t1}, {"tag": pi, "measures": "pressure", "on": f"discharge of {p1}"},
                            {"tag": tt, "measures": "temperature", "on": f"outlet of {e1}"},
                            {"tag": fic, "measures": "flow", "controls": fcv, "on": f"line into {t2}"}, {"tag": lic, "measures": "level", "on": t2}]}


def golden(gt):
    cases = []
    for g in gt:
        k = g["drawing"][-1]
        p1, t1, t2, e1 = f"P-{k}01", f"T-{k}01", f"T-{k}02", f"E-{k}01"
        cases += [
            {"id": f"pid-{k}a", "drawing": g["drawing"], "question": f"Which valve isolates the suction of pump {p1}?", "facts": [f"HV-{k}01"], "must_not_contain": [f"HV-{k}02"]},
            {"id": f"pid-{k}b", "drawing": g["drawing"], "question": f"Which instrument controls the flow into tank {t2}, and through which valve?", "facts": [f"FIC-{k}01", f"FCV-{k}01"], "must_not_contain": []},
            {"id": f"pid-{k}c", "drawing": g["drawing"], "question": f"What does LT-{k}01 measure, and on which equipment?", "facts": ["level", t1], "must_not_contain": [t2]},
            {"id": f"pid-{k}d", "drawing": g["drawing"], "question": f"Which drawing shows heat exchanger {e1}, and what unit is it?", "facts": [f"{g['drawing']}|{g['file'][:-4]}", g["unit"].split()[0]], "must_not_contain": []},   # P&ID-00k or PID-00k: same id
        ]
    for c in cases:
        c.update(route="documents", type="drawing")
    return cases


if __name__ == "__main__":
    gt = [draw(k) for k in (1, 2, 3)]
    (HERE / "ground_truth.json").write_text(json.dumps(gt, indent=1))
    cases = golden(gt)
    (HERE / "golden_pid.jsonl").write_text("\n".join(json.dumps(c) for c in cases) + "\n")
    print(f"3 drawings, ground truth for {sum(len(g['equipment']) + len(g['valves']) + len(g['instruments']) for g in gt)} tags, {len(cases)} golden questions")

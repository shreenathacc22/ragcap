// ragcap deck: structured pptxgenjs build (theme, layouts, placeholders, sections), then applyTheme.
const pptxgen = require("pptxgenjs");
const path = require("path");
const { applyTheme } = require(process.env.SKILL_DIR + "/scripts/apply_theme.js");

const THEME = { name: "ragcap", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1F2933", lt1: "FFFFFF", dk2: "0F4C5C", lt2: "EEF3F6", accent1: "0F766E", accent2: "B54141",
            accent3: "1E7F4F", accent4: "D98E04", accent5: "5F6B76", accent6: "2457A8", hlink: "0F766E", folHlink: "5F6B76" } };
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";           // 10 x 5.625 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "ragcap: a multi-agent RAG system, built and measured"; pres.author = "Shreenath Shetty";
const C = pres.SchemeColor;
const IMG = (f) => path.join(__dirname, f);
const PAGES = "https://shreenathacc22.github.io/ragcap/", REPO = "https://github.com/shreenathacc22/ragcap";

// ---- layouts
pres.defineSlideMaster({ title: "DARK", background: { color: THEME.colors.dk2 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.0, w: 8.8, h: 1.4, fontSize: 36, bold: true, color: C.background1, margin: 0 }, text: "" } },
            { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 2.7, w: 8.8, h: 1.9, fontSize: 15, color: C.background1, margin: 0 }, text: "" } }] });
pres.defineSlideMaster({ title: "CONTENT", background: { color: THEME.colors.lt1 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.35, w: 9.0, h: 0.7, fontSize: 28, bold: true, color: C.text2, margin: 0 }, text: "" } },
            { text: { text: "ragcap  ·  github.com/shreenathacc22/ragcap", options: { x: 0.5, y: 5.2, w: 6, h: 0.3, fontSize: 9, color: C.accent5, margin: 0 } } }],
  slideNumber: { x: 9.1, y: 5.2, w: 0.5, h: 0.3, fontSize: 9, color: THEME.colors.accent5 } });

// ---- helpers (fresh option objects every call)
const box = (s, x, y, w, h, fill, text, opt = {}) => {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.08, objectName: "card " + (opt.name || text.slice(0, 12)) });
  s.addText(text, Object.assign({ x: x + 0.1, y, w: w - 0.2, h, fontSize: 12, color: C.text1, align: "center", valign: "middle", isTextBox: true, margin: 0 }, opt));
};
const card = (s, x, y, w, h, head, body, headColor) => {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, fill: { color: THEME.colors.lt2 }, line: { color: THEME.colors.lt2 }, rectRadius: 0.1, objectName: "card " + head });
  s.addText(head, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: 0.4, fontSize: 15, bold: true, color: headColor || C.accent1, isTextBox: true, margin: 0 });
  s.addText(body, { x: x + 0.2, y: y + 0.55, w: w - 0.4, h: h - 0.7, fontSize: 12, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
};
const stat = (s, x, y, w, big, small, color) => {
  s.addText(big, { x, y, w, h: 0.75, fontSize: 36, bold: true, color: color || C.accent1, isTextBox: true, margin: 0, align: "left" });
  s.addText(small, { x, y: y + 0.75, w, h: 0.5, fontSize: 11, color: C.accent5, isTextBox: true, margin: 0 });
};
const arrow = (s, x1, y1, x2, y2) => s.addShape(pres.ShapeType.line, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.01, h: Math.abs(y2 - y1) || 0.01,
  flipH: x2 < x1, flipV: y2 < y1, line: { color: THEME.colors.accent5, width: 1.5, endArrowType: "triangle" }, objectName: "arrow" });
const bullets = (items) => items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6 } }));

// ================= 1 title
pres.addSection({ title: "Overview" });
let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Overview" });
s.addText("ragcap: a multi-agent RAG system, built and measured", { placeholder: "title" });
s.addText([{ text: "A colleague's capstone design (LangGraph router, document RAG with grade and rewrite, SQL agent, general agent, Postgres + pgvector) reproduced on local models, then evaluated the way it should be: frozen test sets, repeated runs, and a version-aware filter with an OFF/ON proof.", options: { breakLine: true } },
           { text: "2019 Intel MacBook Pro · no API key · no GPU · October 2026", options: { fontSize: 13, color: C.background2 } }], { placeholder: "body" });
s.addText([{ text: REPO, options: { hyperlink: { url: REPO }, color: C.background1 } }, { text: "    ·    " }, { text: PAGES, options: { hyperlink: { url: PAGES }, color: C.background1 } }],
  { x: 0.6, y: 4.7, w: 8.8, h: 0.4, fontSize: 12, color: C.background1, isTextBox: true, margin: 0 });
s.addNotes("Open with the one-line summary, then the two links. Everything on these slides is reproducible from the repository.");

// ================= 2 the ask vs what was built
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Overview" });
s.addText("The design to reproduce, and what was added", { placeholder: "title" });
card(s, 0.5, 1.2, 4.4, 3.8, "The design (from the capstone PDF)", "", C.accent6);
s.addText(bullets(["Router → documents / database / general", "Retrieve top-6 → Grade → one Rewrite → Generate with citations", "SQL agent: one SELECT, read-only, time-limited, one retry", "General agent never states facts", "Postgres + pgvector, LangGraph, FastAPI, streaming chat, UI", "Reported: latency and cost per flow (110 answers)"]),
  { x: 0.7, y: 1.75, w: 4.0, h: 3.1, fontSize: 12, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
card(s, 5.1, 1.2, 4.4, 3.8, "Added here", "", C.accent1);
s.addText(bullets(["A quality column: frozen golden set (27), unseen set (25), router / retrieval / answer accuracy", "Repeated runs: means and ranges, failing ids listed", "Version-aware retrieval: superseded versions excluded before ranking, proven OFF vs ON", "Honest negatives: 8B grader on CPU, Docling on Intel macOS", "A P&ID branch on synthetic drawings with a 3B vision model", "Three documents: SOP, runbook, recreate guide; a one-command rebuild"]),
  { x: 5.3, y: 1.75, w: 4.0, h: 3.1, fontSize: 12, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
s.addNotes("The left column is what the PDF described; the right is what this project added. The key gap in the original was that nothing measured correctness.");

// ================= 3 flow
pres.addSection({ title: "How it works" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "How it works" });
s.addText("The graph: one router, three paths, one trace", { placeholder: "title" });
const F = THEME.colors;
box(s, 0.5, 2.55, 1.1, 0.6, F.lt2, "question", { fontSize: 12 });
box(s, 1.9, 2.55, 1.2, 0.6, F.dk2, "router", { fontSize: 13, bold: true, color: C.background1 });
box(s, 3.6, 1.35, 1.2, 0.6, F.lt2, "retrieve"); box(s, 5.1, 1.35, 1.2, 0.6, F.lt2, "grade"); box(s, 6.6, 1.35, 1.2, 0.6, F.lt2, "generate");
s.addShape(pres.ShapeType.roundRect, { x: 5.1, y: 2.15, w: 1.2, h: 0.45, fill: { color: F.lt1 }, line: { color: F.accent5, dashType: "dash" }, rectRadius: 0.08, objectName: "rewrite box" });
s.addText("rewrite ×1", { x: 5.1, y: 2.15, w: 1.2, h: 0.45, fontSize: 11, align: "center", valign: "middle", color: C.text1, isTextBox: true, margin: 0 });
box(s, 3.6, 2.9, 1.3, 0.6, F.lt2, "sql_agent"); box(s, 5.2, 2.9, 1.5, 0.6, F.lt2, "generate_sql");
box(s, 3.6, 3.9, 1.2, 0.6, F.lt2, "general");
box(s, 8.3, 2.55, 1.2, 0.6, F.lt2, "answer", { fontSize: 12 });
arrow(s, 1.6, 2.85, 1.9, 2.85); arrow(s, 3.1, 2.7, 3.6, 1.65); arrow(s, 4.8, 1.65, 5.1, 1.65); arrow(s, 6.3, 1.65, 6.6, 1.65);
arrow(s, 5.7, 1.95, 5.7, 2.15); arrow(s, 5.1, 2.37, 4.2, 1.95);
arrow(s, 3.1, 2.9, 3.6, 3.2); arrow(s, 4.9, 3.2, 5.2, 3.2); arrow(s, 3.1, 3.0, 3.6, 4.2);
arrow(s, 7.8, 1.65, 8.3, 2.7); arrow(s, 6.7, 3.2, 8.3, 2.9); arrow(s, 4.8, 4.2, 8.3, 3.0);
s.addText("documents: top-6 chunks from pgvector, WHERE superseded = false before ranking", { x: 3.6, y: 0.98, w: 5.9, h: 0.3, fontSize: 10, color: C.accent5, isTextBox: true, margin: 0 });
s.addText("database: one read-only SELECT, 5 s timeout, one retry", { x: 3.6, y: 3.52, w: 3.0, h: 0.3, fontSize: 10, color: C.accent5, isTextBox: true, margin: 0 });
s.addText("general: greetings only; forbidden from stating facts", { x: 3.6, y: 4.52, w: 5.9, h: 0.3, fontSize: 10, color: C.accent5, isTextBox: true, margin: 0 });
s.addText("Every node appends its milliseconds and tokens to the trace; the API streams one event per node.", { x: 0.5, y: 4.85, w: 9, h: 0.3, fontSize: 11, italic: true, color: C.accent5, isTextBox: true, margin: 0 });
s.addNotes("Walk the three paths. Point out that the version filter is a WHERE clause in code, before the vector ranking, not a prompt instruction.");

// ================= 4 stack
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "How it works" });
s.addText("The stack, all local", { placeholder: "title" });
const stack = [["Postgres 16 + pgvector 0.8", "In Docker on 127.0.0.1:5433. Tables documents (name, version, superseded, effective_date), chunks (vector(768), HNSW), uploaded_tables."],
  ["Ollama", "llama3.2:3b for every LLM call; nomic-embed-text (768 d) for embeddings; qwen2.5vl:3b for drawings. OpenAI-compatible endpoint, so the openai SDK is the only client."],
  ["LangGraph 1.2", "StateGraph with conditional edges; nodes are plain functions with a timing decorator."],
  ["Ingestion", "Markdown and PDF to paragraph-packed chunks; front-matter becomes version metadata and is stripped before embedding; CSV/Excel become SQL tables."],
  ["FastAPI + web/", "/upload, /chat (server-sent events), /eval, /health; a static page renders the node stream. Gradio as a second UI."],
  ["Evaluation scripts", "eval.py (answer level), b1_eval.py (retrieval OFF/ON), b1_check.py (data checks + negative tests), pid_eval.py, summarize_series.py, recreate.sh."]];
stack.forEach((it, i) => { const col = i % 2, row = Math.floor(i / 2); card(s, 0.5 + col * 4.6, 1.15 + row * 1.3, 4.4, 1.18, it[0], it[1]); });
s.addNotes("No hosted service anywhere. That is what made the honest measurement cheap to repeat.");

// ================= 5 phases
pres.addSection({ title: "How it was built" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "How it was built" });
s.addText("Twenty-five steps in six phases", { placeholder: "title" });
const ph = [["1", "Build", "DB, ingest, graph, golden set frozen before any code, eval, API + UI (steps 1–8)"],
  ["2", "Improve", "router, SQL rules, per-passage grader; one change at a time, committed before measuring (9–14)"],
  ["3", "Measure", "25 unseen questions, 3+4 repeated runs, mean and range, the gap stated (15–18)"],
  ["4", "Negative", "8B grader on this CPU: recorded with evidence, switch kept for a GPU (19)"],
  ["5", "Versions", "16 runbooks old/current, data checks, OFF/ON ablation, default ON (20)"],
  ["6", "Close out", "browser checks, LangSmith opt-in, static front end, P&ID branch, site (21–25)"]];
ph.forEach((p, i) => { const x = 0.5 + i * 1.55;
  s.addShape(pres.ShapeType.ellipse, { x: x + 0.45, y: 1.3, w: 0.6, h: 0.6, fill: { color: i === 3 ? F.accent2 : F.accent1 }, line: { color: F.lt1 }, objectName: "phase " + p[0] });
  s.addText(p[0], { x: x + 0.45, y: 1.3, w: 0.6, h: 0.6, fontSize: 18, bold: true, color: C.background1, align: "center", valign: "middle", isTextBox: true, margin: 0 });
  if (i < 5) arrow(s, x + 1.1, 1.6, x + 1.95, 1.6);
  s.addText(p[1], { x, y: 2.05, w: 1.5, h: 0.4, fontSize: 15, bold: true, color: C.text2, align: "center", isTextBox: true, margin: 0 });
  s.addText(p[2], { x, y: 2.5, w: 1.5, h: 2.0, fontSize: 10.5, color: C.text1, align: "center", isTextBox: true, margin: 0, valign: "top" }); });
s.addText("Every step in the SOP has the problem found, the change, how it was verified, and the commands used.", { x: 0.5, y: 4.7, w: 9, h: 0.35, fontSize: 12, italic: true, color: C.accent5, isTextBox: true, margin: 0 });
s.addNotes("Phase 4 is red on purpose: a recorded negative result is part of the method, not a failure of it.");

// ================= 6 method
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "How it was built" });
s.addText("How the numbers were kept honest", { placeholder: "title" });
const rules = [["Freeze first", "The golden set was committed before the pipeline existed; the unseen set before its first run. Git order is the evidence."],
  ["Never tune on the test", "A first router draft copied golden questions as examples; it was replaced before any run. Scorer fixes go in an amendments file, never in the frozen set."],
  ["Commit before measuring", "One prompt change at a time, full run, compared by failing case ids, not just the percentage."],
  ["Report ranges", "Three held-out runs and four tuned-set runs; the 7.6-point gap between them is stated as the over-fitting measure."],
  ["Fair latency", "OFF and ON interleaved in one process after a warm-up; a single cold run once showed a false 3× difference."],
  ["Record negatives", "qwen3:8b could not grade six passages in usable time on this CPU; the switch stays, the evidence is in the SOP."]];
rules.forEach((r, i) => { const col = i % 2, row = Math.floor(i / 2), x = 0.5 + col * 4.6, y = 1.15 + row * 1.3;
  s.addShape(pres.ShapeType.ellipse, { x, y: y + 0.1, w: 0.5, h: 0.5, fill: { color: F.accent1 }, line: { color: F.accent1 }, objectName: "rule " + (i + 1) });
  s.addText(String(i + 1), { x, y: y + 0.1, w: 0.5, h: 0.5, fontSize: 14, bold: true, color: C.background1, align: "center", valign: "middle", isTextBox: true, margin: 0 });
  s.addText(r[0], { x: x + 0.65, y, w: 3.7, h: 0.4, fontSize: 14, bold: true, color: C.text2, isTextBox: true, margin: 0 });
  s.addText(r[1], { x: x + 0.65, y: y + 0.42, w: 3.75, h: 0.85, fontSize: 11, color: C.text1, isTextBox: true, margin: 0, valign: "top" }); });
s.addNotes("These six rules are what make the next two slides trustworthy.");

// ================= 7 results chart
pres.addSection({ title: "Results" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("Results: tuned set vs unseen set", { placeholder: "title" });
s.addChart(pres.ChartType.bar, [{ name: "Tuned set (27, mean of 4 runs)", labels: ["Router accuracy", "Answers correct", "Retrieval hit rate"], values: [100, 88.9, 100] },
  { name: "Unseen set (25, mean of 3 runs)", labels: ["Router accuracy", "Answers correct", "Retrieval hit rate"], values: [96, 81.3, 100] }],
  { x: 0.5, y: 1.15, w: 5.6, h: 3.9, barDir: "col", chartColors: [F.accent1, F.accent6], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", dataLabelFontSize: 10, dataLabelColor: F.dk1, dataLabelFontFace: "+mn-lt",
    valAxisMinVal: 0, valAxisMaxVal: 110, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, catAxisLabelColor: F.accent5, catAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt",
    showLegend: true, legendPos: "b", legendFontSize: 10, legendColor: F.accent5, legendFontFace: "+mn-lt", showTitle: true, title: "Percent (llama3.2:3b)", titleFontSize: 11, titleColor: F.accent5, titleFontFace: "+mn-lt", barGapWidthPct: 60 });
stat(s, 6.5, 1.2, 3.0, "7.6 pts", "the gap between tuned and unseen answer accuracy: the honest measure of over-fitting", C.accent4);
stat(s, 6.5, 2.6, 3.0, "4 cases", "fail in every held-out run: three are the 3B grader rejecting a differently phrased passage, one is a router ambiguity", C.accent2);
stat(s, 6.5, 4.0, 3.0, "100%", "unanswerable questions refused, every run; general questions never answered with facts", C.accent3);
s.addNotes("Routing and retrieval generalise; answer accuracy drops 7.6 points on unseen questions, and the failing ids are the same every run, so they are model limits, not noise.");

// ================= 8 version filter
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("Version-aware retrieval: the trap and the fix", { placeholder: "title" });
s.addChart(pres.ChartType.bar, [{ name: "Filter OFF", labels: ["Superseded chunks retrieved (%)"], values: [51.6] }, { name: "Filter ON", labels: ["Superseded chunks retrieved (%)"], values: [0] }],
  { x: 0.5, y: 1.15, w: 3.4, h: 3.0, barDir: "col", chartColors: [F.accent2, F.accent3], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", dataLabelFontSize: 11, dataLabelColor: F.dk1, dataLabelFontFace: "+mn-lt",
    valAxisMinVal: 0, valAxisMaxVal: 60, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, catAxisLabelColor: F.accent5, catAxisLabelFontSize: 10, catAxisLabelFontFace: "+mn-lt",
    showLegend: true, legendPos: "b", legendFontSize: 10, legendColor: F.accent5, legendFontFace: "+mn-lt", showTitle: true, title: "99/192 → 0/192 chunks", titleFontSize: 11, titleColor: F.accent5, titleFontFace: "+mn-lt", barGapWidthPct: 40 });
s.addTable([[{ text: "Retrieval only, 32 frozen cases", options: { bold: true, color: F.lt1, fill: { color: F.dk2 } } }, { text: "OFF", options: { bold: true, color: F.lt1, fill: { color: F.dk2 } } }, { text: "ON", options: { bold: true, color: F.lt1, fill: { color: F.dk2 } } }],
  ["Version-trap cases passing (facts present, no stale value from an old chunk)", "2/12", "12/12"], ["Control cases passing (must stay flat)", "20/20", "20/20"], ["Median retrieve, interleaved ×3, 96 calls each", "56 ms", "57 ms"],
  ["Pair similarity old vs current (nomic-embed-text)", { text: "0.962 – 0.990", options: { colspan: 2 } }]],
  { x: 4.2, y: 1.15, w: 5.3, colW: [3.5, 0.9, 0.9], fontSize: 10.5, color: F.dk1, border: { type: "solid", color: "D9DEE5", pt: 0.75 }, valign: "middle", rowH: 0.42 });
s.addText("How: each document version carries version, effective_date and superseded; retrieve() adds WHERE d.superseded = false before ORDER BY, so an old runbook that is 0.99-similar to the question is never a candidate. One line of SQL, behind a switch, default ON since the ablation was recorded.",
  { x: 4.2, y: 3.5, w: 5.3, h: 1.0, fontSize: 11, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
s.addText("At answer level both settings scored 88.9% on this corpus (its current runbooks name their former values); multi-hop improved 0/2 → 1/2 with the filter on.", { x: 0.5, y: 4.55, w: 9, h: 0.5, fontSize: 10.5, italic: true, color: C.accent5, isTextBox: true, margin: 0 });
s.addNotes("The headline is the left chart. The right table shows the control cases did not move and the cost is one millisecond.");

// ================= 9 decisions
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("Decisions taken on evidence", { placeholder: "title" });
const dec = [["Stronger grader: tested, not possible here", "qwen3:8b grades one passage in 33–52 s but never returned six passages in 20 minutes on this CPU; the runner sat at 578% CPU. The escalate design and switch are in place for a GPU or hosted model.", C.accent2],
  ["Next.js: descoped", "Node 24 is installed, so it was possible; it adds a toolchain and hosting without changing anything measured. A static page proves the streaming contract instead.", C.accent4],
  ["Docling: blocked on Intel macOS", "Last torch wheel is 2.2.2; the layout model needs newer transformers and numpy 2. PDFs use pypdf text; run Docling elsewhere and ingest the Markdown.", C.accent4],
  ["The 'outages' were sleep", "Three service failures traced in the system log to the Mac sleeping; every long script now re-execs under caffeinate, and the runbook has the checklist.", C.accent3]];
dec.forEach((d, i) => { const col = i % 2, row = Math.floor(i / 2); card(s, 0.5 + col * 4.6, 1.15 + row * 1.9, 4.4, 1.75, d[0], d[1], d[2]); });
s.addNotes("Each of these is written up with its evidence in the SOP; none is a guess.");

// ================= 10 interfaces
pres.addSection({ title: "Showcase" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Showcase" });
s.addText("Two interfaces on one streaming API", { placeholder: "title" });
s.addImage({ path: IMG("web_chat_crop.png"), x: 0.5, y: 1.3, w: 4.4, h: 1.94, objectName: "web front end screenshot", altText: "static page showing node pills and an SQL answer" });
s.addImage({ path: IMG("gradio_chat_crop.png"), x: 5.1, y: 1.3, w: 4.4, h: 2.48, objectName: "Gradio screenshot", altText: "Gradio chat answering 75% with a trace line" });
s.addText("web/index.html: one pill per graph node as it finishes, then the answer, route, SQL and citations. No build step; served by FastAPI at /.", { x: 0.5, y: 3.95, w: 4.4, h: 0.75, fontSize: 11, color: C.text1, isTextBox: true, margin: 0 });
s.addText("Gradio: chat with the trace line under each answer; upload documents and tables. Both were exercised in headless Chromium with live questions.", { x: 5.1, y: 3.95, w: 4.4, h: 0.75, fontSize: 11, color: C.text1, isTextBox: true, margin: 0 });
s.addNotes("Both screenshots are from real runs on the Mac; the latencies in the pills are real.");

// ================= 11 P&ID
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Showcase" });
s.addText("P&ID branch: drawings into the same index", { placeholder: "title" });
s.addImage({ path: IMG("pid_001_example.png"), x: 0.5, y: 1.15, w: 4.7, h: 3.0, objectName: "synthetic P&ID", altText: "synthetic piping and instrumentation diagram" });
s.addTable([[{ text: "Run 2 (qwen2.5vl:3b, ~100 s per drawing)", options: { bold: true, color: F.lt1, fill: { color: F.dk2 } } }, { text: "", options: { fill: { color: F.dk2 } } }],
  ["Tags read correctly (3 drawings)", "36/39, none invented"], ["Right drawing retrieved", "12/12"], ["Answers correct, 12 frozen questions", "5/12"],
  ["what an instrument measures, on what", "3/3"], ["valve isolating a pump", "1/3"], ["controller + control valve", "1/3"], ["which drawing / unit", "0/3"]],
  { x: 5.4, y: 1.15, w: 4.1, colW: [2.7, 1.4], fontSize: 10.5, color: F.dk1, border: { type: "solid", color: "D9DEE5", pt: 0.75 }, rowH: 0.33 });
s.addText("Synthetic drawings from one template with every tag in a ground-truth file (real P&IDs are confidential). What fails is the same 3B grader that limits the text pipeline, plus the title-block subtitle and small text near symbol edges: exactly what a real set will exercise first. Start a real project from a golden set like this one, on a GPU-class vision model.",
  { x: 0.5, y: 4.25, w: 9, h: 0.85, fontSize: 10.5, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
s.addNotes("This was the colleague's proposed direction. The scaffold and the measurement method transfer; the model needs to be bigger.");

// ================= 12 site + test
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Showcase" });
s.addText("See it, test it", { placeholder: "title" });
s.addImage({ path: IMG("site_top.png"), x: 0.5, y: 1.15, w: 4.7, h: 3.4, objectName: "showcase site screenshot", altText: "the ragcap showcase site" });
s.addText([{ text: "Live showcase (GitHub Pages, static): ", options: { bold: true } }, { text: PAGES, options: { hyperlink: { url: PAGES }, color: C.accent1 } }],
  { x: 5.4, y: 1.15, w: 4.1, h: 0.6, fontSize: 12, color: C.text1, isTextBox: true, margin: 0 });
s.addText("Results, the flow, screenshots, the documents, and a replay of 64 recorded runs: pick a question, see its route, node timings, answer, and for version cases the documents retrieved OFF vs ON.", { x: 5.4, y: 1.75, w: 4.1, h: 0.9, fontSize: 10.5, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
s.addText([{ text: "Test it live (45 min, Docker + Ollama + Python 3.12):", options: { bold: true, breakLine: true } },
  { text: "git clone " + REPO, options: { fontFace: "Courier New", fontSize: 9.5, breakLine: true } },
  { text: "cd ragcap && ./recreate.sh", options: { fontFace: "Courier New", fontSize: 9.5, breakLine: true } },
  { text: "Then try the scenario catalogue in docs/RECREATE.pdf, for example:", options: { breakLine: true } },
  { text: "VERSION_AWARE=0 … \"At what disk utilisation should a broker page?\" → often 85% (the trap)", options: { fontSize: 10, breakLine: true } },
  { text: "VERSION_AWARE=1 … the same question → 75% (the fix)", options: { fontSize: 10, breakLine: true } },
  { text: "\"Which brokers are above 85% disk usage?\" → SQL agent, brokers 3 and 5", options: { fontSize: 10 } }],
  { x: 5.4, y: 2.75, w: 4.1, h: 1.9, fontSize: 11, color: C.text1, isTextBox: true, margin: 0, valign: "top", paraSpaceAfter: 3 });
s.addText([{ text: "Documents: " }, { text: "SOP", options: { hyperlink: { url: PAGES + "docs/SOP_ragcap_build.pdf" }, color: C.accent1 } }, { text: "  ·  " }, { text: "Runbook", options: { hyperlink: { url: PAGES + "docs/RUNBOOK_ragcap_operations.pdf" }, color: C.accent1 } }, { text: "  ·  " }, { text: "Recreate guide", options: { hyperlink: { url: PAGES + "docs/RECREATE_ragcap.pdf" }, color: C.accent1 } }],
  { x: 0.5, y: 4.7, w: 9, h: 0.35, fontSize: 11, color: C.text1, isTextBox: true, margin: 0 });
s.addNotes("The site is static: the replay is recorded. recreate.sh exits 1 if any fingerprint differs from the recorded ones.");

// ================= 13 vercel
pres.addSection({ title: "Deploy" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Deploy" });
s.addText("Deploying the site to Vercel, step by step", { placeholder: "title" });
const vs = [["1", "Sign in", "vercel.com → Continue with GitHub (the account that owns shreenathacc22/ragcap)."],
  ["2", "Import", "Add New → Project → Import Git Repository → shreenathacc22/ragcap. Authorise the Vercel GitHub app for this repo if asked."],
  ["3", "Settings", "Framework Preset: Other. Root Directory: leave as the repo root. Build Command: empty. Output Directory: site (vercel.json already says so)."],
  ["4", "Deploy", "Click Deploy; the first URL looks like ragcap-<hash>.vercel.app and opens the same site as GitHub Pages."],
  ["5", "Domain", "Settings → Domains → add ragcap.vercel.app (or any free name); paste the URL into README.md and the site, run publish_site.sh."],
  ["6", "Keep it current", "Every git push to main redeploys; the Deployments tab shows each build. CLI alternative: npm i -g vercel && vercel login && vercel --prod."]];
vs.forEach((v, i) => { const col = i % 2, row = Math.floor(i / 2), x = 0.5 + col * 4.6, y = 1.15 + row * 1.25;
  s.addShape(pres.ShapeType.ellipse, { x, y: y + 0.08, w: 0.5, h: 0.5, fill: { color: F.dk2 }, line: { color: F.dk2 }, objectName: "vercel step " + v[0] });
  s.addText(v[0], { x, y: y + 0.08, w: 0.5, h: 0.5, fontSize: 14, bold: true, color: C.background1, align: "center", valign: "middle", isTextBox: true, margin: 0 });
  s.addText(v[1], { x: x + 0.65, y, w: 3.7, h: 0.38, fontSize: 14, bold: true, color: C.text2, isTextBox: true, margin: 0 });
  s.addText(v[2], { x: x + 0.65, y: y + 0.4, w: 3.75, h: 0.82, fontSize: 10.5, color: C.text1, isTextBox: true, margin: 0, valign: "top" }); });
s.addText("Why only the site: the pipeline needs Postgres + pgvector and Ollama, which neither Vercel nor Pages run. GitHub Pages is already live from the gh-pages branch (publish_site.sh); Vercel serves the identical site/ folder once imported.", { x: 0.5, y: 4.85, w: 9, h: 0.4, fontSize: 10, italic: true, color: C.accent5, isTextBox: true, margin: 0 });
s.addNotes("Three minutes in the Vercel dashboard. The CLI path needs an interactive login, which is why it was not done from the build machine.");

// ================= 14 recreate
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Deploy" });
s.addText("Recreating it anywhere", { placeholder: "title" });
s.addText([{ text: "git clone " + REPO + " && cd ragcap", options: { breakLine: true } }, { text: "open -a Docker; ollama pull llama3.2:3b; ollama pull nomic-embed-text", options: { breakLine: true } },
  { text: "./recreate.sh          # DB, ingest, checks, fingerprints, OFF/ON ablation, smoke questions", options: { breakLine: true } },
  { text: ".venv/bin/uvicorn api:app --port 8000     # http://127.0.0.1:8000/", options: { breakLine: true } },
  { text: "./run_series.sh mylabel llama3.2:3b     # repeated runs; summarize_series.py mylabel", options: { breakLine: true } },
  { text: ".venv/bin/python pid_eval.py --ingest   # P&ID branch (ollama pull qwen2.5vl:3b first)" }],
  { x: 0.5, y: 1.15, w: 9, h: 1.55, fontFace: "Courier New", fontSize: 11, color: C.text1, fill: { color: F.lt2 }, isTextBox: true, margin: 10, valign: "top" });
s.addTable([[{ text: "Fingerprint", options: { bold: true, color: F.lt1, fill: { color: F.dk2 } } }, { text: "Value a correct rebuild must match", options: { bold: true, color: F.lt1, fill: { color: F.dk2 } } }],
  ["Database after ingest", "16 docs, 16 chunks, 8 superseded, 1 table"], ["Data checks", "PASS; pair similarity 0.962–0.990; three negative tests reported"],
  ["Retrieval ablation", "OFF 99/192 (51.6%) → ON 0/192 (0.0%); trap 2/12 → 12/12; control 20/20"], ["Golden sets (sha1 prefixes)", "golden 68ec09bd…, held-out 02ddcfd6…, P&ID 10fe1aa6…"]],
  { x: 0.5, y: 3.0, w: 9, colW: [2.4, 6.6], fontSize: 10.5, color: F.dk1, border: { type: "solid", color: "D9DEE5", pt: 0.75 }, rowH: 0.3 });
s.addNotes("recreate.sh checks every row of this table and stops on the first mismatch.");

// ================= 15 close
s = pres.addSlide({ masterName: "DARK", sectionTitle: "Deploy" });
s.addText("What this shows", { placeholder: "title" });
s.addText([{ text: "A design can be reproduced on a laptop with no API key. What makes it credible is not the architecture but the measurement: a frozen test set, an unseen set, ranges over repeated runs, a filter proven OFF against ON, and negatives written down with their evidence.", options: { breakLine: true } },
  { text: "Next, on a GPU or hosted model: the escalate grader, a real P&ID set with its own golden questions, and LangSmith with a real key.", options: { fontSize: 13, color: C.background2 } }], { placeholder: "body" });
s.addText([{ text: REPO, options: { hyperlink: { url: REPO }, color: C.background1 } }, { text: "    ·    " }, { text: PAGES, options: { hyperlink: { url: PAGES }, color: C.background1 } }],
  { x: 0.6, y: 4.7, w: 8.8, h: 0.4, fontSize: 12, color: C.background1, isTextBox: true, margin: 0 });
s.addNotes("Close on the two links. Offer the method before the numbers.");

(async () => { await pres.writeFile({ fileName: path.join(__dirname, "ragcap_deck.pptx") }); await applyTheme(path.join(__dirname, "ragcap_deck.pptx"), THEME); console.log("deck written"); })();

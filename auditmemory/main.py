import os, json, re
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import memory, rules

app = FastAPI(title="AuditMemory")
RANK = ["low", "medium", "high", "critical"]

class Check(BaseModel):
    vendor: str
    product: str = ""
    label_text: str
class Feedback(BaseModel):
    vendor: str
    rule: str
    verdict: str  # confirmed | false_positive
    note: str = ""

def count(snips, rule, tag):
    return sum(1 for s in snips if f"RULE={rule}" in s and tag in s)

def bump(sev, n):
    return RANK[min(RANK.index(sev) + n, 3)]

def narrate(vendor, findings, snips):
    """LLM summary grounded in recalled memory (Groq); templated fallback."""
    if os.getenv("GROQ_API_KEY"):
        try:
            from groq import Groq
            r = Groq().chat.completions.create(model="openai/gpt-oss-120b", messages=[
                {"role": "system", "content": "You are a Legal Metrology compliance officer's assistant. Write 2 short sentences: what to act on first, citing vendor history."},
                {"role": "user", "content": json.dumps({"vendor": vendor, "findings": findings, "memory": snips[-8:]})}])
            return r.choices[0].message.content.strip()
        except Exception as e: print("llm failed:", e)
    if not findings: return "No violations found."
    top = findings[0]
    hist = f" Seen {top['repeat']}x before for this vendor." if top["repeat"] else " First time this vendor is flagged."
    return f"Act first on: {top['title']}.{hist}"

@app.post("/api/check")
def check(c: Check):
    snips = memory.recall(c.vendor)
    out = []
    for f in rules.check(c.label_text):
        rep = count(snips, f["rule"], "STATUS=violation")
        fp = count(snips, f["rule"], "STATUS=false_positive")
        f["repeat"], f["fp"] = rep, fp
        f["memory_note"] = None
        if fp >= 2:
            f["severity"] = "low"
            f["memory_note"] = f"Officers marked this a false positive {fp}x for this vendor: downgraded."
        elif rep >= 1:
            f["severity"] = bump(f["severity"], 2 if rep >= 2 else 1)
            f["memory_note"] = f"Repeat offender: flagged {rep}x before. Severity escalated."
        out.append(f)
    out.sort(key=lambda f: -RANK.index(f["severity"]))
    for f in out:
        memory.retain(f"VENDOR={c.vendor} PRODUCT={c.product} RULE={f['rule']} STATUS=violation SEVERITY={f['severity']}")
    if not out:
        memory.retain(f"VENDOR={c.vendor} PRODUCT={c.product} STATUS=compliant")
    return {"findings": out, "summary": narrate(c.vendor, out, snips), "memory_mode": memory.mode(),
            "history_count": len(snips)}

class Img(BaseModel):
    image: str  # data URL

@app.post("/api/ocr")
def ocr(i: Img):
    """Read label text from a photo using a Groq vision model."""
    if not os.getenv("GROQ_API_KEY"):
        return {"text": "", "error": "GROQ_API_KEY is not set on the server."}
    from groq import Groq
    models = [x for x in [os.getenv("VISION_MODEL"), "qwen/qwen3.6-27b", "qwen/qwen3.8-27b"] if x]
    err = ""
    for model in models:
        try:
            r = Groq().chat.completions.create(model=model, messages=[{"role": "user", "content": [
                {"type": "text", "text": "Transcribe all text on this product label exactly as printed. Output only the text, no commentary."},
                {"type": "image_url", "image_url": {"url": i.image}}]}])
            t = re.sub(r"<think>.*?</think>", "", r.choices[0].message.content or "", flags=re.S).strip()
            if t: return {"text": t}
        except Exception as e:
            err = str(e)
    return {"text": "", "error": f"Could not read the image: {err}"}

@app.post("/api/feedback")
def feedback(f: Feedback):
    memory.retain(f"VENDOR={f.vendor} RULE={f.rule} STATUS={f.verdict} NOTE={f.note}", context="officer feedback")
    return {"ok": True}

@app.get("/api/history")
def history(vendor: str):
    return {"items": memory.recall(vendor)}

@app.get("/")
def index(): return FileResponse("static/index.html")
app.mount("/static", StaticFiles(directory="static"), name="static")

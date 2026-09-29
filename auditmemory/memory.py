"""Memory layer. Uses Hindsight when configured; otherwise a local fallback so the demo always runs."""
import os, time
BANK = "auditmemory"
_local = []
_client = None
if os.getenv("HINDSIGHT_API_KEY"):
    try:
        from hindsight_client import Hindsight
        _client = Hindsight(base_url=os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io"),
                            api_key=os.environ["HINDSIGHT_API_KEY"])
    except Exception as e:
        print("Hindsight unavailable, using local memory:", e)

def mode(): return "hindsight" if _client else "local"

def retain(text: str, context: str = "audit"):
    _local.append({"text": text, "ts": time.time()})
    if _client:
        try: _client.retain(bank_id=BANK, content=text, context=context)
        except Exception as e: print("retain failed:", e)

def recall(vendor: str, query: str = "") -> list[str]:
    """Return memory snippets about a vendor."""
    if _client:
        try:
            r = _client.recall(bank_id=BANK, query=f"{vendor} {query}".strip())
            res = getattr(r, "results", r) or []
            out = [getattr(x, "text", str(x)) for x in res]
            return [t for t in out if vendor.lower() in t.lower()]
        except Exception as e: print("recall failed:", e)
    return [m["text"] for m in _local if vendor.lower() in m["text"].lower()]

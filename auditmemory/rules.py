"""Rule engine: simplified Legal Metrology (Packaged Commodities) Rules, 2011 checks."""
import re
RULES = {
 "mrp": ("MRP inclusive of all taxes", r"(m\.?r\.?p\.?|maximum retail price).{0,30}(rs\.?|₹|inr)?\s*\d", "high"),
 "net_qty": ("Net quantity declaration", r"(net\s*(qty|quantity|wt|weight|content)|\b\d+(\.\d+)?\s?(g|kg|ml|l)\b)", "high"),
 "mfg_date": ("Month & year of manufacture/packing", r"(mfg|manufactur|packed|pkd).{0,20}(\d{1,2}[/-]\d{2,4}|[a-z]{3}\s*\d{2,4})", "medium"),
 "address": ("Manufacturer/packer/importer name & address", r"(manufactured|packed|marketed|imported)\s*by.{5,}", "high"),
 "care": ("Consumer care details", r"(customer|consumer)\s*care|toll\s*free|helpline|@[a-z0-9.-]+\.[a-z]{2,}", "medium"),
}
def check(text: str):
    t = text.lower()
    return [{"rule": k, "title": v[0], "severity": v[2]} for k, v in RULES.items() if not re.search(v[1], t)]

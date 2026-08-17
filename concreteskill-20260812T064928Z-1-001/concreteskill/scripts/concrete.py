#!/usr/bin/env python3
"""concreteskill — builds both sides of the concrete market.

DEMAND  live-pulled from the Department of Labor every run, so the crew dates
        and wages are current.
SUPPLY  read from the cached roster shipped with this skill.

Stdlib only. No API keys. No paid tools.

Usage:
    python3 concrete.py                      # both sides -> ~/Desktop
    python3 concrete.py --out ~/lists        # choose the folder
    python3 concrete.py --demand-only
    python3 concrete.py --supply-only
    python3 concrete.py --state TX,CO,IA     # filter both sides
"""
import csv, gzip, os, re, subprocess, sys, zipfile
from datetime import date, timedelta

HERE      = os.path.dirname(os.path.abspath(__file__))
SUPPLY_GZ = os.path.join(HERE, "..", "data", "bond_agents.csv.gz")
# Workbooks cache outside the skill folder so the skill stays small and portable.
CACHE     = os.path.expanduser("~/.cache/concreteskill")
DOL_PERF  = "https://www.dol.gov/agencies/eta/foreign-labor/performance"

# Concrete family. Masonry, rebar, precast, gunite, terrazzo, ready-mix.
SOC   = re.compile(r'cement mason|concrete finish|\bconcrete\b|\bmason(ry|s)?\b|rebar|reinforcing iron|terrazzo', re.I)
NAME  = re.compile(r'\b(concrete|cement|masonry|gunite|shotcrete|terrazzo|rebar|precast|ready[- ]?mix|readymix|curb(ing)?)\b', re.I)
NAICS = ('23811', '23814', '32732')
EMAIL_OK = re.compile(r'^[^@\s]+@[^@\s]+\.[a-z]{2,}$', re.I)


def die(msg):
    print(f"\n  {msg}\n", file=sys.stderr)
    sys.exit(1)


def curl(url, out=None):
    """dol.gov accepts curl's DEFAULT user-agent and rejects a browser one.
    Do not add -A here; a browser string turns this into a 403."""
    cmd = ["curl", "-sfL", "--max-time", "580", url] + (["-o", out] if out else [])
    r = subprocess.run(cmd, capture_output=not out)
    if r.returncode:
        die(f"could not reach {url} (curl {r.returncode}). Check the connection and rerun.")
    return r.stdout.decode("utf-8", "replace") if not out else None


def free_path(folder, stem, ext=".csv"):
    """Never overwrite. Pick the next free name and let the caller announce it."""
    p = os.path.join(folder, stem + ext)
    n = 2
    while os.path.exists(p):
        p = os.path.join(folder, f"{stem}-{n}{ext}")
        n += 1
    return p


def titlecase(s):
    return " ".join(w.capitalize() if w.isupper() or w.islower() else w for w in s.split())


def excel_date(v):
    """Dates in these workbooks arrive as Excel serial numbers (45383), and in
    older files as text. Serial 1 is 1900-01-01, with Excel's phantom 1900 leap
    day to skip. A raw serial in the output looks like a plausible number and
    silently breaks any date filter, so it is converted here."""
    v = (v or "").strip()
    if not v:
        return ""
    if re.fullmatch(r'\d+(\.0+)?', v):
        n = int(float(v))
        if 1 < n < 80000:
            return (date(1899, 12, 30) + timedelta(days=n)).isoformat()
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', v)
    if m:
        return m.group(0)
    m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', v)
    if m:
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return v[:10]


# ---------------------------------------------------------------- xlsx reader
def rows_from_xlsx(path):
    """Stream a workbook using only zipfile + re, so nothing needs installing."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            xml = z.read("xl/sharedStrings.xml").decode("utf-8", "replace")
            shared = [re.sub(r'<[^>]+>', '', m) for m in re.findall(r'<si>(.*?)</si>', xml, re.S)]
        sheet = next(n for n in z.namelist() if re.match(r'xl/worksheets/sheet1\.xml', n))
        xml = z.read(sheet).decode("utf-8", "replace")

    def col_index(col):
        n = 0
        for ch in col:
            n = n * 26 + (ord(ch) - 64)
        return n - 1

    def cells(rowxml):
        out = {}
        for m in re.finditer(r'<c\b([^>]*?)(?:/>|>(.*?)</c>)', rowxml, re.S):
            attrs, body = m.group(1), m.group(2) or ""
            ref = re.search(r'r="([A-Z]+)\d+"', attrs)
            if not ref:
                continue
            v = ""
            vm = re.search(r'<v>(.*?)</v>', body, re.S)
            if vm:
                v = vm.group(1)
                if 't="s"' in attrs:
                    try:
                        v = shared[int(v)]
                    except (ValueError, IndexError):
                        v = ""
            elif 't="inlineStr"' in attrs:
                v = re.sub(r'<[^>]+>', '', body)
            out[col_index(ref.group(1))] = (v.replace("&amp;", "&")
                                             .replace("&lt;", "<")
                                             .replace("&gt;", ">")
                                             .replace("&#39;", "'")
                                             .replace("&quot;", '"').strip())
        return out

    hdr = None
    for rowxml in re.findall(r'<row\b[^>]*>(.*?)</row>', xml, re.S):
        cs = cells(rowxml)
        if not cs:
            continue
        flat = [""] * (max(cs) + 1)
        for i, v in cs.items():
            flat[i] = v
        if hdr is None:
            hdr = [h.strip().upper() for h in flat]
            continue
        flat += [""] * (len(hdr) - len(flat))
        yield dict(zip(hdr, flat))


def pick(row, *names):
    for n in names:
        if row.get(n):
            return row[n].strip()
    return ""


# ------------------------------------------------------------------- lanes
def build_demand(states):
    os.makedirs(CACHE, exist_ok=True)
    html = curl(DOL_PERF)
    urls = sorted({("https://www.dol.gov" + h if h.startswith("/") else h)
                   for h in re.findall(r'href="([^"]+\.xlsx)"', html)
                   if "H-2B" in h and "Appendix" not in h})
    if not urls:
        die("the Department of Labor page layout changed and no files were found. "
            "Open " + DOL_PERF + " and look for the H-2B disclosure workbooks.")

    best, collisions = {}, 0
    for url in urls:
        fn = os.path.join(CACHE, url.rsplit("/", 1)[-1])
        if not os.path.exists(fn):
            print(f"  reading {os.path.basename(fn)}", flush=True)
            curl(url, out=fn)
        if open(fn, "rb").read(2) != b"PK":
            continue
        for r in rows_from_xlsx(fn):
            status = pick(r, "CASE_STATUS")
            if status and "CERTIF" not in status.upper():
                continue
            email = pick(r, "EMPLOYER_POC_EMAIL", "EMPLOYER_EMAIL").lower()
            if not EMAIL_OK.match(email):
                continue          # drop malformed rather than repair by guessing
            company = pick(r, "EMPLOYER_NAME")
            dba     = pick(r, "TRADE_NAME_DBA", "EMPLOYER_TRADE_NAME")
            soc     = pick(r, "SOC_TITLE", "SOC_NAME")
            code    = pick(r, "NAICS_CODE")
            if not (SOC.search(soc) or NAME.search(company + " " + dba) or code.startswith(NAICS)):
                continue
            st = pick(r, "EMPLOYER_STATE", "EMPLOYER_POC_STATE").upper()
            if states and st not in states:
                continue
            # Convert BEFORE comparing. Raw serials and ISO strings sort against
            # each other incorrectly, which silently keeps the wrong filing.
            when = excel_date(pick(r, "DECISION_DATE"))
            if email in best:
                collisions += 1
                if when <= best[email]["_when"]:
                    continue      # a filer re-files each season; keep the newest
            best[email] = {
                "email": email,
                "firstName": titlecase(pick(r, "EMPLOYER_POC_FIRST_NAME")),
                "lastName":  titlecase(pick(r, "EMPLOYER_POC_LAST_NAME")),
                "title":     pick(r, "EMPLOYER_POC_JOB_TITLE"),
                "company":   dba or company,
                "city":      titlecase(pick(r, "EMPLOYER_CITY", "EMPLOYER_POC_CITY")),
                "state":     st,
                "workers":   pick(r, "TOTAL_WORKERS_CERTIFIED", "NBR_WORKERS_CERTIFIED",
                                     "TOTAL_WORKERS_H-2B_CERTIFIED"),
                "crewStart": excel_date(pick(r, "EMPLOYMENT_BEGIN_DATE", "REQUESTED_BEGIN_DATE",
                                                "BEGIN_DATE")),
                "wagePerHour": pick(r, "BASIC_WAGE_RATE_FROM", "WAGE_OFFER_FROM",
                                       "WAGE_RATE_OF_PAY_FROM"),
                "_when": when,
            }
    for v in best.values():
        v.pop("_when", None)
    return sorted(best.values(), key=lambda x: (x["state"], x["company"])), collisions


def build_supply(states):
    if not os.path.exists(SUPPLY_GZ):
        die("the bond agent roster is missing from this skill's data folder.")
    with gzip.open(SUPPLY_GZ, "rt", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if EMAIL_OK.match(r["email"])]
    if states:
        rows = [r for r in rows if r["state"].upper() in states]
    return rows


def write(rows, path, cols):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main():
    args = sys.argv[1:]
    out_dir, states = os.path.expanduser("~/Desktop"), set()
    want_demand = want_supply = True
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--out" and i + 1 < len(args):
            out_dir = os.path.expanduser(args[i + 1]); i += 2
        elif a == "--state" and i + 1 < len(args):
            states = {s.strip().upper() for s in args[i + 1].split(",")}; i += 2
        elif a == "--demand-only":
            want_supply = False; i += 1
        elif a == "--supply-only":
            want_demand = False; i += 1
        else:
            die(f"unrecognised option: {a}\n  valid: --out PATH  --state XX,YY  --demand-only  --supply-only")
    os.makedirs(out_dir, exist_ok=True)

    stamp = date.today().isoformat()
    if want_demand:
        rows, collisions = build_demand(states)
        p = free_path(out_dir, f"concrete-contractors-{stamp}")
        write(rows, p, ["email", "firstName", "lastName", "title", "company",
                        "city", "state", "workers", "crewStart", "wagePerHour"])
        april = sum(1 for r in rows if r["crewStart"][5:7] == "04")
        print(f"\n  Contractors written: {len(rows)}")
        print(f"    {april} of them start crews in April")
        if collisions:
            print(f"    {collisions} repeat filings folded into the newest one")
        print(f"    {os.path.basename(p)}")

    if want_supply:
        rows = build_supply(states)
        p = free_path(out_dir, f"bond-agents-{stamp}")
        write(rows, p, ["email", "firstName", "lastName", "agency", "city", "state", "appointedBy"])
        print(f"\n  Bond agents written: {len(rows)}")
        print(f"    {os.path.basename(p)}")

    print(f"\n  Folder: {out_dir}")
    print("\n  Saad wishes you happy connecting!\n")


if __name__ == "__main__":
    main()

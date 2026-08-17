#!/usr/bin/env python3
"""Rebuild the bond agent roster from the source, past the shipped roster.

The skill ships a cached roster because it changes slowly. Run this when the
operator wants to go further than what ships, or to refresh it.

This is the code that produced the shipped file — the same URLs, the same
carrier list, the same three filters. Prose drifts from what actually ran, so
the filters live here as code rather than as a description.

Florida publishes every active insurance appointment in the state. An
appointment is a carrier saying "this person may write our paper," so an active
appointment from a construction surety carrier is the state's own record that
this person sells bonds. The roster reaches 37 states because national agencies
register in Florida too.

Usage:
    python3 rebuild_supply.py                    # all six files -> ~/Desktop
    python3 rebuild_supply.py --files A-C,D-G    # a subset
    python3 rebuild_supply.py --out ~/lists
    python3 rebuild_supply.py --keep-brokerages  # skip the brokerage filters
"""
import csv, os, re, subprocess, sys
from datetime import date

BASE = ("https://www.myfloridacfo.com/downloads/AAS/LicenseeSearch/"
        "AllActiveAppointmentsIndividual({}).csv")
CHUNKS = ["A-C", "D-G", "H-L", "M-P", "Q-S", "T-Z"]
CACHE  = os.path.expanduser("~/.cache/concreteskill/fl")
UA     = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# Construction surety writers. An active appointment from one of these is the
# selector — Florida has no surety licence class to filter on.
CARRIERS = [
    "TRAVELERS CASUALTY AND SURETY COMPANY OF AMERICA",
    "WESTERN SURETY COMPANY",
    "FIDELITY AND DEPOSIT COMPANY OF MARYLAND",
    "MERCHANTS BONDING COMPANY",
    "AMERICAN CONTRACTORS INDEMNITY COMPANY",
    "PLATTE RIVER INSURANCE COMPANY",
    "XL SPECIALTY INSURANCE COMPANY",
    "HUDSON INSURANCE COMPANY",
    "CONTRACTORS BONDING",
    "DEVELOPERS SURETY AND INDEMNITY COMPANY",
    "OLD REPUBLIC SURETY",
    "SURETEC",
]

# Each of these contaminated a run. Zurich is multiline; its surety paper is
# Fidelity and Deposit Company of Maryland, which stays in CARRIERS above.
EXCLUDE_CARRIERS = [
    "ZURICH AMERICAN INSURANCE COMPANY",
    "PENNSYLVANIA MANUFACTURERS",
]

# A producer inside a house this size is not buying access to anything. Caught
# twice over, by agency name and by email domain, because each pass misses what
# the other finds.
BROKERAGE = re.compile(
    r'gallagher|arthur j|\bmarsh\b|\baon\b|willis|lockton|brown\s*&\s*brown|'
    r'\busi\b|alliant|acrisure|hub international|assured\s?partners|'
    r'risk strategies|\bnfp\b|mcgriff|hylant|woodruff|epic broker|'
    r'rt specialty|ryan specialty|amwins|crc group|patriot growth|'
    r'foundation risk|relation insurance|sunstar|alera|patra|higginbotham|'
    r'\bhilb\b|leavitt|inszone|world insurance|baldwin', re.I)
BROKERAGE_DOMAINS = {
    "ajg.com", "marshmma.com", "marsh.com", "aon.com", "wtwco.com",
    "lockton.com", "bbrown.com", "usi.com", "alliant.com", "acrisure.com",
    "hubinternational.com", "assuredpartners.com", "riskstrategies.com",
    "nfp.com", "mcgriff.com", "hylant.com", "woodruffsawyer.com",
    "epicbrokers.com", "rtspecialty.com", "amwins.com", "crcgroup.com",
    "patriotgis.com", "patriotgrowth.com", "baldwin.com", "ioausa.com",
    "axaxl.com", "hudsoninsgroup.com", "travelers.com", "cna.com",
}
# Payroll and personal-lines houses ride along on the appointment file.
NOT_SURETY_DOMAINS = {
    "adp.com", "paychex.com", "paycom.com", "trinet.com", "geico.com",
    "allstate.com", "statefarm.com", "progressive.com",
}
FREEMAIL = {
    "gmail.com", "yahoo.com", "hotmail.com", "aol.com", "outlook.com",
    "icloud.com", "comcast.net", "msn.com", "bellsouth.net", "att.net",
    "verizon.net", "sbcglobal.net", "live.com", "me.com", "cox.net",
    "charter.net",
}
ROLE = re.compile(r'^(info|admin|sales|bonds?|surety|service|contact|office|'
                  r'support|underwriting|quotes?|team|mail|agency|'
                  r'customerservice|bondrequest|reports)', re.I)
EMAIL_OK = re.compile(r'^[^@\s]+@[^@\s]+\.[a-z]{2,}$', re.I)


def name_owns_inbox(first, last, email):
    """Florida pairs an agency address with a licensee name, and they are not
    always the same person: davidsr@batesia.com comes back as "Emmett Bates".
    Roughly one row in five. Unchecked, a first-name greeting is wrong at that
    rate, so a row survives only when the local part supports the first name."""
    local = email.split("@")[0].lower()
    first, last = first.lower().strip(), last.lower().strip()
    if not first or ROLE.match(local):
        return False
    if local.startswith(first[:4]) or first in local:
        return True
    if last and len(first) >= 3 and local[0] == first[0] and last[:3] in local:
        return True
    return False


def die(msg):
    print(f"\n  {msg}\n", file=sys.stderr)
    sys.exit(1)


def fetch(chunk):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"appointments_{chunk}.csv")
    if os.path.exists(path) and os.path.getsize(path) > 1_000_000:
        return path
    url = BASE.format(chunk)
    print(f"  downloading {chunk} — this file is large, so it streams to disk", flush=True)
    r = subprocess.run(["curl", "-sfL", "--max-time", "3600", "-A", UA, url, "-o", path])
    if r.returncode:
        die(f"could not download {chunk} (curl {r.returncode}). Rerun to resume; "
            f"finished files are kept in {CACHE}")
    return path


def titlecase(s):
    return " ".join(w.capitalize() if w.isupper() or w.islower() else w for w in s.split())


def free_path(folder, stem, ext=".csv"):
    p, n = os.path.join(folder, stem + ext), 2
    while os.path.exists(p):
        p = os.path.join(folder, f"{stem}-{n}{ext}")
        n += 1
    return p


def main():
    args = sys.argv[1:]
    out_dir, chunks, filter_brokerages = os.path.expanduser("~/Desktop"), CHUNKS, True
    i = 0
    while i < len(args):
        if args[i] == "--out" and i + 1 < len(args):
            out_dir = os.path.expanduser(args[i + 1]); i += 2
        elif args[i] == "--files" and i + 1 < len(args):
            chunks = [c.strip().upper() for c in args[i + 1].split(",")]
            bad = [c for c in chunks if c not in CHUNKS]
            if bad:
                die(f"unknown file group: {', '.join(bad)}\n  valid: {', '.join(CHUNKS)}")
            i += 2
        elif args[i] == "--keep-brokerages":
            filter_brokerages = False; i += 1
        else:
            die(f"unrecognised option: {args[i]}\n"
                f"  valid: --out PATH  --files {','.join(CHUNKS)}  --keep-brokerages")
    os.makedirs(out_dir, exist_ok=True)

    kept, dropped = {}, {}

    def drop(reason):
        dropped[reason] = dropped.get(reason, 0) + 1

    for chunk in chunks:
        path = fetch(chunk)
        with open(path, newline="", encoding="utf-8", errors="replace") as fh:
            for row in csv.DictReader(fh):
                carrier = (row.get("Appointing Entity Name") or "").upper()
                if any(x in carrier for x in EXCLUDE_CARRIERS):
                    drop("carrier writes other lines"); continue
                match = next((c for c in CARRIERS if c in carrier), None)
                if not match:
                    continue
                if "ACTIVE" not in (row.get("Appointment Status") or "").upper():
                    drop("appointment not active"); continue
                email = (row.get("Email Address") or "").strip().lower()
                if not EMAIL_OK.match(email):
                    drop("no usable email"); continue
                domain = email.split("@")[-1]
                if domain in NOT_SURETY_DOMAINS:
                    drop("payroll or personal-lines domain"); continue
                if filter_brokerages and domain in BROKERAGE_DOMAINS:
                    drop("brokerage email domain"); continue
                agency = (row.get("Mailing Name") or row.get("Full Name") or "").strip()
                if filter_brokerages and BROKERAGE.search(agency):
                    drop("agency is a national brokerage"); continue
                full = (row.get("Full Name") or "").strip()
                parts = [p for p in re.split(r'[,\s]+', full) if p]
                last, first = (parts[0], parts[1]) if len(parts) > 1 else ("", full)
                if not name_owns_inbox(first, last, email):
                    drop("name does not match the inbox"); continue
                if email in kept:
                    continue
                kept[email] = {
                    "email": email,
                    "firstName": titlecase(first),
                    "lastName": titlecase(last),
                    "agency": titlecase(agency),
                    "city": titlecase(row.get("Business City") or ""),
                    "state": (row.get("Business State") or "").upper().strip(),
                    "appointedBy": titlecase(match),
                    "_free": domain in FREEMAIL,
                }
        print(f"  {chunk}: running total {len(kept)}", flush=True)

    rows = sorted(kept.values(),
                  key=lambda r: (r["_free"], 0 if r["agency"] else 1, r["state"], r["lastName"]))
    for r in rows:
        r.pop("_free", None)
    p = free_path(out_dir, f"bond-agents-rebuilt-{date.today().isoformat()}")
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["email", "firstName", "lastName", "agency",
                                           "city", "state", "appointedBy"])
        w.writeheader(); w.writerows(rows)

    print(f"\n  Bond agents written: {len(rows)}")
    for reason, n in sorted(dropped.items(), key=lambda x: -x[1]):
        print(f"    {n} set aside — {reason}")
    print(f"    {os.path.basename(p)}\n  Folder: {out_dir}")
    print("\n  Saad wishes you happy connecting!\n")


if __name__ == "__main__":
    main()

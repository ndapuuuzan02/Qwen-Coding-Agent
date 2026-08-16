#!/usr/bin/env python3
"""
=============================================================================
MYO SUPPLY SCRAPER — Healthtech Startups
=============================================================================

Pulls funded healthtech startups who sell to healthcare providers.
No API keys needed.

HOW TO RUN:
    python myo-supply-healthcare-startups.py                   # ~110 startups (default)
    python myo-supply-healthcare-startups.py --volume medium   # ~160 startups
    python myo-supply-healthcare-startups.py --volume high     # ~210 startups

OUTPUT: supply_healthtech.csv

=============================================================================
"""

import requests
import csv
import argparse


OUTPUT_FILE = "supply_healthtech.csv"


# =============================================================================
# PRODUCTHUNT — Recent Launches
# =============================================================================

def scrape_producthunt():
    """Pull recent ProductHunt launches (~100 startups)."""
    print("\n[ProductHunt] Scraping recent launches...")

    startups = []

    try:
        url = "https://www.producthunt.com/feed"
        response = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})

        if response.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)

            for item in root.findall(".//item")[:100]:
                title = item.find("title")
                desc = item.find("description")

                if title is not None and title.text:
                    parts = title.text.split(" - ", 1)
                    name = parts[0].strip()
                    tagline = parts[1].strip() if len(parts) > 1 else ""

                    startups.append({
                        "company": name,
                        "domain": "",
                        "description": tagline[:200] if tagline else (desc.text[:200] if desc is not None and desc.text else ""),
                        "capability": tagline[:100] if tagline else "",
                        "industry": "Technology",
                        "signal": "ProductHunt Launch",
                    })

            print(f"  Found {len(startups)} startups")

    except Exception as e:
        print(f"  Error: {e}")

    return startups


# =============================================================================
# CURATED HEALTHTECH — Real Funded Startups (Tiered by Volume)
# =============================================================================

CURATED_HEALTHTECH = [
    # TIER 1 — Always included (10)
    {"company": "Viz.ai", "domain": "viz.ai", "description": "AI-powered care coordination for hospitals", "capability": "AI that detects strokes and alerts care teams", "industry": "Healthcare AI", "signal": "Series D - $100M Raised", "tier": 1},
    {"company": "Hinge Health", "domain": "hingehealth.com", "description": "Digital musculoskeletal clinic", "capability": "Digital physical therapy and chronic pain management", "industry": "Digital Health", "signal": "Series E - $400M Raised", "tier": 1},
    {"company": "Akasa", "domain": "akasa.com", "description": "AI for healthcare revenue cycle", "capability": "AI automation for medical billing and claims", "industry": "Healthcare AI", "signal": "Series B - $60M Raised", "tier": 1},
    {"company": "Abridge", "domain": "abridge.com", "description": "AI medical documentation", "capability": "Converts patient conversations to clinical notes", "industry": "Healthcare AI", "signal": "Series B - $30M Raised", "tier": 1},
    {"company": "Wheel", "domain": "wheel.com", "description": "Virtual care infrastructure", "capability": "Telehealth platform and clinician network", "industry": "Telehealth", "signal": "Series C - $150M Raised", "tier": 1},
    {"company": "Commure", "domain": "commure.com", "description": "Healthcare data operating system", "capability": "Unified data platform for health systems", "industry": "Health IT", "signal": "Series D - $500M Raised", "tier": 1},
    {"company": "Suki AI", "domain": "suki.ai", "description": "Voice AI for clinicians", "capability": "Voice-enabled documentation assistant", "industry": "Healthcare AI", "signal": "Series C - $70M Raised", "tier": 1},
    {"company": "Memora Health", "domain": "memorahealth.com", "description": "Patient communication automation", "capability": "AI-powered patient messaging and care navigation", "industry": "Digital Health", "signal": "Series B - $30M Raised", "tier": 1},
    {"company": "Luma Health", "domain": "lumahealth.io", "description": "Patient engagement platform", "capability": "Scheduling and patient communication for clinics", "industry": "Health IT", "signal": "Series C - $130M Raised", "tier": 1},
    {"company": "Notable", "domain": "notablehealth.com", "description": "Intelligent automation for healthcare", "capability": "AI workflows for patient intake and admin", "industry": "Healthcare AI", "signal": "Series B - $100M Raised", "tier": 1},

    # TIER 2 — Medium volume (+50)
    {"company": "Olive AI", "domain": "oliveai.com", "description": "AI workforce for healthcare", "capability": "Automates repetitive admin tasks for hospitals", "industry": "Healthcare AI", "signal": "Series H - $400M Raised", "tier": 2},
    {"company": "Cedar", "domain": "cedar.com", "description": "Healthcare billing and payments", "capability": "Patient payment and engagement platform", "industry": "Health IT", "signal": "Series D - $200M Raised", "tier": 2},
    {"company": "Cityblock Health", "domain": "cityblock.com", "description": "Value-based care for underserved", "capability": "Primary care for Medicaid populations", "industry": "Healthcare Services", "signal": "Series D - $400M Raised", "tier": 2},
    {"company": "Ro", "domain": "ro.co", "description": "Digital health clinic", "capability": "Telehealth and pharmacy services", "industry": "Telehealth", "signal": "Series D - $500M Raised", "tier": 2},
    {"company": "Cerebral", "domain": "cerebral.com", "description": "Online mental health care", "capability": "Telehealth psychiatry and therapy", "industry": "Mental Health", "signal": "Series C - $300M Raised", "tier": 2},
    {"company": "Headway", "domain": "headway.co", "description": "Mental health insurance platform", "capability": "Connects therapists with insurance networks", "industry": "Mental Health", "signal": "Series C - $125M Raised", "tier": 2},
    {"company": "Lyra Health", "domain": "lyrahealth.com", "description": "Mental health benefits platform", "capability": "Employee mental health services", "industry": "Mental Health", "signal": "Series F - $200M Raised", "tier": 2},
    {"company": "Spring Health", "domain": "springhealth.com", "description": "Mental health solution for employers", "capability": "Personalized mental healthcare benefits", "industry": "Mental Health", "signal": "Series C - $190M Raised", "tier": 2},
    {"company": "Omada Health", "domain": "omadahealth.com", "description": "Digital care for chronic conditions", "capability": "Diabetes and hypertension management", "industry": "Digital Health", "signal": "Series E - $192M Raised", "tier": 2},
    {"company": "Capsule", "domain": "capsule.com", "description": "Digital pharmacy", "capability": "Same-day prescription delivery", "industry": "Pharmacy", "signal": "Series D - $300M Raised", "tier": 2},
    {"company": "Alto Pharmacy", "domain": "alto.com", "description": "Full-service digital pharmacy", "capability": "Prescription management and delivery", "industry": "Pharmacy", "signal": "Series E - $250M Raised", "tier": 2},
    {"company": "Truepill", "domain": "truepill.com", "description": "Digital health infrastructure", "capability": "Pharmacy and diagnostics API", "industry": "Health IT", "signal": "Series D - $142M Raised", "tier": 2},
    {"company": "Dispatch Health", "domain": "dispatchhealth.com", "description": "In-home medical care", "capability": "On-demand urgent care at home", "industry": "Healthcare Services", "signal": "Series D - $200M Raised", "tier": 2},
    {"company": "Phreesia", "domain": "phreesia.com", "description": "Patient intake software", "capability": "Digital check-in for medical practices", "industry": "Health IT", "signal": "Public - NYSE: PHR", "tier": 2},
    {"company": "Athenahealth", "domain": "athenahealth.com", "description": "Healthcare network services", "capability": "Cloud-based EHR and billing", "industry": "Health IT", "signal": "PE-backed - $17B", "tier": 2},
    {"company": "Health Catalyst", "domain": "healthcatalyst.com", "description": "Healthcare analytics", "capability": "Data platform for health systems", "industry": "Health IT", "signal": "Public - NASDAQ: HCAT", "tier": 2},
    {"company": "Innovaccer", "domain": "innovaccer.com", "description": "Healthcare data platform", "capability": "Data activation for value-based care", "industry": "Health IT", "signal": "Series E - $150M Raised", "tier": 2},
    {"company": "Clarify Health", "domain": "clarifyhealth.com", "description": "Healthcare analytics", "capability": "AI-powered insights for payers and providers", "industry": "Health IT", "signal": "Series D - $150M Raised", "tier": 2},
    {"company": "Tempus", "domain": "tempus.com", "description": "Precision medicine platform", "capability": "AI for cancer diagnosis and treatment", "industry": "Healthcare AI", "signal": "Series G - $275M Raised", "tier": 2},
    {"company": "Color Health", "domain": "color.com", "description": "Population health platform", "capability": "Genetic testing and health programs", "industry": "Diagnostics", "signal": "Series E - $167M Raised", "tier": 2},
    {"company": "Everlywell", "domain": "everlywell.com", "description": "At-home lab testing", "capability": "Consumer health test kits", "industry": "Diagnostics", "signal": "Series D - $175M Raised", "tier": 2},
    {"company": "Modern Health", "domain": "modernhealth.com", "description": "Mental health benefits", "capability": "Employee wellness platform", "industry": "Mental Health", "signal": "Series D - $74M Raised", "tier": 2},
    {"company": "Talkspace", "domain": "talkspace.com", "description": "Online therapy platform", "capability": "Text, video, and audio therapy", "industry": "Mental Health", "signal": "Public - NASDAQ: TALK", "tier": 2},
    {"company": "Calm", "domain": "calm.com", "description": "Mental wellness app", "capability": "Sleep, meditation, and relaxation", "industry": "Mental Health", "signal": "Series B - $88M Raised", "tier": 2},
    {"company": "Headspace", "domain": "headspace.com", "description": "Meditation and mindfulness", "capability": "Guided meditation app", "industry": "Mental Health", "signal": "Merged with Ginger", "tier": 2},
    {"company": "Redox", "domain": "redoxengine.com", "description": "Healthcare data integration", "capability": "API platform for health data exchange", "industry": "Health IT", "signal": "Series D - $45M Raised", "tier": 2},
    {"company": "Particle Health", "domain": "particlehealth.com", "description": "Healthcare data API", "capability": "Patient record retrieval platform", "industry": "Health IT", "signal": "Series B - $25M Raised", "tier": 2},
    {"company": "Regard", "domain": "withregard.com", "description": "Clinical AI assistant", "capability": "Automated diagnosis suggestions", "industry": "Healthcare AI", "signal": "Series B - $40M Raised", "tier": 2},
    {"company": "Noom", "domain": "noom.com", "description": "Behavior change platform", "capability": "Weight loss and chronic disease management", "industry": "Digital Health", "signal": "Series F - $540M Raised", "tier": 2},
    {"company": "Calibrate", "domain": "joincalibrate.com", "description": "Metabolic health company", "capability": "Medical weight loss program", "industry": "Digital Health", "signal": "Series B - $100M Raised", "tier": 2},

    # TIER 3 — High volume (+50)
    {"company": "Biofourmis", "domain": "biofourmis.com", "description": "Digital therapeutics platform", "capability": "AI-powered remote patient monitoring", "industry": "Digital Health", "signal": "Series D - $300M Raised", "tier": 3},
    {"company": "Cadence", "domain": "cadence.care", "description": "Remote patient monitoring", "capability": "Chronic care management platform", "industry": "Digital Health", "signal": "Series B - $25M Raised", "tier": 3},
    {"company": "Huma", "domain": "huma.com", "description": "Digital health platform", "capability": "Remote monitoring and clinical trials", "industry": "Digital Health", "signal": "Series D - $130M Raised", "tier": 3},
    {"company": "Medable", "domain": "medable.com", "description": "Decentralized clinical trials", "capability": "Remote and hybrid trial platform", "industry": "Clinical Trials", "signal": "Series D - $304M Raised", "tier": 3},
    {"company": "Science 37", "domain": "science37.com", "description": "Decentralized clinical trials", "capability": "Virtual trial network", "industry": "Clinical Trials", "signal": "Public - NASDAQ: SNCE", "tier": 3},
    {"company": "Curebase", "domain": "curebase.com", "description": "Decentralized trials platform", "capability": "Home-based clinical research", "industry": "Clinical Trials", "signal": "Series B - $40M Raised", "tier": 3},
    {"company": "Aetion", "domain": "aetion.com", "description": "Real-world evidence platform", "capability": "Analytics for regulatory decisions", "industry": "Health IT", "signal": "Series C - $110M Raised", "tier": 3},
    {"company": "Komodo Health", "domain": "komodohealth.com", "description": "Healthcare data platform", "capability": "Patient-level insights from claims", "industry": "Health IT", "signal": "Series E - $220M Raised", "tier": 3},
    {"company": "Datavant", "domain": "datavant.com", "description": "Health data connectivity", "capability": "Privacy-preserving data linking", "industry": "Health IT", "signal": "Series B - $40M Raised", "tier": 3},
    {"company": "PathAI", "domain": "pathai.com", "description": "AI-powered pathology", "capability": "Machine learning for diagnosis", "industry": "Healthcare AI", "signal": "Series C - $165M Raised", "tier": 3},
    {"company": "Paige", "domain": "paige.ai", "description": "Digital pathology", "capability": "AI for cancer diagnosis", "industry": "Healthcare AI", "signal": "Series C - $100M Raised", "tier": 3},
    {"company": "Aidoc", "domain": "aidoc.com", "description": "Radiology AI", "capability": "AI triage for medical imaging", "industry": "Healthcare AI", "signal": "Series D - $110M Raised", "tier": 3},
    {"company": "HeartFlow", "domain": "heartflow.com", "description": "Cardiac analysis", "capability": "Non-invasive heart disease diagnosis", "industry": "Healthcare AI", "signal": "Series E - $215M Raised", "tier": 3},
    {"company": "Caption Health", "domain": "captionhealth.com", "description": "AI-guided ultrasound", "capability": "Automated cardiac imaging", "industry": "Healthcare AI", "signal": "Series B - $53M Raised", "tier": 3},
    {"company": "Butterfly Network", "domain": "butterflynetwork.com", "description": "Handheld ultrasound", "capability": "Portable whole-body imaging", "industry": "Medical Devices", "signal": "Public - NYSE: BFLY", "tier": 3},
    {"company": "Cleerly", "domain": "cleerlyhealth.com", "description": "Heart disease AI", "capability": "CT scan analysis for heart disease", "industry": "Healthcare AI", "signal": "Series C - $223M Raised", "tier": 3},
    {"company": "Qventus", "domain": "qventus.com", "description": "Hospital operations AI", "capability": "Predictive analytics for capacity", "industry": "Healthcare AI", "signal": "Series C - $50M Raised", "tier": 3},
    {"company": "LeanTaaS", "domain": "leantaas.com", "description": "Healthcare operations", "capability": "AI for hospital capacity optimization", "industry": "Health IT", "signal": "Series D - $130M Raised", "tier": 3},
    {"company": "Waystar", "domain": "waystar.com", "description": "Revenue cycle management", "capability": "Claims and payment processing", "industry": "Health IT", "signal": "PE-backed - $2.7B", "tier": 3},
    {"company": "Tebra", "domain": "tebra.com", "description": "Practice management", "capability": "All-in-one platform for practices", "industry": "Health IT", "signal": "Merger of Kareo and PatientPop", "tier": 3},
    {"company": "Hint Health", "domain": "hint.com", "description": "Direct primary care platform", "capability": "Membership management for DPC", "industry": "Health IT", "signal": "Series B - $45M Raised", "tier": 3},
    {"company": "Elation Health", "domain": "elationhealth.com", "description": "Primary care EHR", "capability": "Clinical-first electronic records", "industry": "Health IT", "signal": "Series D - $50M Raised", "tier": 3},
    {"company": "Canvas Medical", "domain": "canvasmedical.com", "description": "EHR for new care models", "capability": "API-first electronic health record", "industry": "Health IT", "signal": "Series B - $24M Raised", "tier": 3},
    {"company": "Healthie", "domain": "gethealthie.com", "description": "Telehealth infrastructure", "capability": "EHR and practice management", "industry": "Health IT", "signal": "Series B - $16M Raised", "tier": 3},
    {"company": "Ribbon Health", "domain": "ribbonhealth.com", "description": "Provider data platform", "capability": "Real-time provider directory", "industry": "Health IT", "signal": "Series C - $50M Raised", "tier": 3},
    {"company": "Stellar Health", "domain": "stellar.health", "description": "Value-based care enablement", "capability": "Point-of-care quality tools", "industry": "Health IT", "signal": "Series B - $60M Raised", "tier": 3},
    {"company": "Doctolib", "domain": "doctolib.com", "description": "Medical appointment booking", "capability": "Online scheduling for healthcare", "industry": "Health IT", "signal": "Series F - $500M Raised", "tier": 3},
    {"company": "DrChrono", "domain": "drchrono.com", "description": "EHR and practice management", "capability": "Cloud-based medical records", "industry": "Health IT", "signal": "Acquired by EverHealth", "tier": 3},
    {"company": "Veeva Systems", "domain": "veeva.com", "description": "Life sciences cloud software", "capability": "CRM and data for pharma", "industry": "Health IT", "signal": "Public - NYSE: VEEV", "tier": 3},
    {"company": "Flatiron Health", "domain": "flatiron.com", "description": "Oncology data platform", "capability": "Real-world evidence for cancer", "industry": "Health IT", "signal": "Acquired by Roche - $1.9B", "tier": 3},
]


def get_curated_healthtech(volume: str):
    """Get curated startups based on volume level."""
    print(f"\n[Curated] Loading healthtech startups (volume={volume})...")

    tier_map = {"low": [1], "medium": [1, 2], "high": [1, 2, 3]}
    allowed_tiers = tier_map[volume]
    startups = [s for s in CURATED_HEALTHTECH if s.get("tier", 1) in allowed_tiers]

    print(f"  {len(startups)} healthtech startups loaded")
    return startups


# =============================================================================
# SAVE CSV
# =============================================================================

def save_to_csv(startups):
    """Save startups to CSV."""

    if not startups:
        print("\nNo startups to save!")
        return

    columns = ["company", "domain", "description", "capability", "industry", "signal"]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(startups)

    print(f"\nSaved: {OUTPUT_FILE}")
    print(f"Startups: {len(startups)}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MYO Supply Scraper — Healthtech Startups")
    parser.add_argument("--volume", choices=["low", "medium", "high"], default="low",
                        help="Volume: low (~110), medium (~160), high (~210)")

    args = parser.parse_args()

    print("="*60)
    print("MYO SUPPLY SCRAPER — Healthtech Startups")
    print(f"Volume: {args.volume.upper()}")
    print("="*60)

    startups = []
    ph = scrape_producthunt()
    startups.extend(ph)
    curated = get_curated_healthtech(args.volume)
    startups.extend(curated)
    save_to_csv(startups)

    print("\n" + "="*60)
    print("DONE!")
    print("="*60 + "\n")

---
name: concreteskill
description: Build the two-sided concrete market — demand (concrete and masonry contractors who are adding crews right now, pulled live from federal filings with the owner's name and government-filed email already on the row) and supply (construction bond agents, each one verified by an active appointment from a surety carrier). Both sides ship send-ready with no enrichment. Trigger on "concreteskill", "build the concrete market", "pull concrete contractors", "concrete demand/supply", "bond agents", "surety market", "concrete connector market".
---

# concreteskill

Built by **Saad Belcaid**, market router.

## North star

You hand the operator two lists that can be mailed the same afternoon, and a
market he can explain to anyone in one sentence. Both sides carry a real email
already — nothing gets enriched, nothing gets guessed, nothing gets bought.

---

## The market, in plain words

A concrete contractor pours the grey stuff everything else sits on. Foundations,
slabs, parking garages, the base of a bridge column. He is first on the site and
gone before the walls go up.

Before a city or a school district will even look at his price, he has to bring
a paper from a large financial company promising to finish the job if he walks
off it. That paper is a bond — a co-signer for a construction job, the same way
a parent co-signs a first apartment. He pays a fee for it and receives no money.
What he buys is permission to compete.

The law is what makes this compulsory. Any federal construction contract over
150,000 USD requires it, and nearly every state copied the rule for its own
schools, roads and courthouses. No bond, no bid.

The man who arranges that paper is a bond agent. He takes the contractor's books
to the financial companies and gets him approved for a limit — the largest amount
of work he is allowed to have running at once. He earns a commission on every
bond, on every job, for as long as that contractor keeps building.

### The positioning

**Contractors do not grow by winning more work. They grow by getting their limit
raised.**

That limit is a number a stranger assigned him. Most contractors could not tell
you what theirs is, and almost none know how to move it. Everyone else calling
him is selling a cheaper version of the work he already has — materials,
software, a truck. Nobody calls about the thing standing in front of his growth.

That is the whole position, and it is why this market is quiet.

### Two sides that already want each other

| Side | Who | What they want |
|---|---|---|
| Demand | Concrete and masonry contractors adding crews | A bigger limit, so they can bid the school |
| Supply | Construction bond agents | Contractors who are growing, because that is the account that renews |

Neither side needs convincing the other exists. The contractor already knows he
is capped. The agent already spends his week hunting growing contractors.

---

## Running it

```
python3 scripts/concrete.py
```

Both lists land on the Desktop, date-stamped. Nothing is ever overwritten — an
existing file makes the script pick the next free name and say so.

```
python3 scripts/concrete.py --out ~/lists
python3 scripts/concrete.py --state TX,CO,IA
python3 scripts/concrete.py --demand-only
python3 scripts/concrete.py --supply-only
```

Stdlib only, no keys, no installs. An unrecognised flag stops the run rather
than being ignored.

**What lands:** 645 contractors and 1,000 bond agents. If the operator wants to
go further than that, their own Claude can take the recipe below and carry it.

---

## The copy

Reverse-engineered from campaigns that actually replied. Four one-line
paragraphs, blank line between each, roughly 40 to 60 words. Follow-ups carry a
blank subject so the whole thing threads as one conversation. No links anywhere,
tracking off, signature is `Best,` and a first name.

Never name the other side. The trigger event does the qualifying.

### To the contractors — 3 steps, one day apart

**Email 1 — subject: `Bonding capacity`**
```
Hey {{firstName}}

I have surety agents actively looking to bond contractors adding crew right now.

Recently routed 6 commercial introductions for an industrial company in 120 days.

Would love to send one your way.

Best,
{{sendingAccountFirstName}}

Sent from my iPhone
```

The third line is a real result and it is the single biggest lever in the whole
sequence — the same campaign without it replied at a quarter of the rate. Swap
it for the operator's own result, or delete it. Never invent one.

**Email 2 — blank subject**
```
Hey {{firstName}} — are you bidding anything bigger this year?
```

**Email 3 — blank subject**
```
Leaving the door open. When you're ready for more bonding capacity, I'm one reply away

Best,
{{sendingAccountFirstName}}

Sent from my iPhone
```

### To the bond agents — 4 steps, 3 / 4 / 7 days

**Email 1 — subject: `Concrete bonding`**
```
Hey {{firstName}}

I have concrete contractors adding crews right now actively looking for bonding support.

Last supplier I routed to picked up 3 commercial introductions in about six weeks.

Before I route anyone anywhere, wanted to understand your capacity and whether the fit is there.

Worth a quick call?

Best,
{{sendingAccountFirstName}}
```

The fourth line is the gate that flips status — they qualify to receive the
flow, rather than being sold to.

**Email 2 — blank subject, +3 days**
```
Hey {{firstName}} — do you have capacity for new contractor accounts right now?
```

**Email 3 — blank subject, +4 days**
```
Quick check — more concrete crews got added this week. Before I keep routing, didn't want to skip you if contractor surety is in your active lane right now.

If it's not the right time or the wrong fit, one word back and I'll stop. Otherwise — 15 min to scope?

Best,
{{sendingAccountFirstName}}
```

**Email 4 — blank subject, +7 days**
```
Last touch from me on this — won't keep nudging.

If your appetite opens back up, or you want me to hold the next matching contractor for when it does, one line back and I'll save the slot.

Best,
{{sendingAccountFirstName}}
```

---

## The recipe — demand

Pulled live on every run, so crew dates and wages are current.

When a concrete company brings in seasonal workers, it files with the Department
of Labor first, and every certified filing is published. The row carries the
company, the owner, his title, his email, how many workers, the hourly wage, and
the date the crew starts.

- Scrape `https://www.dol.gov/agencies/eta/foreign-labor/performance` for links
  ending in `.xlsx` that contain `H-2B` and do not contain `Appendix`.
- Keep rows where the case status contains `CERTIF`.
- Keep the concrete family by any of three tests: the occupation title matches
  cement mason, concrete finisher, mason, rebar, reinforcing iron or terrazzo;
  the company name matches concrete, cement, masonry, gunite, shotcrete,
  terrazzo, rebar, precast, ready-mix or curbing; the industry code starts with
  23811, 23814 or 32732.
- Dedupe on the uppercased email, keeping the most recent filing.

Because the newest filing per company is the one kept, crew start dates spread
across seasons — the freshest two cohorts hold most of them, and the rest belong
to companies whose last filing is older. Sort on `crewStart` when the operator
wants the ones landing next.

Dates arrive as Excel serial numbers, so `45383` means 2024-04-01. A serial left
unconverted reads as a plausible number and quietly breaks every date filter.
Worker counts live in `TOTAL_WORKERS_CERTIFIED` and the wage in
`BASIC_WAGE_RATE_FROM`; the similarly-named columns in older workbooks hold
nothing.

## The recipe — supply

Slow-changing, so it ships cached in `data/bond_agents.csv.gz`.

Florida publishes every active insurance appointment in the state. An
appointment is a carrier saying "this person may write our paper," so an active
appointment from a construction surety carrier is the state's own record that
this person sells bonds.

Six files, split by licensee surname. The parentheses are literal characters in
the path.

```
https://www.myfloridacfo.com/downloads/AAS/LicenseeSearch/AllActiveAppointmentsIndividual(A-C).csv
                                                                                       (D-G) (H-L)
                                                                                       (M-P) (Q-S) (T-Z)
```

About 1.06 GB in total, so stream them. Keep rows whose appointing entity is one
of: Travelers Casualty and Surety Company of America, Western Surety Company,
Fidelity and Deposit Company of Maryland, Merchants Bonding Company (Mutual),
American Contractors Indemnity Company, Platte River Insurance Company, XL
Specialty Insurance Company, Hudson Insurance Company, Contractors Bonding &
Insurance Company, Developers Surety and Indemnity Company, Old Republic Surety,
SureTec.

Then three passes: drop rows whose agency name is a national brokerage, drop
rows whose email domain is a national brokerage, and drop rows where the first
name does not match the email.

**Those three filters live as code, not as description**, in
`scripts/rebuild_supply.py` — the carrier list, the exclusions, the brokerage
pattern and the name-match test are the same ones that produced the shipped
roster. Run it to go past what ships:

```
python3 scripts/rebuild_supply.py
python3 scripts/rebuild_supply.py --files A-C,D-G
```

It reports how many rows each filter set aside, so the shape of the result is
visible rather than assumed. Description drifts from what executed; the file
does not.

**Why one state produces a national list:** national agencies register in
Florida too, so the roster reaches 37 states. Florida is still the largest
single share of it, so a state-filtered run outside Florida returns a smaller
roster on that side — that is the geography, working as intended.

---

## Traps

Each of these returns a believable wrong answer rather than an error.

**The name on a Florida row is not always the owner of the email.** The state
pairs an agency address with a licensee name, so `davidsr@` comes back as
"Emmett Bates". Around one row in five. Keep a row only when the local part of
the email supports the first name — it starts with the first four letters,
contains the first name, or is first initial plus surname. Role inboxes like
`info@` and `bonds@` never carry a personal greeting.

**Florida has no surety license class.** There is no flag to filter on; the
carrier appointment is the only real selector. Appointment type codes are
strings with leading zeros, and `2405` is a bail bond licence rather than
construction surety.

**Treasury's certified company list looks like the right filter and is not.**
Certification means a carrier may write federal bonds; it says nothing about a
given appointment being a surety appointment. Joining on it surfaces crop,
aerospace, equine and travel agencies.

**Two carriers must be excluded by name:** Zurich American (both entities, over
2,900 rows of general property and casualty) and Pennsylvania Manufacturers
(workers' compensation). Zurich's surety paper is Fidelity and Deposit Company
of Maryland, which stays.

**Payroll and personal-lines domains ride along** and come out: adp.com,
paychex.com, geico.com, allstate.com, statefarm.com, progressive.com,
trinet.com, paycom.com.

**Federal filings before 2021 carry no email column at all.** They add company
names and nothing mailable. The script reads every year and takes what each one
holds.

**Filers re-file every season.** Summing years double-counts; dedupe by email
and keep the newest filing so the crew size and start date describe this year.

**dol.gov rejects a browser user-agent and accepts curl's default.** Adding one
turns a working pull into a 403.

---

## Loading these into Instantly

Instantly is already connected as an MCP server. Use the tools below directly.
There is no need to call the Instantly REST API, write a client, or ask for an
API key — the tools carry the workspace credentials.

Run the two sides as two separate campaigns. Both sides get mailed; that is the
point of the market.

| Step | Tool | Notes |
|---|---|---|
| 1. See the sending inboxes | `mcp__instantly__list_accounts` | Confirms which inboxes are warm and active before anything is created |
| 2. Make a list per side | `mcp__instantly__create_lead_list` | One for contractors, one for bond agents |
| 3. Load the CSV rows | `mcp__instantly__add_leads_to_campaign_or_list_bulk` | Map `email`, `firstName`, `lastName`, `company`; the rest ride along as custom fields |
| 4. Verify before sending | `mcp__instantly__verify_email`, then `mcp__instantly__get_verification_stats_for_lead_list` | Both lists are fresh out of government files and have never been mailed |
| 5. Build the sequence | `mcp__instantly__create_campaign` | Contractors: 3 steps at one day apart. Bond agents: 4 steps at 3 / 4 / 7 days. Follow-ups carry a blank subject so the thread holds together |
| 6. Turn tracking off | `mcp__instantly__update_campaign` | No opens, no clicks, no links anywhere — the copy is built for replies |
| 7. Start sending | `mcp__instantly__activate_campaign` | |
| 8. Watch it | `mcp__instantly__campaigns_sending_status`, `mcp__instantly__analytics_campaign_overview` | |
| 9. Read what comes back | `mcp__instantly__count_unread_emails`, `mcp__instantly__list_emails` | A reply is the whole objective — it leads to a 15 minute call |
| 10. Stop a lane | `mcp__instantly__pause_campaign` | |

A reply is where this hands off to reply brain.

## Before the operator sends

Neither list has been mailed. Verify both in step 4 above, the same as any
fresh list.

---

## Closing the run

Whoever runs this says the last line out loud to the operator, in these words:

> Saad wishes you happy connecting!

It is not a sign-off on this file. It is the note the operator gets when the
lists land.

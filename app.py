import requests
from bs4 import BeautifulSoup
import json
import os
import anthropic

# -------- SETTINGS -------- #

TARGET_LOCATIONS = [
    "houston", "cypress", "magnolia",
    "the woodlands", "spring", "tomball"
]

KEYWORDS = ["teller", "banker", "relationship", "associate"]

EXCLUDE_DEGREES = [
    "finance degree", "accounting degree",
    "mba", "bba", "bachelor in finance"
]

TRACK_FILE = "applications.json"


# -------- UTIL FUNCTIONS -------- #

def matches_filters(text):
    text = text.lower()
    return (
        any(loc in text for loc in TARGET_LOCATIONS) and
        any(role in text for role in KEYWORDS)
    )


def exclude_degree(text):
    return any(bad in text for bad in EXCLUDE_DEGREES)


# -------- SCORING -------- #

def score_job(title):
    text = title.lower()
    score = 0

    if any(role in text for role in KEYWORDS):
        score += 3

    if any(loc in text for loc in TARGET_LOCATIONS):
        score += 3

    if "bilingual" in text or "spanish" in text:
        score += 2

    if "sales" in text or "customer" in text:
        score += 2

    if exclude_degree(text):
        score -= 5

    return score


# -------- WOODFOREST SCRAPER -------- #

def search_woodforest():
    url = "https://woodforest.taleo.net/careersection/2/jobsearch.ftl?lang=en"

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    jobs = []

    for link in soup.find_all("a"):
        title = link.get_text().strip()

        if not title:
            continue

        if not any(role in title.lower() for role in KEYWORDS):
            continue

        href = link.get("href")

        if href and not href.startswith("http"):
            href = "https://woodforest.taleo.net" + href

        jobs.append({
            "company": "Woodforest National Bank",
            "title": title,
            "location": "Check posting",
            "link": href,
            "score": score_job(title)
        })

    return jobs


# -------- HIGH PRIORITY SOURCES -------- #

def static_sources():
    return [
        {
            "company": "First Convenience Bank",
            "title": "Teller / Banker Roles",
            "location": "Houston Area",
            "link": "https://myjobs.adp.com/fnbtandfcbcareers/cx",
            "score": 9
        },
        {
            "company": "Woodforest National Bank",
            "title": "Branch Banking Roles",
            "location": "Houston Area",
            "link": "https://woodforest.taleo.net",
            "score": 8
        },
        {
            "company": "PNC",
            "title": "Regional Banker / Teller",
            "location": "Houston Area",
            "link": "https://careers.pnc.com",
            "score": 7
        },
        {
            "company": "Prosperity Bank",
            "title": "Retail Banking Roles",
            "location": "Texas",
            "link": "https://workforcenow.adp.com",
            "score": 7
        },
        {
            "company": "Bank of America",
            "title": "Financial Center Roles",
            "location": "Houston Area",
            "link": "https://careers.bankofamerica.com",
            "score": 6
        },
        {
            "company": "Wells Fargo",
            "title": "Banking Roles",
            "location": "Houston Area",
            "link": "https://www.wellsfargojobs.com",
            "score": 6
        },
        {
            "company": "JPMorgan Chase",
            "title": "Branch Banking Roles",
            "location": "Houston Area",
            "link": "https://jpmc.fa.oraclecloud.com",
            "score": 6
        }
    ]


# -------- AI JOB ANALYSIS -------- #

def analyze_job(job):
    client = anthropic.Anthropic()

    prompt = f"""Analyze this job for Frida Peralta and tell her in 3-4 sentences whether it is a strong fit.

Job: {job['title']} at {job['company']} ({job['location']})

Frida's background: Bilingual (EN/ES), B.A. Sociology & Pre-Health from UT Austin. Experience in healthcare (clinical assistant, EMR systems), education (bilingual teacher, Power BI dashboards), and project analytics (Dell Medical School). Skills: Power BI, Excel, Python, SPSS. Target: analytical or customer-facing roles in banking, healthcare, or education. No finance or accounting degree.

What is the strongest selling point she should lead with for this specific role?"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


# -------- TRACKING SYSTEM -------- #

def load_tracking():
    if not os.path.exists(TRACK_FILE):
        return []
    with open(TRACK_FILE, "r") as f:
        return json.load(f)


def save_tracking(data):
    with open(TRACK_FILE, "w") as f:
        json.dump(data, f, indent=2)


def mark_applied(job, tracking):
    tracking.append(job)
    save_tracking(tracking)
    print("✅ Marked as applied.")


# -------- MAIN ENGINE -------- #

def main():
    jobs = []

    print("\n🔍 Pulling live jobs...")
    jobs += search_woodforest()

    print("🔍 Adding priority banks...")
    jobs += static_sources()

    jobs = sorted(jobs, key=lambda x: x["score"], reverse=True)

    tracking = load_tracking()

    print("\n=== ELITE JOB DASHBOARD ===\n")

    for i, job in enumerate(jobs):
        print(f"{i+1}. 🔥 Score: {job['score']}")
        print(f"   Company: {job['company']}")
        print(f"   Role: {job['title']}")
        print(f"   Location: {job['location']}")
        print(f"   Link: {job['link']}")
        print("------")

    # -------- USER ACTION -------- #
    choice = input(
        "\nEnter job number to mark as applied, 'a#' to analyze with AI (e.g. a2), or Enter to skip: ")

    if choice.lower().startswith("a") and choice[1:].isdigit():
        idx = int(choice[1:]) - 1
        if 0 <= idx < len(jobs):
            print("\n--- AI Analysis ---")
            print(analyze_job(jobs[idx]))
            print("-------------------")
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(jobs):
            mark_applied(jobs[idx], tracking)


if __name__ == "__main__":
    main()

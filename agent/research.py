import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


def fetch_url_text(url, timeout=8):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # get visible paragraphs
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
        return "\n\n".join(paragraphs)[:20000]
    except Exception:
        return ""


def search_duckduckgo(query, max_results=5):
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        links = []
        for a in soup.select('a.result__a')[:max_results]:
            href = a.get('href')
            if href:
                links.append(href)
        # fallback for different HTML structure
        if not links:
            for a in soup.select('a')[:max_results*2]:
                href = a.get('href')
                if href and href.startswith('http'):
                    links.append(href)
        return links[:max_results]
    except Exception:
        return []


def fetch_wikipedia(company_name):
    name = company_name.strip().replace(' ', '_')
    url = f"https://en.wikipedia.org/wiki/{quote_plus(name)}"
    text = fetch_url_text(url)
    if text:
        return {"source": url, "text": text}
    # fallback: search
    links = search_duckduckgo(company_name + ' wikipedia')
    for link in links:
        if 'wikipedia.org' in link:
            text = fetch_url_text(link)
            if text:
                return {"source": link, "text": text}
    return None


def extract_facts(text):
    facts = {}
    # revenue pattern like $1,234,000 or $1.2 billion
    revenue_matches = re.findall(r"\$[\d\.,]+(?:\s*billion|\s*million|\s*bn|\s*m)?", text, flags=re.I)
    if revenue_matches:
        facts['revenue_candidates'] = list(dict.fromkeys(revenue_matches))
    # employees patterns
    emp_matches = re.findall(r"([\d,]{3,})\s+employees", text, flags=re.I)
    if emp_matches:
        facts['employees_candidates'] = list(dict.fromkeys(emp_matches))
    # HQ
    hq = None
    m = re.search(r"Headquarters\:?[\s\-–]*([A-Za-z0-9,\s]+)\n", text)
    if m:
        hq = m.group(1).strip()
    if not hq:
        m2 = re.search(r"Headquartered in ([A-Za-z0-9,\s]+)[\.,]", text)
        if m2:
            hq = m2.group(1).strip()
    if hq:
        facts['headquarters'] = hq
    return facts


def synthesize_sources(sources):
    # sources: list of dict {source, text}
    combined = []
    facts_agg = {"revenue": [], "employees": [], "headquarters": []}
    for s in sources:
        t = s.get('text','')
        combined.append(t[:2000])
        f = extract_facts(t)
        for k,v in f.items():
            if k == 'revenue_candidates':
                facts_agg['revenue'].extend(v)
            if k == 'employees_candidates':
                facts_agg['employees'].extend(v)
            if k == 'headquarters':
                facts_agg['headquarters'].append(v)

    # dedupe
    for k in facts_agg:
        facts_agg[k] = list(dict.fromkeys(facts_agg[k]))

    overview = '\n\n'.join(combined[:3])

    # build simple account plan
    plan = {
        'Overview': overview[:4000] or 'No overview available.',
        'Financials': '',
        'Opportunities': '',
        'Risks': '',
        'Strategy': '',
    }

    # Financials
    fin_lines = []
    if facts_agg['revenue']:
        fin_lines.append('Revenue candidates: ' + '; '.join(facts_agg['revenue']))
    if facts_agg['employees']:
        fin_lines.append('Employee counts found: ' + '; '.join(facts_agg['employees']))
    if facts_agg['headquarters']:
        fin_lines.append('Headquarters candidates: ' + '; '.join(facts_agg['headquarters']))
    plan['Financials'] = '\n'.join(fin_lines) if fin_lines else 'No financial data found.'

    # lightweight opportunities/risk heuristics
    if 'acqui' in overview.lower() or 'partnership' in overview.lower():
        plan['Opportunities'] = 'Potential M&A/partnership signals in recent coverage.'
    else:
        plan['Opportunities'] = 'Opportunity: Engage on product integration and GTM.'

    if 'layoff' in overview.lower() or 'lawsuit' in overview.lower():
        plan['Risks'] = 'Detected potential risks: layoffs or legal issues in recent reports.'
    else:
        plan['Risks'] = 'Low immediate risk signals from scraped text.'

    plan['Strategy'] = 'Intro deck -> discovery -> pilot -> expansion. Tailor by product fit.'

    # conflict detection
    conflicts = []
    if len(facts_agg['revenue']) > 1:
        conflicts.append('Multiple revenue figures found: ' + '; '.join(facts_agg['revenue']))
    if len(facts_agg['employees']) > 1:
        conflicts.append('Multiple employee counts found: ' + '; '.join(facts_agg['employees']))

    return plan, conflicts


def research_company(company_name, max_search=5):
    sources = []
    wiki = fetch_wikipedia(company_name)
    if wiki:
        sources.append(wiki)

    # search other pages
    links = search_duckduckgo(company_name + ' company', max_results=max_search)
    for link in links:
        if any(domain in link for domain in ['linkedin.com', 'facebook.com', 'twitter.com']):
            continue
        text = fetch_url_text(link)
        if text:
            sources.append({'source': link, 'text': text})

    plan, conflicts = synthesize_sources(sources)
    return {
        'company': company_name,
        'plan': plan,
        'conflicts': conflicts,
        'sources': [s['source'] for s in sources[:6]]
    }

from agency_swarm.tools import BaseTool
from pydantic import Field
import os
import json
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus

load_dotenv()

class CompanyResearchTool(BaseTool):
    """
    Gathers and synthesizes company information from multiple free sources (Wikipedia, NewsAPI, DuckDuckGo, Bing Search, Google News RSS, company website meta tags).
    Uses an LLM (Claude or OpenAI) to generate a 500-word, natural language summary for sales preparation, broken into key areas.
    """
    company_name: str = Field(
        ..., description="Name of the company to research"
    )
    
    def _get_wikipedia_data(self) -> Dict:
        """Fetch company data from Wikipedia API"""
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={self.company_name}&format=json"
        response = requests.get(search_url)
        response.raise_for_status()
        search_data = response.json()
        if not search_data["query"]["search"]:
            return {}
        page_id = search_data["query"]["search"][0]["pageid"]
        content_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&pageids={page_id}&format=json&exintro=1"
        response = requests.get(content_url)
        response.raise_for_status()
        content_data = response.json()
        return {
            "title": content_data["query"]["pages"][str(page_id)]["title"],
            "extract": content_data["query"]["pages"][str(page_id)]["extract"]
        }

    def _get_newsapi_data(self) -> List[Dict]:
        """Fetch recent news about the company using NewsAPI (if key present)"""
        api_key = os.getenv("NEWS_API_KEY")
        if not api_key:
            return []
        news_url = f"https://newsapi.org/v2/everything?q={self.company_name}&apiKey={api_key}&language=en&sortBy=publishedAt&pageSize=5"
        response = requests.get(news_url)
        response.raise_for_status()
        news_data = response.json()
        return news_data.get("articles", [])

    def _get_google_news_rss(self) -> List[Dict]:
        """Fetch recent news using Google News RSS (no API key required)"""
        try:
            encoded_query = quote_plus(self.company_name)
            news_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            response = requests.get(news_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'xml')
            news_items = []
            for item in soup.find_all('item')[:10]:
                news_items.append({
                    'title': item.title.text if item.title else '',
                    'link': item.link.text if item.link else '',
                    'pubDate': item.pubDate.text if item.pubDate else '',
                    'source': item.source.text if item.source else ''
                })
            return news_items
        except Exception:
            return []

    def _get_duckduckgo_instant_answer(self) -> Optional[str]:
        """Fetch a summary from DuckDuckGo Instant Answer API (free)"""
        url = f"https://api.duckduckgo.com/?q={self.company_name}&format=json&no_html=1"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("AbstractText") or data.get("RelatedTopics", [{}])[0].get("Text")
        except Exception:
            return None

    def _get_bing_search(self) -> Dict:
        """Get company data using Bing search scraping (free, no API key)"""
        try:
            search_url = f"https://www.bing.com/search?q={quote_plus(self.company_name + ' company information')}"
            headers = {
                'User-Agent': 'Mozilla/5.0',
            }
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            for result in soup.find_all('li', class_='b_algo'):
                title_elem = result.find('h2')
                link_elem = result.find('a')
                snippet_elem = result.find('div', class_='b_caption')
                if title_elem and link_elem and snippet_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True)
                    if title and link and snippet:
                        results.append({
                            'title': title,
                            'link': link,
                            'snippet': snippet
                        })
            # Extract company website
            company_url = None
            for result in results:
                if any(domain in result['link'].lower() for domain in ['.com', '.org', '.net']):
                    if self.company_name.lower() in result['title'].lower():
                        company_url = result['link']
                        break
            return {
                "search_results": results[:5],
                "company_url": company_url
            }
        except Exception:
            return {"search_results": [], "company_url": None}

    def _get_company_website_info(self, crm_data_path: Optional[str] = None, fallback_url: Optional[str] = None) -> Dict:
        """Fetch and parse meta tags and OpenGraph data from the company website (from crm_data.json or Bing fallback)"""
        # Find company website from crm_data.json or fallback
        website = None
        if not crm_data_path:
            crm_data_path = str(Path(__file__).parent.parent.parent / 'data' / 'crm_data.json')
        try:
            with open(crm_data_path, "r") as f:
                crm_data = json.load(f)
            for lead in crm_data.get("crm_leads", []):
                if lead.get("company_name", "").lower() == self.company_name.lower():
                    website = lead.get("company_website")
                    break
        except Exception:
            pass
        if not website and fallback_url:
            website = fallback_url
        if not website:
            return {}
        try:
            resp = requests.get(website, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            meta = {tag.get("name", tag.get("property", "")).lower(): tag.get("content", "") for tag in soup.find_all("meta")}
            og = {tag.get("property", "").lower(): tag.get("content", "") for tag in soup.find_all("meta") if tag.get("property", "").startswith("og:")}
            info = {
                "description": meta.get("description") or og.get("og:description"),
                "title": meta.get("title") or og.get("og:title"),
                "site_name": og.get("og:site_name"),
                "mission": meta.get("mission"),
                "products": meta.get("products"),
                "team": meta.get("team"),
                "values": meta.get("values"),
            }
            return {k: v for k, v in info.items() if v}
        except Exception:
            return {}

    def _analyze_web_presence(self, website: str) -> Dict:
        """Analyze company's web presence: meta tags, social links, about text."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(website, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            meta_data = {
                "title": soup.title.string if soup.title else None,
                "description": soup.find("meta", {"name": "description"})["content"] if soup.find("meta", {"name": "description"}) else None,
                "keywords": soup.find("meta", {"name": "keywords"})["content"] if soup.find("meta", {"name": "keywords"}) else None
            }
            social_links = {}
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "linkedin.com" in href:
                    social_links["linkedin"] = href
                elif "twitter.com" in href:
                    social_links["twitter"] = href
                elif "facebook.com" in href:
                    social_links["facebook"] = href
                elif "instagram.com" in href:
                    social_links["instagram"] = href
            company_info = {}
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if 'about' in text.lower() or 'company' in text.lower():
                    company_info['about'] = text
                    break
            return {
                "meta_data": meta_data,
                "social_links": social_links,
                "company_info": company_info
            }
        except Exception:
            return {}

    def _llm_generate_summary(self, wiki_data, newsapi, google_news, duckduckgo, bing, website_info, web_presence) -> str:
        """Use Claude or OpenAI to generate a 500-word, natural language summary broken into key areas."""
        import openai
        import anthropic
        import os
        prompt = f"""
Can you please use the outputs from Wikipedia, NewsAPI, Google News RSS, DuckDuckGo, Bing Search, and company website meta tags below and summarize this into a 500 word, natural language summary which clearly outlines what the company does, why they do it, where they are based, their values etc. Anything that would be helpful to know for a sales rep to interact with someone from this company.

Break it into key areas like:
- Overview
- Products & Services
- Team
- Recent News or Blogs
- Web Presence
- Other relevant sections if available

Write your response as a natural language summary that will be read by a sales rep in preparation for a call. Do NOT output JSON.

----
WIKIPEDIA:
{wiki_data}

NEWSAPI:
{newsapi}

GOOGLE NEWS RSS:
{google_news}

DUCKDUCKGO:
{duckduckgo}

BING SEARCH:
{bing}

WEBSITE META TAGS:
{website_info}

WEB PRESENCE:
{web_presence}
"""
        claude_key = os.getenv("CLAUDE_API_KEY")
        if claude_key:
            client = anthropic.Anthropic(api_key=claude_key)
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0.2,
                system="You are a helpful sales research assistant.",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            client = openai.OpenAI(api_key=openai_key)
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are a helpful sales research assistant."},
                          {"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.2
            )
            return completion.choices[0].message.content.strip()
        return "\n\n".join([
            f"Overview: {wiki_data.get('extract', '')}",
            f"DuckDuckGo: {duckduckgo}",
            f"Bing: {bing}",
            f"Website: {website_info}",
            f"Web Presence: {web_presence}",
            f"NewsAPI: {[a.get('title') for a in newsapi] if newsapi else ''}",
            f"Google News: {[a.get('title') for a in google_news] if google_news else ''}"
        ])

    def run(self):
        """
        Gathers company data from Wikipedia, NewsAPI, Google News RSS, DuckDuckGo, Bing Search, and company website meta tags, then uses an LLM to generate a 500-word, natural language summary for sales preparation. Also saves the output to data/outputs/company_{company_name}.txt.
        """
        try:
            wiki_data = self._get_wikipedia_data()
            newsapi = self._get_newsapi_data()
            google_news = self._get_google_news_rss()
            duckduckgo = self._get_duckduckgo_instant_answer()
            bing = self._get_bing_search()
            website_info = self._get_company_website_info(fallback_url=bing.get("company_url"))
            web_presence = self._analyze_web_presence(bing.get("company_url")) if bing.get("company_url") else {}
            summary = self._llm_generate_summary(wiki_data, newsapi, google_news, duckduckgo, bing, website_info, web_presence)
            # Save output
            outputs_dir = Path(__file__).parent.parent.parent / 'data' / 'outputs'
            outputs_dir.mkdir(parents=True, exist_ok=True)
            safe_company = self.company_name.replace(' ', '_').lower()
            with open(outputs_dir / f'company_{safe_company}.txt', 'w') as f:
                f.write(summary)
            return summary
        except Exception as e:
            return f"Error researching company: {str(e)}" 
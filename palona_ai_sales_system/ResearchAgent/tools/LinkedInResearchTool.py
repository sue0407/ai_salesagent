from agency_swarm.tools import BaseTool
from pydantic import Field
import os
import requests
from typing import Optional, Dict, List
from dotenv import load_dotenv
import re
from pathlib import Path

load_dotenv()

class LinkedInResearchTool(BaseTool):
    """
    Researches prospects using publicly available data from Google Custom Search, Bing, DuckDuckGo, and Google News RSS.
    Uses an LLM (Claude or OpenAI) to generate a 300-word, resume-style summary for sales preparation, including:
    - Name, location, follower count, current company and position at the top
    - Overview section
    - Key career experience
    - Current role and duration
    - Recent news articles or posts
    - All details relevant for a sales rep to prepare for sales communication
    The person's name and company are provided as explicit inputs, not extracted from the LinkedIn URL.
    """
    linkedin_url: str = Field(
        ..., description="LinkedIn profile URL to research"
    )
    name: str = Field(
        ..., description="Full name of the person to research"
    )
    company: str = Field(
        ..., description="Current company of the person to research"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Google Custom Search API key (if not provided, will use environment variable)"
    )

    def _get_api_key(self) -> str:
        api_key = self.api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key not found in environment variables")
        return api_key

    def _get_search_engine_id(self) -> str:
        search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        if not search_engine_id:
            raise ValueError("Google Search Engine ID not found in environment variables")
        return search_engine_id

    def _extract_profile_id(self, url: str) -> str:
        if "linkedin.com/in/" in url:
            parts = url.split("linkedin.com/in/")
            profile_id = parts[1].split("/")[0].split("?")[0]
            return profile_id
        raise ValueError("Invalid LinkedIn profile URL format")

    def _get_google_custom_search(self, name: str, company: str) -> Dict:
        api_key = self._get_api_key()
        search_engine_id = self._get_search_engine_id()
        query = f'site:linkedin.com/in/ "{name}" "{company}"'
        search_url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": search_engine_id,
            "q": query
        }
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        return response.json()

    def _extract_company_from_google(self, google_data: dict) -> str:
        """Try to extract company name from Google Custom Search results."""
        # Look for company in snippet or title
        if 'items' in google_data:
            for item in google_data['items']:
                snippet = item.get('snippet', '')
                title = item.get('title', '')
                # Try to find a company name pattern (e.g., 'at CompanyName')
                match = re.search(r'at ([A-Za-z0-9&.,\- ]+)', snippet)
                if match:
                    return match.group(1).strip()
                match = re.search(r'at ([A-Za-z0-9&.,\- ]+)', title)
                if match:
                    return match.group(1).strip()
        return ''

    def _get_bing_search(self, name: str, company: str) -> List[Dict]:
        """Search Bing for the person's name and company to avoid mismatches with common names."""
        try:
            query = f"{name} {company} LinkedIn" if company else f"{name} LinkedIn"
            search_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            from bs4 import BeautifulSoup
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
            return results[:5]
        except Exception:
            return []

    def _get_duckduckgo_search(self, name: str, company: str) -> Optional[str]:
        """Search DuckDuckGo for the person's name and company to avoid mismatches with common names."""
        query = f"{name} {company} LinkedIn" if company else f"{name} LinkedIn"
        url = f"https://api.duckduckgo.com/?q={query.replace(' ', '+')}&format=json&no_html=1"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("AbstractText") or data.get("RelatedTopics", [{}])[0].get("Text")
        except Exception:
            return None

    def _get_google_news_rss(self, name: str, company: str) -> List[Dict]:
        """Search Google News RSS for the person's name and company to avoid mismatches with common names."""
        try:
            from bs4 import BeautifulSoup
            from urllib.parse import quote_plus
            query = f"{name} {company}" if company else name
            encoded_query = quote_plus(query)
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

    def _gather_profile_data(self) -> Dict:
        # Use explicit name and company provided by the user for all searches
        google_data = self._get_google_custom_search(self.name, self.company)
        bing_data = self._get_bing_search(self.name, self.company)
        duckduckgo_data = self._get_duckduckgo_search(self.name, self.company)
        news_data = self._get_google_news_rss(self.name, self.company)
        return {
            "name": self.name,
            "company": self.company,
            "google_custom_search": google_data,
            "bing_search": bing_data,
            "duckduckgo": duckduckgo_data,
            "google_news": news_data
        }

    def _llm_generate_summary(self, profile_data: Dict) -> str:
        import openai
        import anthropic
        import os
        prompt = f"""
Can you please take this LinkedIn profile information and summarize this into a 300 word summary with details on the user's background, key career experience, current role and duration in role. This is a summary for a sales rep to prepare for a sales communication, so make sure all the relevant details are there for this purpose, it should be an overview that will rapidly bring someone up to speed on a prospect they are about to have a meeting with.
Make it read like a resume, with Name, location, follower count, current company and position all listed one after the other at the top, before you break into an overview section and then experience, news/posts etc.

Here is the data:
GOOGLE CUSTOM SEARCH:
{profile_data['google_custom_search']}

BING SEARCH:
{profile_data['bing_search']}

DUCKDUCKGO:
{profile_data['duckduckgo']}

GOOGLE NEWS RSS:
{profile_data['google_news']}
"""
        claude_key = os.getenv("CLAUDE_API_KEY")
        if claude_key:
            client = anthropic.Anthropic(api_key=claude_key)
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=600,
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
                max_tokens=600,
                temperature=0.2
            )
            return completion.choices[0].message.content.strip()
        # Fallback: concatenate text
        return f"GOOGLE CUSTOM SEARCH: {profile_data['google_custom_search']}\nBING: {profile_data['bing_search']}\nDUCKDUCKGO: {profile_data['duckduckgo']}\nGOOGLE NEWS: {profile_data['google_news']}"

    def run(self):
        """
        Performs LinkedIn profile research using publicly available data and generates a 300-word, resume-style summary for sales preparation using an LLM. Returns a natural language summary (not JSON), formatted as specified in the prompt. Also saves the output to data/outputs/linkedin_{name}.txt.
        """
        try:
            profile_data = self._gather_profile_data()
            summary = self._llm_generate_summary(profile_data)
            # Save output
            outputs_dir = Path(__file__).parent.parent.parent / 'data' / 'outputs'
            outputs_dir.mkdir(parents=True, exist_ok=True)
            safe_name = self.name.replace(' ', '_').lower()
            with open(outputs_dir / f'linkedin_{safe_name}.txt', 'w') as f:
                f.write(summary)
            return summary
        except requests.exceptions.RequestException as e:
            return f"API request failed: {str(e)}"
        except Exception as e:
            return f"Error researching profile: {str(e)}" 
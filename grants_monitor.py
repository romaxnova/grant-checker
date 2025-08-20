"""
Production-ready grants monitoring system using xAI Grok and Slack notifications.
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from slack_sdk.webhook import WebhookClient

# Add src to path for imports  
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate

# Import our configuration
from config import GRANT_SOURCES, RELEVANT_KEYWORDS, EXTRACTION_SETTINGS, SLACK_SETTINGS

class GrantsMonitor:
    """Production grants monitoring system."""
    
    def __init__(self):
        """Initialize the grants monitor."""
        load_dotenv()
        
        # Initialize xAI Grok
        api_key = os.getenv('GROQ_API_KEY')  # Contains xAI key
        if not api_key:
            raise ValueError("Please set GROQ_API_KEY (xAI key) in your .env file")
            
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
            model="grok-2",
            temperature=0.1
        )
        
        # Initialize Slack webhook
        slack_webhook = os.getenv('SLACK_BOT_TOKEN')
        if not slack_webhook:
            raise ValueError("Please set SLACK_BOT_TOKEN in your .env file")
            
        self.slack = WebhookClient(slack_webhook)
        
        # Text processing
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=EXTRACTION_SETTINGS['chunk_size'],
            chunk_overlap=EXTRACTION_SETTINGS['chunk_overlap']
        )
        
        # Results storage
        self.discovered_grants = []
        
    def scrape_grant_source(self, source: Dict[str, Any]) -> str:
        """
        Scrape content from a grant source website with retry logic.
        
        Args:
            source (Dict): Grant source configuration
            
        Returns:
            str: Scraped text content
        """
        try:
            print(f"🌐 Scraping: {source['name']}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5,fr;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Retry logic for better reliability
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(
                        source['url'], 
                        headers=headers, 
                        timeout=30,
                        allow_redirects=True
                    )
                    response.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        raise e
                    print(f"   ⚠️ Attempt {attempt + 1} failed, retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements more thoroughly
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
                element.decompose()
            
            # Try to find main content areas first
            main_content = None
            content_selectors = [
                'main', '[role="main"]', '.main-content', '#main-content',
                '.content', '#content', 'article', '.article'
            ]
            
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # Use main content if found, otherwise use full body
            content_element = main_content if main_content else soup.find('body')
            if not content_element:
                content_element = soup
            
            # Extract text content
            text = content_element.get_text()
            
            # Clean text more thoroughly
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            cleaned_text = ' '.join(chunk for chunk in chunks if chunk and len(chunk) > 2)
            
            print(f"   ✅ Scraped {len(cleaned_text)} characters")
            return cleaned_text
            
        except Exception as e:
            print(f"   ❌ Error scraping {source['name']}: {e}")
            return ""
    
    def discover_specific_grant_urls(self, source: Dict[str, Any], main_content: str) -> List[str]:
        """
        Discover specific grant URLs from main program pages like Bpifrance.
        
        Args:
            source (Dict): Grant source configuration
            main_content (str): Main page content
            
        Returns:
            List[str]: List of specific grant URLs
        """
        try:
            print(f"🔍 Discovering specific grants from {source['name']}")
            
            # Extract URLs from the main content using AI
            discovery_prompt = f"""
            You are an expert at finding specific grant and funding opportunity URLs.
            
            From the following webpage content from "{source['name']}", extract all specific URLs that lead to individual grants, calls for proposals, or funding opportunities.
            
            Focus on URLs that are likely to contain grants related to:
            - Healthcare technology and AI
            - Digital innovation and automation  
            - Startup and SME funding
            - Research and development
            - Administrative technology
            
            Look for patterns like:
            - "appel à projets"
            - "concours"
            - "financement"
            - "subvention"
            - Individual grant program names
            - Specific deadline dates
            
            Return ONLY a JSON array of URLs. Each URL should be complete and valid.
            If you find relative URLs, convert them to absolute URLs using the base: {source['url']}
            
            Example format: ["https://example.com/grant1", "https://example.com/grant2"]
            
            Content to analyze:
            {main_content[:3000]}
            
            JSON Response:
            """
            
            response = self.llm.invoke([HumanMessage(content=discovery_prompt)])
            result_text = response.content.strip()
            
            if result_text.startswith('```json'):
                result_text = result_text[7:-3]
            elif result_text.startswith('```'):
                result_text = result_text[3:-3]
                
            urls = json.loads(result_text)
            
            # Validate and clean URLs
            valid_urls = []
            for url in urls:
                if isinstance(url, str) and url.startswith('http'):
                    # Limit to reasonable domain matches
                    if any(domain in url for domain in ['bpifrance', 'anr.fr', 'economie.gouv', 'boamp.fr']):
                        valid_urls.append(url)
            
            print(f"   ✅ Discovered {len(valid_urls)} specific grant URLs")
            return valid_urls[:5]  # Limit to top 5 to avoid overwhelming
            
        except Exception as e:
            print(f"   ⚠️ Error discovering URLs: {e}")
            return []
    
    def extract_grants_from_text(self, text: str, source_name: str) -> List[Dict[str, Any]]:
        """
        Extract grants from text using xAI Grok with enhanced multilingual support.
        
        Args:
            text (str): Text to analyze
            source_name (str): Name of the source
            
        Returns:
            List[Dict]: Extracted grants
        """
        try:
            print(f"🤖 Analyzing content from {source_name} with Grok...")
            
            # Enhanced prompt for better extraction with multilingual support
            prompt_template = PromptTemplate(
                input_variables=["text", "keywords", "source_name"],
                template="""
You are an expert grant analyst who speaks multiple languages (English, French, German, etc.). 

Extract funding opportunities from the following text from "{source_name}".

Focus on grants that match these keywords: {keywords}

For EACH grant found, return a JSON object with these fields:
- "title": Grant name/title (translate to English if needed)
- "organization": Funding organization or agency
- "amount": Funding amount as number + currency (extract specific amounts like "€2M", "$500K", or "Not specified")
- "deadline": Application deadline in YYYY-MM-DD format if possible (or "Not specified")
- "published_date": Date when this grant was published/announced in YYYY-MM-DD format (look for "publié le", "published on", "date de publication", etc.)
- "description": Brief description (2-3 sentences max, translate to English if needed)
- "eligibility": Who can apply (companies, universities, individuals, etc.)
- "url": Any specific URL mentioned for this grant
- "relevance_score": Rate 1-10 how relevant this is for tech/innovation/research projects
- "country": Country/region this grant is for
- "language": Original language of the grant announcement

IMPORTANT EXTRACTION RULES:
1. Look for keywords like: "funding", "grant", "call for proposals", "appel à projets", "financement", "subvention", "concours", "bourse"
2. Extract specific monetary amounts when mentioned
3. Look for dates and deadlines carefully
4. Only include grants with relevance_score >= 6
5. If text is in French/other languages, translate key info to English but note original language
6. Look for innovation, technology, research, startup, SME funding specifically

Return ONLY a valid JSON array. If no relevant grants found, return: []

Text to analyze:
{text}

JSON Response:
"""
            )
            
            keywords_str = ", ".join(RELEVANT_KEYWORDS + [
                "innovation", "recherche", "financement", "subvention", 
                "technologie", "startup", "PME", "digital", "IA"
            ])
            
            # Process text in chunks if too large
            if len(text) > EXTRACTION_SETTINGS['chunk_size']:
                chunks = self.text_splitter.split_text(text)
                all_grants = []
                
                # Process up to 5 chunks for better coverage
                for i, chunk in enumerate(chunks[:5]):
                    try:
                        prompt = prompt_template.format(
                            text=chunk, 
                            keywords=keywords_str,
                            source_name=source_name
                        )
                        response = self.llm.invoke([HumanMessage(content=prompt)])
                        
                        # Parse JSON response
                        result_text = response.content.strip()
                        if result_text.startswith('```json'):
                            result_text = result_text[7:-3]
                        elif result_text.startswith('```'):
                            result_text = result_text[3:-3]
                            
                        grants_data = json.loads(result_text)
                        if isinstance(grants_data, list):
                            all_grants.extend(grants_data)
                            
                    except Exception as e:
                        print(f"   ⚠️ Error processing chunk {i+1}: {e}")
                        continue
                
                return all_grants
            else:
                # Process entire text
                prompt = prompt_template.format(
                    text=text, 
                    keywords=keywords_str,
                    source_name=source_name
                )
                response = self.llm.invoke([HumanMessage(content=prompt)])
                
                result_text = response.content.strip()
                if result_text.startswith('```json'):
                    result_text = result_text[7:-3]
                elif result_text.startswith('```'):
                    result_text = result_text[3:-3]
                    
                grants_data = json.loads(result_text)
                return grants_data if isinstance(grants_data, list) else []
                
        except Exception as e:
            print(f"   ❌ Error extracting grants: {e}")
            return []
    
    def send_slack_notification(self, grants: List[Dict[str, Any]]) -> bool:
        """
        Send grants digest to Slack with rich formatting for French healthtech startup.
        
        Args:
            grants (List[Dict]): List of discovered grants
            
        Returns:
            bool: Success status
        """
        try:
            if not grants:
                print("📭 No grants to send")
                return True
                
            # Create message focused on French healthcare AI startup
            message = f"🎯 *Weekly Grants Digest* - {datetime.now().strftime('%B %d, %Y')}\n\n"
            
            # Count new grants (published in last 7 days)
            recent_grants = []
            older_grants = []
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for grant in grants:
                pub_date = grant.get('published_date', '')
                try:
                    if pub_date and pub_date != 'Not specified':
                        grant_date = datetime.strptime(pub_date, '%Y-%m-%d')
                        if grant_date >= cutoff_date:
                            recent_grants.append(grant)
                        else:
                            older_grants.append(grant)
                    else:
                        older_grants.append(grant)
                except:
                    older_grants.append(grant)
            
            message += f"Found *{len(grants)}* relevant funding opportunities:\n"
            if recent_grants:
                message += f"🆕 *{len(recent_grants)} new* (published in last 7 days)\n"
            if older_grants:
                message += f"📋 {len(older_grants)} ongoing opportunities\n"
            message += "\n"
            
            # Add each grant (limit to top 10)
            for i, grant in enumerate(grants[:10], 1):
                # Format with proper Slack markdown and clear URLs
                title = grant.get('title', 'Unknown Title')
                amount = grant.get('amount', 'Not specified') 
                org = grant.get('organization', 'Not specified')
                deadline = grant.get('deadline', 'Not specified')
                published_date = grant.get('published_date', 'Not specified')
                description = grant.get('description', 'No description')
                relevance = grant.get('relevance_score', 'N/A')
                source = grant.get('source', 'Unknown')
                
                # Truncate description if too long
                if len(description) > 150:
                    description = description[:150] + "..."
                
                message += f"*{i}. {title}*\n"
                message += f"💰 Amount: {amount}\n"
                message += f"🏢 Organization: {org}\n"
                message += f"📅 Deadline: {deadline}\n"
                message += f"📰 Published: {published_date}\n"
                message += f"📝 {description}\n"
                message += f"⭐ Relevance: {relevance}/10\n"
                message += f"🌍 Source: {source}\n"
                
                # Add clickable URL with validation
                grant_url = grant.get('url', '').strip()
                if grant_url and grant_url != 'Not specified' and grant_url.startswith('http'):
                    # Validate URL format for Slack
                    if '|' in grant_url:
                        grant_url = grant_url.split('|')[0]  # Remove any existing link text
                    message += f"🔗 <{grant_url}|Apply Here>\n"
                elif grant.get('source_url'):
                    message += f"🔗 <{grant['source_url']}|View Source>\n"
                    
                message += "\n---\n\n"
            
            # Ensure message isn't too long
            if len(message) > 4000:
                message = message[:3900] + "\n\n...(truncated for length)"
            
            # Send to Slack 
            response = self.slack.send(text=message)
            
            if response.status_code == 200:
                print(f"✅ Sent rich Slack notification with {len(grants)} grants")
                return True
            else:
                print(f"❌ Slack notification failed: {response.status_code}")
                print(f"Response: {response.body}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending Slack notification: {e}")
            return False
    
    def run_grants_scan(self) -> Dict[str, Any]:
        """
        Run a complete grants scanning cycle.
        
        Returns:
            Dict: Scan results summary
        """
        print(f"🚀 Starting grants scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        start_time = time.time()
        total_grants = []
        sources_processed = 0
        
        # Process each grant source
        for source in GRANT_SOURCES:
            if not source.get('active', True):
                print(f"⏭️ Skipping inactive source: {source['name']}")
                continue
                
            try:
                # Scrape content
                content = self.scrape_grant_source(source)
                if not content:
                    continue
                
                # For major programs like Bpifrance, discover specific grant URLs
                specific_urls = []
                if any(keyword in source['name'].lower() for keyword in ['bpifrance', 'anr', 'france relance']):
                    specific_urls = self.discover_specific_grant_urls(source, content)
                
                # Extract grants from main content
                grants = self.extract_grants_from_text(content, source['name'])
                
                # Also extract from specific URLs if found
                for url in specific_urls:
                    try:
                        print(f"   🔍 Analyzing specific URL: {url[:50]}...")
                        specific_response = requests.get(url, timeout=20)
                        specific_soup = BeautifulSoup(specific_response.content, 'html.parser')
                        specific_text = specific_soup.get_text()
                        
                        # Clean and analyze specific page
                        lines = (line.strip() for line in specific_text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        clean_specific_text = ' '.join(chunk for chunk in chunks if chunk and len(chunk) > 2)
                        
                        specific_grants = self.extract_grants_from_text(clean_specific_text, f"{source['name']} - Specific Page")
                        
                        # Add specific URL to each grant
                        for grant in specific_grants:
                            grant['specific_url'] = url
                        
                        grants.extend(specific_grants)
                        time.sleep(1)  # Rate limiting
                        
                    except Exception as e:
                        print(f"   ⚠️ Error processing specific URL: {e}")
                        continue
                
                if grants:
                    # Add source information
                    for grant in grants:
                        grant['source'] = source['name']
                        grant['source_url'] = source['url']
                        grant['discovered_at'] = datetime.now().isoformat()
                    
                    total_grants.extend(grants)
                    print(f"   ✅ Found {len(grants)} grants from {source['name']}")
                else:
                    print(f"   📭 No relevant grants found in {source['name']}")
                    
                sources_processed += 1
                
                # Rate limiting - pause between requests
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Error processing {source['name']}: {e}")
                continue
        
        # Sort by publication date (newest first), then by relevance score
        def sort_key(grant):
            # Parse publication date
            pub_date = grant.get('published_date', '')
            try:
                if pub_date and pub_date != 'Not specified':
                    # Convert to datetime for sorting
                    date_obj = datetime.strptime(pub_date, '%Y-%m-%d')
                    return (date_obj, float(grant.get('relevance_score', 0)))
                else:
                    # No date specified - put at end with just relevance
                    return (datetime.min, float(grant.get('relevance_score', 0)))
            except:
                return (datetime.min, float(grant.get('relevance_score', 0)))
        
        total_grants.sort(key=sort_key, reverse=True)
        
        # Send to Slack
        slack_success = self.send_slack_notification(total_grants)
        
        # Generate summary
        scan_time = time.time() - start_time
        summary = {
            'timestamp': datetime.now().isoformat(),
            'sources_processed': sources_processed,
            'total_sources': len([s for s in GRANT_SOURCES if s.get('active', True)]),
            'grants_found': len(total_grants),
            'scan_duration_seconds': round(scan_time, 2),
            'slack_notification_sent': slack_success,
            'top_grants': total_grants[:5]  # Top 5 for summary
        }
        
        print("=" * 60)
        print(f"✅ Scan complete!")
        print(f"📊 Processed {sources_processed} sources in {scan_time:.1f}s")
        print(f"🎯 Found {len(total_grants)} relevant grants")
        print(f"📱 Slack notification: {'✅ Sent' if slack_success else '❌ Failed'}")
        
        return summary

def main():
    """Main execution function."""
    try:
        monitor = GrantsMonitor()
        results = monitor.run_grants_scan()
        
        # Save results for record keeping
        with open(f"grants_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(results, f, indent=2)
            
        print(f"\n💾 Results saved to grants_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
    except Exception as e:
        print(f"❌ Error in main execution: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

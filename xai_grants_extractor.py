"""
Grants extraction agent using xAI's Grok models via OpenAI-compatible API.
"""

import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import requests
from bs4 import BeautifulSoup

class GrantsExtractorXAI:
    """Grants extraction agent using xAI's Grok models."""
    
    def __init__(self, model="grok-2"):
        """
        Initialize the grants extractor with xAI Grok.
        
        Args:
            model (str): xAI model to use (grok-2, grok-beta, etc.)
        """
        load_dotenv()
        
        # Get xAI API key (stored as GROQ_API_KEY in our .env)
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key or api_key == 'your_groq_api_key_here':
            raise ValueError("Please set GROQ_API_KEY (xAI key) in your .env file")
        
        # Initialize xAI Grok via OpenAI-compatible endpoint
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
            model=model,
            temperature=0.1  # Lower temperature for more consistent extraction
        )
        
        # Text splitter for large web pages
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200
        )
        
    def scrape_website(self, url: str) -> str:
        """
        Scrape content from a website.
        
        Args:
            url (str): URL to scrape
            
        Returns:
            str: Cleaned text content
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return ""
    
    def extract_grants(self, text: str) -> List[str]:
        """
        Extract grant information from text using xAI Grok.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            List[str]: List of extracted grants
        """
        
        # Create prompt for grant extraction
        prompt = PromptTemplate(
            input_variables=["text"],
            template="""
You are an expert at extracting grant and funding opportunity information from text. 

Please analyze the following text and extract any grant or funding opportunities. For each grant you find, provide:

1. **Title**: The name/title of the grant
2. **Organization**: The funding organization or agency  
3. **Amount**: The funding amount (if mentioned)
4. **Deadline**: Application deadline (if mentioned)
5. **Description**: Brief description of what the grant funds
6. **Eligibility**: Who is eligible to apply (if mentioned)
7. **URL**: Any specific URL mentioned for the grant (if available)

Format each grant as a clearly structured entry. If no grants are found, respond with "No grants found."

Be thorough but accurate - only extract information that is clearly present in the text.

Text to analyze:
{text}

Extracted Grants:
"""
        )
        
        # Split text if it's too long
        if len(text) > 4000:
            chunks = self.text_splitter.split_text(text)
            all_grants = []
            
            for i, chunk in enumerate(chunks[:3]):  # Limit to first 3 chunks
                try:
                    print(f"Processing chunk {i+1}/{min(3, len(chunks))}...")
                    chain = LLMChain(llm=self.llm, prompt=prompt)
                    result = chain.run(text=chunk)
                    if "No grants found" not in result:
                        all_grants.append(result)
                except Exception as e:
                    print(f"Error processing chunk {i+1}: {e}")
                    continue
            
            return all_grants
        else:
            try:
                chain = LLMChain(llm=self.llm, prompt=prompt)
                result = chain.run(text=text)
                return [result] if "No grants found" not in result else []
            except Exception as e:
                print(f"Error processing text: {e}")
                return []
    
    def format_grants_summary(self, grants_data: List[str]) -> str:
        """
        Format extracted grants into a readable summary.
        
        Args:
            grants_data (List[str]): Raw grants data from LLM
            
        Returns:
            str: Formatted summary
        """
        if not grants_data:
            return "No grants found in the analyzed content."
        
        summary = "🎯 **GRANTS DIGEST**\n"
        summary += "=" * 50 + "\n\n"
        
        for i, grants_text in enumerate(grants_data, 1):
            summary += f"**Source {i}:**\n"
            summary += grants_text + "\n\n"
            summary += "-" * 30 + "\n\n"
        
        return summary

# Test functions
def test_xai_connection():
    """Test xAI Grok connection."""
    print("🧪 Testing xAI Grok connection...")
    
    try:
        extractor = GrantsExtractorXAI(model="grok-2")
        
        # Simple test message
        response = extractor.llm.invoke([HumanMessage(content="Hello! Just testing the xAI connection. Please respond briefly.")])
        print("✅ xAI Grok connection successful!")
        print(f"   Response: {response.content[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ xAI connection failed: {e}")
        return False

def test_grants_extraction():
    """Test grant extraction functionality."""
    print("🧪 Testing grant extraction with xAI Grok...")
    
    try:
        extractor = GrantsExtractorXAI(model="grok-2")
        
        # Test with sample grant text
        sample_text = """
        The National Science Foundation (NSF) is pleased to announce the availability of funding 
        through the Small Business Innovation Research (SBIR) program. This program provides 
        up to $500,000 in Phase I funding for innovative small businesses developing cutting-edge 
        technologies. Applications are due March 15, 2024. The program is open to small businesses 
        with fewer than 500 employees. For more information, visit 
        https://www.nsf.gov/funding/pgm_summ.jsp?pims_id=5371
        
        Additionally, the Department of Energy announces the Clean Energy Innovation Grant 
        with up to $2 million available for renewable energy projects. Application deadline 
        is April 30, 2024. Universities and research institutions are eligible to apply.
        More details at https://www.energy.gov/funding-opportunities
        """
        
        print("Extracting grants from sample text...")
        grants = extractor.extract_grants(sample_text)
        summary = extractor.format_grants_summary(grants)
        
        print("✅ Extraction successful!")
        print("\nExtracted grants:")
        print(summary)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run tests and examples."""
    print("🚀 xAI Grok Grants Extractor Test")
    print("=" * 50)
    
    # Test xAI connection
    if test_xai_connection():
        print()
        # Test grants extraction
        test_grants_extraction()
    
    print()
    print("=" * 50)
    print("🎉 Test complete!")
    print("\nUsing xAI Grok for:")
    print("• Intelligent grant information extraction")
    print("• Natural language understanding")
    print("• Structured data output")
    print("• Weekly funding opportunity analysis")

if __name__ == "__main__":
    main()

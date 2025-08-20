# Grant Checker

A production-ready, AI-powered system for monitoring and extracting relevant grant opportunities for French and EU startups, with a focus on healthcare, insurance, and AI innovation.

## Features
- Scrapes and analyzes top French and EU grant sources (Bpifrance, ANR, EIC, etc.)
- Uses xAI Grok LLM for intelligent, multilingual grant extraction
- Filters for healthtech, admintech, AI, and digital innovation
- Publishes weekly digests to Slack with clickable links, deadlines, and publication dates
- Granular extraction for large sources (e.g., Bpifrance)
- Results sorted by publication date for easy tracking

## Quick Start
1. **Clone the repo:**
   ```sh
   git clone <your-repo-url>
   cd grant-checker
   ```
2. **Set up Python environment:**
   ```sh
   python3 -m venv agents
   source agents/bin/activate
   pip install -r requirements.txt
   ```
3. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in your xAI API key and Slack webhook URL.
4. **Run a scan:**
   ```sh
   python grants_monitor.py
   ```

## Deployment
- Schedule weekly runs with cron or a workflow runner:
  ```sh
  0 9 * * 1 cd /path/to/grant-checker && source agents/bin/activate && python grants_monitor.py
  ```
- Results and digests are sent to your configured Slack channel.

## Customization
- Edit `config.py` to adjust sources, keywords, and notification settings.
- Add or remove grant sources as needed.

## License
MIT
# Grants Extraction Agent with LangChain

This project uses LangChain to build an AI-powered grants extraction agent that scrapes grant opportunities from various websites and sends weekly Slack digests.

## Setup

1. **Python Environment**: 
   ```bash
   cd /Users/romanstadnikov/Desktop/agents/langchain
   source agents/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**:
   - Copy `.env.example` to `.env`
   - Fill in your API keys for OpenAI/Groq and Slack

## Project Structure

```
langchain/
├── agents/              # Python virtual environment
├── src/
│   ├── agents/         # LangChain agents
│   ├── scrapers/       # Web scrapers for different grant sites
│   ├── processors/     # Text processing and extraction
│   └── notifiers/      # Slack notification handlers
├── config/             # Configuration files
├── data/               # Scraped data and outputs
├── requirements.txt    # Python dependencies
└── .env.example       # Environment variables template
```

## Features

- **AI-Powered Extraction**: Uses LLMs to intelligently extract grant information
- **Multi-Site Scraping**: Supports various grant websites with different structures
- **Smart Filtering**: Filters relevant grants based on criteria
- **Slack Integration**: Sends formatted weekly digests
- **Scheduling**: Automated weekly runs

## LangChain Components Used

- **Chat Models**: OpenAI GPT and Groq for text processing
- **Document Loaders**: Web page content extraction
- **Text Splitters**: Handle large web pages
- **Chains**: Orchestrate extraction workflows
- **Agents**: Dynamic decision making for complex sites

## Getting Started

1. Test the basic setup with a simple LangChain example
2. Configure your grant source websites
3. Test individual scrapers
4. Set up Slack integration
5. Schedule weekly runs

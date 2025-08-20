"""
Configuration for grant sources and extraction settings.
"""

# Grant source websites to monitor - Focused on French and relevant EU opportunities
GRANT_SOURCES = [
    {
        "name": "Bpifrance - Concours et Appels à Projets",
        "url": "https://www.bpifrance.fr/nos-appels-a-projets-concours",
        "type": "french_development", 
        "active": True
    },
    {
        "name": "BOAMP - Bulletin Officiel des Annonces de Marchés Publics",
        "url": "https://www.boamp.fr/",
        "type": "french_public",
        "active": True
    },
    # Removed France Relance - Aides aux Entreprises due to persistent 403 errors
    {
        "name": "ANR - Appels à Projets en Cours",
        "url": "https://anr.fr/fr/appels-a-projets/",
        "type": "french_research",
        "active": True
    },
    {
        "name": "European Innovation Council (EIC)",
        "url": "https://eic.ec.europa.eu/eic-funding-opportunities_en",
        "type": "european",
        "active": True
    },
    {
        "name": "Horizon Europe Work Programme",
        "url": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/programmes/horizon",
        "type": "european",
        "active": True
    },
    {
        "name": "Digital Europe Programme",
        "url": "https://digital-strategy.ec.europa.eu/en/activities/digital-programme",
        "type": "eu_digital",
        "active": True
    },
    # Removed French Tech - Startup Support due to persistent SSL errors
    {
        "name": "Caisse des Dépôts - Innovation Fund",
        "url": "https://www.caissedesdepots.fr/",
        "type": "french_institutional",
        "active": True
    }
]

# Keywords to filter relevant grants - Focused on AI healthcare administration startup
RELEVANT_KEYWORDS = [
    # Core AI & Healthcare
    "intelligence artificielle", "IA", "AI", "artificial intelligence", "machine learning",
    "santé", "healthcare", "health", "médical", "medical", "administration", "administratif",
    "assurance", "insurance", "mutuelle", "sécurité sociale", "social security",
    
    # Healthcare Tech
    "healthtech", "medtech", "e-santé", "e-health", "digital health", "santé numérique",
    "télémédecine", "telemedicine", "dossier médical", "medical records", "EHR",
    "facturation médicale", "medical billing", "remboursement", "reimbursement",
    
    # Technology & Innovation  
    "deeptech", "startup", "innovation", "numérique", "digital", "transformation digitale",
    "automatisation", "automation", "traitement automatique", "processing",
    "algorithme", "algorithm", "données", "data", "big data", "analytics",
    
    # Business & Funding
    "PME", "startup", "entreprise innovante", "innovative company", "small business",
    "financement", "funding", "investissement", "investment", "subvention", "grant",
    "développement", "development", "recherche", "research", "R&D",
    
    # Specific French Programs
    "France 2030", "Bpifrance", "PIA", "programme d'investissements d'avenir",
    "french tech", "deeptech", "concours innovation", "appel à projets"
]

# Grant extraction settings
EXTRACTION_SETTINGS = {
    "max_pages_per_source": 3,
    "chunk_size": 4000,
    "chunk_overlap": 200,
    "min_grant_amount": 1000,  # Minimum funding amount to consider
    "max_deadline_days": 90,   # Only consider grants with deadlines within 90 days
}

# Slack notification settings
SLACK_SETTINGS = {
    "channel": "#grants-alerts",
    "username": "Grants Bot",
    "icon_emoji": ":money_with_wings:",
    "max_message_length": 4000
}

"""
Scrapers package for fetching real-world data.

Data Sources:
- US Census Bureau 2010: Surname frequency data
- US Social Security Administration: First name frequency data  
- Y Combinator: Company names
- GitHub: Issue/task patterns from public repositories
- Asana Templates: Project and section naming patterns
"""

from src.scrapers.real_data_scraper import (
    RealDataScraper,
    CensusSurnameScraper,
    SSAFirstNameScraper,
    YCombinatorScraper,
    GitHubIssueScraper,
    AsanaTemplateScraper,
)

__all__ = [
    "RealDataScraper",
    "CensusSurnameScraper",
    "SSAFirstNameScraper",
    "YCombinatorScraper",
    "GitHubIssueScraper",
    "AsanaTemplateScraper",
]
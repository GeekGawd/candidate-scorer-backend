import requests
import logging
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class VerificationService:
    """Service for verifying candidate information through profile crawling"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def verify_candidate_profiles(self, profile_urls: Dict[str, str]) -> Dict[str, Any]:
        """
        Verify candidate profiles from multiple sources
        
        Args:
            profile_urls: Dictionary with keys like 'github_url', 'linkedin_url', 'portfolio_url'
        
        Returns:
            Dictionary with verification data from all sources
        """
        verification_data = {
            'github': {},
            'linkedin': {},
            'portfolio': {},
            'summary': '',
            'verification_score': 0.0
        }
        
        successful_verifications = 0
        total_urls = 0
        
        for url_type, url in profile_urls.items():
            if url and url.strip():
                total_urls += 1
                try:
                    if 'github.com' in url.lower():
                        verification_data['github'] = self._verify_github_profile(url)
                        if verification_data['github']:
                            successful_verifications += 1
                    elif 'linkedin.com' in url.lower():
                        verification_data['linkedin'] = self._verify_linkedin_profile(url)
                        if verification_data['linkedin']:
                            successful_verifications += 1
                    else:
                        verification_data['portfolio'] = self._verify_portfolio_site(url)
                        if verification_data['portfolio']:
                            successful_verifications += 1
                except Exception as e:
                    logger.error(f"Failed to verify {url_type}: {e}")
        
        # Calculate verification score
        if total_urls > 0:
            verification_data['verification_score'] = (successful_verifications / total_urls) * 100
        
        # Generate summary
        verification_data['summary'] = self._generate_verification_summary(verification_data)
        
        return verification_data
    
    def _verify_github_profile(self, github_url: str) -> Dict[str, Any]:
        """Extract information from GitHub profile"""
        try:
            # Clean URL
            parsed_url = urlparse(github_url)
            username = parsed_url.path.strip('/').split('/')[0]
            
            # Get profile information
            profile_data = self._get_github_profile_data(username)
            
            # Get repositories information
            repos_data = self._get_github_repos_data(username)
            
            return {
                'username': username,
                'profile': profile_data,
                'repositories': repos_data,
                'activity_summary': self._analyze_github_activity(profile_data, repos_data)
            }
        except Exception as e:
            logger.error(f"GitHub verification failed: {e}")
            return {}
    
    def _get_github_profile_data(self, username: str) -> Dict[str, Any]:
        """Get GitHub profile data via web scraping (GitHub API would be better but requires auth)"""
        try:
            url = f"https://github.com/{username}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            profile_data = {
                'name': '',
                'bio': '',
                'company': '',
                'location': '',
                'public_repos': 0,
                'followers': 0,
                'following': 0
            }
            
            # Extract basic info
            name_elem = soup.find('span', {'class': 'p-name'})
            if name_elem:
                profile_data['name'] = name_elem.get_text(strip=True)
            
            bio_elem = soup.find('div', {'class': 'p-note user-profile-bio'})
            if bio_elem:
                profile_data['bio'] = bio_elem.get_text(strip=True)
            
            # Extract stats
            stats = soup.find_all('span', {'class': 'text-bold color-fg-default'})
            for stat in stats:
                text = stat.get_text(strip=True)
                if text.isdigit():
                    parent_text = stat.parent.get_text(strip=True).lower()
                    if 'repositories' in parent_text or 'repos' in parent_text:
                        profile_data['public_repos'] = int(text)
                    elif 'followers' in parent_text:
                        profile_data['followers'] = int(text)
                    elif 'following' in parent_text:
                        profile_data['following'] = int(text)
            
            return profile_data
        except Exception as e:
            logger.error(f"Failed to get GitHub profile data: {e}")
            return {}
    
    def _get_github_repos_data(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get information about user's repositories"""
        try:
            url = f"https://github.com/{username}?tab=repositories"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            repos = []
            
            repo_items = soup.find_all('div', {'class': 'col-10 col-lg-9 d-inline-block'})[:limit]
            
            for repo_item in repo_items:
                repo_data = {}
                
                # Repository name and link
                name_link = repo_item.find('a', href=True)
                if name_link:
                    repo_data['name'] = name_link.get_text(strip=True)
                    repo_data['url'] = f"https://github.com{name_link['href']}"
                
                # Description
                desc_elem = repo_item.find('p', {'class': 'col-9'})
                if desc_elem:
                    repo_data['description'] = desc_elem.get_text(strip=True)
                
                # Language
                lang_elem = repo_item.find('span', {'itemprop': 'programmingLanguage'})
                if lang_elem:
                    repo_data['language'] = lang_elem.get_text(strip=True)
                
                repos.append(repo_data)
            
            return repos
        except Exception as e:
            logger.error(f"Failed to get GitHub repos data: {e}")
            return []
    
    def _analyze_github_activity(self, profile_data: Dict, repos_data: List[Dict]) -> str:
        """Analyze GitHub activity and generate summary"""
        try:
            summary_parts = []
            
            if profile_data.get('public_repos', 0) > 0:
                summary_parts.append(f"Has {profile_data['public_repos']} public repositories")
            
            if profile_data.get('followers', 0) > 10:
                summary_parts.append(f"Has {profile_data['followers']} followers")
            
            # Analyze programming languages
            languages = {}
            for repo in repos_data:
                lang = repo.get('language')
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1
            
            if languages:
                top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:3]
                lang_list = [lang for lang, count in top_languages]
                summary_parts.append(f"Primary languages: {', '.join(lang_list)}")
            
            # Analyze project types
            project_keywords = ['web', 'api', 'app', 'machine learning', 'ml', 'ai', 'data', 'mobile']
            found_keywords = []
            
            for repo in repos_data:
                desc = repo.get('description', '').lower()
                name = repo.get('name', '').lower()
                for keyword in project_keywords:
                    if keyword in desc or keyword in name:
                        found_keywords.append(keyword)
            
            if found_keywords:
                unique_keywords = list(set(found_keywords))
                summary_parts.append(f"Project types: {', '.join(unique_keywords[:3])}")
            
            return '. '.join(summary_parts) if summary_parts else "Limited GitHub activity found"
        except Exception as e:
            logger.error(f"Failed to analyze GitHub activity: {e}")
            return "Unable to analyze GitHub activity"
    
    def _verify_linkedin_profile(self, linkedin_url: str) -> Dict[str, Any]:
        """Verify LinkedIn profile (limited due to anti-scraping measures)"""
        try:
            # LinkedIn has strong anti-scraping measures, so this is basic
            response = self.session.get(linkedin_url, timeout=10)
            
            if response.status_code != 200:
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to extract basic information
            profile_data = {
                'accessible': True,
                'title': soup.title.string if soup.title else '',
                'summary': 'LinkedIn profile accessible but detailed scraping limited due to platform restrictions'
            }
            
            return profile_data
        except Exception as e:
            logger.error(f"LinkedIn verification failed: {e}")
            return {'accessible': False, 'summary': 'LinkedIn profile not accessible'}
    
    def _verify_portfolio_site(self, portfolio_url: str) -> Dict[str, Any]:
        """Verify portfolio website"""
        try:
            response = self.session.get(portfolio_url, timeout=10)
            
            if response.status_code != 200:
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            portfolio_data = {
                'accessible': True,
                'title': soup.title.string if soup.title else '',
                'technologies': self._extract_technologies_from_portfolio(soup),
                'content_summary': self._analyze_portfolio_content(soup)
            }
            
            return portfolio_data
        except Exception as e:
            logger.error(f"Portfolio verification failed: {e}")
            return {'accessible': False, 'summary': 'Portfolio site not accessible'}
    
    def _extract_technologies_from_portfolio(self, soup: BeautifulSoup) -> List[str]:
        """Extract technology mentions from portfolio"""
        tech_keywords = [
            'react', 'angular', 'vue', 'javascript', 'typescript', 'python', 'java',
            'node.js', 'django', 'flask', 'spring', 'mongodb', 'postgresql', 'mysql',
            'aws', 'azure', 'docker', 'kubernetes', 'git', 'html', 'css', 'sass'
        ]
        
        text_content = soup.get_text().lower()
        found_technologies = []
        
        for tech in tech_keywords:
            if tech in text_content:
                found_technologies.append(tech)
        
        return found_technologies
    
    def _analyze_portfolio_content(self, soup: BeautifulSoup) -> str:
        """Analyze portfolio content for professional indicators"""
        text_content = soup.get_text().lower()
        
        professional_indicators = [
            'experience', 'skills', 'projects', 'portfolio', 'about',
            'contact', 'resume', 'work', 'education', 'achievements'
        ]
        
        found_sections = [indicator for indicator in professional_indicators if indicator in text_content]
        
        if found_sections:
            return f"Professional portfolio with sections: {', '.join(found_sections[:5])}"
        else:
            return "Basic website with limited professional content"
    
    def _generate_verification_summary(self, verification_data: Dict[str, Any]) -> str:
        """Generate overall verification summary"""
        summary_parts = []
        
        if verification_data['github']:
            github_summary = verification_data['github'].get('activity_summary', '')
            if github_summary:
                summary_parts.append(f"GitHub: {github_summary}")
        
        if verification_data['linkedin'] and verification_data['linkedin'].get('accessible'):
            summary_parts.append("LinkedIn: Profile accessible and appears professional")
        
        if verification_data['portfolio'] and verification_data['portfolio'].get('accessible'):
            portfolio_summary = verification_data['portfolio'].get('content_summary', '')
            if portfolio_summary:
                summary_parts.append(f"Portfolio: {portfolio_summary}")
        
        if not summary_parts:
            return "Limited verification data available from provided profiles"
        
        return '. '.join(summary_parts) 
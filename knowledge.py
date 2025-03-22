import wikipedia
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from functools import lru_cache
import time
import traceback
import re
from datetime import datetime, timedelta

from core.errors import KnowledgeRetrievalError

logger = logging.getLogger(__name__)

# Advanced cache with TTL and size limits
class KnowledgeCache:
    def __init__(self, max_size=1000, ttl_seconds=86400):  # 24 hour default TTL
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.access_times = {}  # Track last access for LRU eviction
    
    def get(self, key):
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry["expires"]:
                # Update access time for LRU
                self.access_times[key] = time.time()
                return entry["value"]
            else:
                # Expired entry
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
        return None
    
    def set(self, key, value, ttl=None):
        # Evict if we're at capacity
        if len(self.cache) >= self.max_size:
            self._evict_lru()
            
        ttl = ttl or self.ttl
        self.cache[key] = {
            "value": value,
            "expires": time.time() + ttl
        }
        self.access_times[key] = time.time()
    
    def _evict_lru(self):
        if not self.access_times:
            return
            
        # Find least recently used item
        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
        del self.cache[lru_key]
        del self.access_times[lru_key]
    
    def clear(self):
        self.cache = {}
        self.access_times = {}

# Pre-defined knowledge bases
GENERAL_KNOWLEDGE = {
    # Science and Technology
    "ai": "Artificial Intelligence (AI) refers to systems that can perform tasks requiring human intelligence. This includes learning, reasoning, problem-solving, and understanding natural language. Machine learning, deep learning, and neural networks are key components of modern AI systems. AI applications include virtual assistants, recommendation systems, autonomous vehicles, and medical diagnosis tools.",
    
    "machine learning": "Machine Learning is a subset of AI that gives computers the ability to learn from data without being explicitly programmed. Key techniques include supervised learning (training with labeled data), unsupervised learning (finding patterns in unlabeled data), and reinforcement learning (learning through trial and error). Popular algorithms include decision trees, neural networks, and support vector machines.",
    
    "blockchain": "Blockchain is a distributed ledger technology that maintains a continuously growing list of records (blocks) that are linked and secured using cryptography. Each block contains a timestamp and transaction data, and by design is resistant to modification. Bitcoin and Ethereum are well-known applications of blockchain technology. It enables secure, transparent, and decentralized transactions without requiring a trusted third party.",
    
    "quantum computing": "Quantum computing uses quantum bits or qubits that can exist in multiple states simultaneously, unlike classical bits. This property, called superposition, along with entanglement, allows quantum computers to perform certain calculations exponentially faster than classical computers. Potential applications include cryptography, drug discovery, optimization problems, and simulating quantum systems.",
    
    "python": "Python is a high-level, interpreted programming language known for its readability and versatility. Created by Guido van Rossum and first released in 1991, it's widely used in web development, data science, artificial intelligence, and automation. Python emphasizes code readability with its notable use of significant whitespace and a syntax that allows programmers to express concepts in fewer lines of code.",
    
    "big data": "Big Data refers to extremely large and complex data sets that cannot be effectively processed using traditional data processing applications. The challenges include capture, storage, analysis, search, sharing, transfer, visualization, and privacy. The '3Vs' that characterize big data are volume, velocity, and variety. Technologies like Hadoop, Spark, and NoSQL databases are commonly used to handle big data.",
    
    # Sports
    "cricket": "Cricket is a bat-and-ball game played between two teams of eleven players on a field. It originated in England and is popular in countries like India, Australia, England, Pakistan, and the West Indies. The main formats are Test matches (lasting up to 5 days), One-Day Internationals (50 overs per side), and Twenty20 (20 overs per side). The ICC Cricket World Cup is held every four years.",
    
    "football": "Football (soccer) is a team sport played between two teams of eleven players with a spherical ball. It's the world's most popular sport, played in over 200 countries. Major competitions include the FIFA World Cup, held every four years, and professional leagues like the English Premier League, Spanish La Liga, and German Bundesliga.",
    
    "ipl": "The Indian Premier League (IPL) is a professional Twenty20 cricket league in India. It was founded by the Board of Control for Cricket in India (BCCI) in 2007. Teams represent different Indian cities. The tournament typically runs for 2 months in March-May. Mumbai Indians and Chennai Super Kings are the most successful teams with multiple titles each.",
    
    "nba": "The National Basketball Association (NBA) is the premier professional basketball league in North America, consisting of 30 teams (29 in United States, 1 in Canada). Founded in 1946, the NBA features some of the world's most famous athletes and teams like the Los Angeles Lakers, Boston Celtics, and Chicago Bulls. The NBA season culminates in the NBA Finals, determining the league champion.",
    
    "olympics": "The Olympic Games are an international sports competition held every four years, featuring summer and winter sports competitions with thousands of athletes from around the world. The International Olympic Committee (IOC) organizes the games. The Summer Olympics feature sports like athletics (track and field), swimming, gymnastics, and team sports, while the Winter Olympics include sports like skiing, ice hockey, and figure skating.",
    
    # Entertainment
    "movies": "Movies (films) are visual art forms that tell stories through moving images. The film industry produces thousands of movies annually across genres like action, comedy, drama, science fiction, and documentaries. Major film industries include Hollywood (USA), Bollywood (India), and others worldwide. The Academy Awards (Oscars) are the most prestigious film awards globally.",
    
    "music": "Music is an art form that arranges sounds in time through elements like melody, harmony, rhythm, and timbre. Music spans countless genres including classical, rock, pop, jazz, hip-hop, electronic, and folk traditions from around the world. Digital streaming platforms like Spotify and Apple Music have transformed how music is distributed and consumed in recent years.",
    
    # Health
    "covid-19": "COVID-19 is an infectious disease caused by the SARS-CoV-2 virus, first identified in Wuhan, China in December 2019. It led to a global pandemic with symptoms ranging from mild respiratory issues to severe illness and death. Vaccines have been developed to combat the spread, and various public health measures including social distancing, mask-wearing, and lockdowns were implemented worldwide to control transmission.",
    
    "mental health": "Mental health encompasses emotional, psychological, and social well-being. It affects how people think, feel, and act. Common mental health conditions include depression, anxiety disorders, bipolar disorder, and schizophrenia. Treatment typically involves therapy, medication, or a combination of approaches. There's growing awareness about reducing stigma and improving access to mental health services.",
    
    # Business and Economics
    "cryptocurrency": "Cryptocurrency is a digital or virtual currency that uses cryptography for security and operates on decentralized networks based on blockchain technology. Bitcoin, created in 2009, was the first cryptocurrency. Others include Ethereum, Ripple, and thousands more. Cryptocurrencies are not typically issued by any central authority, making them potentially resistant to government interference or manipulation.",
    
    "stock market": "The stock market is a collection of markets where stocks (pieces of ownership in businesses) are traded. Major stock exchanges include the New York Stock Exchange (NYSE), NASDAQ, and Tokyo Stock Exchange. Stock markets enable companies to raise capital and provide investors opportunities for growth. Stock prices are influenced by factors like company performance, economic indicators, and investor sentiment.",
    
    # Education
    "online learning": "Online learning involves educational courses delivered via the internet, allowing students to learn remotely. It offers flexibility in terms of time and location, making education more accessible. Online learning platforms include Coursera, edX, Khan Academy, and institutional offerings from traditional universities. The COVID-19 pandemic accelerated the adoption of online learning globally.",

    # AI and ML terms
    "neural networks": "Neural networks are computing systems inspired by biological neural networks in animal brains. They consist of interconnected nodes (neurons) that process information by responding to external inputs and transmitting information between each node. Deep learning uses multi-layered neural networks to analyze various factors of data. Applications include image and speech recognition, natural language processing, and more complex decision-making tasks.",
    
    "deep learning": "Deep Learning is a subset of machine learning that uses neural networks with many layers (deep neural networks). It has revolutionized fields like computer vision, natural language processing, and speech recognition. Deep learning excels at automatically discovering patterns in data without manual feature engineering. Frameworks like TensorFlow and PyTorch are commonly used for implementing deep learning models.",
    
    "nlp": "Natural Language Processing (NLP) is a field of AI that focuses on the interaction between computers and human language. It enables computers to read, understand, and generate human language. Applications include machine translation, sentiment analysis, chatbots, voice assistants, and text summarization. Recent advances in deep learning, particularly transformer models like BERT and GPT, have significantly improved NLP capabilities.",
    
    "computer vision": "Computer Vision is a field of AI that enables computers to derive meaningful information from digital images and videos. It involves tasks such as image classification, object detection, segmentation, and tracking. Applications include facial recognition, autonomous vehicles, medical image analysis, and augmented reality. Deep learning, particularly convolutional neural networks (CNNs), has dramatically improved computer vision capabilities.",
    
    "reinforcement learning": "Reinforcement Learning is a type of machine learning where an agent learns by interacting with an environment and receiving rewards or penalties. The agent learns to make decisions by trial and error, maximizing cumulative rewards. It's been successfully applied to game playing (like AlphaGo), robotics, autonomous driving, and resource management. Key algorithms include Q-learning, Deep Q Networks (DQN), and Proximal Policy Optimization (PPO).",
    
    # Additional topics
    "climate change": "Climate change refers to long-term shifts in temperatures and weather patterns, primarily caused by human activities, especially burning fossil fuels. Effects include rising sea levels, extreme weather events, and ecosystem disruption. The Paris Agreement is an international treaty aiming to limit global warming. Mitigation strategies include reducing carbon emissions, developing renewable energy, and improving energy efficiency.",
    
    "renewable energy": "Renewable energy comes from naturally replenishing sources such as sunlight, wind, rain, tides, and geothermal heat. Unlike fossil fuels, renewable energy sources won't deplete over time. Common types include solar power, wind power, hydroelectric power, biomass, and geothermal energy. Renewable energy is crucial for reducing carbon emissions and combating climate change."
}

class WikipediaService:
    """
    Enhanced service for retrieving information from Wikipedia with robust error handling
    """
    def __init__(self, timeout: float = 8.0):
        self.wiki = wikipedia
        self.wiki.set_lang('en')
        self.timeout = timeout  # Default timeout in seconds
        self.cache = KnowledgeCache(max_size=500)
        
    async def search(self, query: str, limit: int = 5) -> List[str]:
        """
        Search Wikipedia for pages matching the query with robust error handling
        """
        if not query or query.strip() == "":
            logger.warning("Empty query provided to Wikipedia search")
            return []
            
        # Clean the query
        cleaned_query = self._clean_query(query)
        
        # Check cache first
        cache_key = f"search_{cleaned_query}_{limit}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for search: {query}")
            return cached_result
            
        try:
            # Use the search function from the wikipedia package with timeout
            logger.info(f"Searching Wikipedia for: {query} (timeout: {self.timeout}s)")
            loop = asyncio.get_event_loop()
            
            # Search for pages with timeout
            start_time = time.time()
            search_results = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: self.wiki.search(cleaned_query, results=limit)),
                timeout=self.timeout
            )
            
            duration = time.time() - start_time
            logger.info(f"Wikipedia search completed in {duration:.2f}s. Results: {search_results}")
            
            # Filter out disambiguation pages and irrelevant results
            filtered_results = []
            for title in search_results:
                if len(filtered_results) >= 3:  # Limit to top 3 relevant results
                    break
                    
                # Skip obvious disambiguation pages
                if "(disambiguation)" in title.lower():
                    continue
                    
                filtered_results.append(title)
            
            # Cache the results
            self.cache.set(cache_key, filtered_results)
            return filtered_results
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout searching Wikipedia for '{query}' after {self.timeout}s")
            return []
            
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    async def get_page_summary(self, title: str, sentences: int = 5) -> Optional[str]:
        """
        Get a detailed summary of a Wikipedia page with robust error handling
        """
        if not title or title.strip() == "":
            logger.warning("Empty title provided to Wikipedia summary")
            return None
                
        # Check cache first
        cache_key = f"summary_{title}_{sentences}"
        cached_summary = self.cache.get(cache_key)
        if cached_summary:
            logger.info(f"Cache hit for summary: {title}")
            return cached_summary
            
        try:
            logger.info(f"Getting Wikipedia summary for: {title} (timeout: {self.timeout}s)")
            loop = asyncio.get_event_loop()
            
            # Get the page summary with timeout
            start_time = time.time()
            
            # First try to get the full page content for better summaries
            try:
                page = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: self.wiki.page(title, auto_suggest=False)),
                    timeout=self.timeout
                )
                
                # Try to extract a more comprehensive summary
                content = page.content
                # Split into paragraphs and take the first few that are long enough
                paragraphs = [p for p in content.split('\n\n') if len(p) > 50]
                
                if paragraphs:
                    # Join first 2-3 paragraphs for a better summary
                    summary = '\n\n'.join(paragraphs[:min(3, len(paragraphs))])
                    # Limit length
                    if len(summary) > 1000:
                        summary = summary[:1000] + "..."
                else:
                    # Fallback to regular summary
                    summary = page.summary
            except:
                # Fallback to standard summary if full page retrieval fails
                summary = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: self.wiki.summary(title, sentences=sentences, auto_suggest=False)),
                    timeout=self.timeout
                )
            
            duration = time.time() - start_time
            logger.info(f"Wikipedia summary completed in {duration:.2f}s. Length: {len(summary)}")
            
            # Clean up the summary
            summary = self._clean_content(summary)
            
            # Cache the result with longer TTL for stable topics
            self.cache.set(cache_key, summary, ttl=7*86400)  # 7 days for stable content
            return summary
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting Wikipedia summary for '{title}' after {self.timeout}s")
            return None
            
        except self.wiki.exceptions.DisambiguationError as e:
            # Handle disambiguation pages by returning the options
            options = e.options[:3]  # Limit to 3 options
            logger.info(f"Wikipedia disambiguation for '{title}'. Options: {options}")
            options_text = ", ".join(options)
            result = f"The term '{title}' could refer to multiple topics including {options_text}. Please specify which one you're interested in."
            
            # Cache with shorter TTL since this is a disambiguation
            self.cache.set(cache_key, result, ttl=86400)  # 1 day
            return result
            
        except self.wiki.exceptions.PageError:
            # Page not found
            logger.info(f"Wikipedia page not found for '{title}'")
            return None
            
        except Exception as e:
            logger.error(f"Error getting Wikipedia summary: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    async def get_knowledge(self, query: str) -> Tuple[str, str]:
        """
        Enhanced function to get knowledge about a topic
        Returns a tuple of (title, information)
        """
        # First search for relevant pages
        search_results = await self.search(query)
        
        # If search failed completely
        if not search_results:
            return ("", "")
        
        # Try to get summaries for the top results in parallel
        summary_tasks = [self.get_page_summary(title) for title in search_results[:2]]
        summaries = await asyncio.gather(*summary_tasks, return_exceptions=True)
        
        # Find the best summary
        best_title, best_summary = "", ""
        
        for i, summary in enumerate(summaries):
            if isinstance(summary, Exception):
                continue
                
            if summary and not best_summary:
                best_title = search_results[i]
                best_summary = summary
                break
        
        return (best_title, best_summary)
        
    def _clean_query(self, query: str) -> str:
        """
        Clean and normalize a query for better search results
        """
        # Remove common question words and punctuation
        query = re.sub(r'^(what is|who is|tell me about|how does|where is|when did|why does|can you explain)\s+', '', query.lower())
        query = re.sub(r'[^\w\s]', '', query)
        # Remove extra whitespace
        query = ' '.join(query.split())
        return query
        
    def _clean_content(self, content: str) -> str:
        """
        Clean retrieved content for better presentation
        """
        # Remove reference markers [1], [2], etc.
        content = re.sub(r'\[\d+\]', '', content)
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        # Remove any Wikipedia editing notes or special markers
        content = re.sub(r'==.*?==', '', content)
        # Clean up any remaining artifacts
        content = content.strip()
        return content

class KnowledgeBase:
    """
    Enhanced knowledge base with multiple sources and semantic search capabilities
    """
    def __init__(self):
        self.fallback_knowledge = GENERAL_KNOWLEDGE
        self.cache = KnowledgeCache(max_size=200)
    
    async def search(self, query: str) -> Tuple[str, str]:
        """
        Search the knowledge base for information matching the query
        """
        # Normalize the query for better matching
        normalized_query = query.lower()
        
        # Check cache
        cache_key = f"kb_search_{normalized_query[:50]}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
            
        # Search for exact or partial matches in the knowledge base
        best_match, best_info = "", ""
        best_score = 0
        
        for key, info in self.fallback_knowledge.items():
            # Calculate a simple relevance score
            score = self._calculate_relevance(normalized_query, key)
            
            if score > best_score:
                best_score = score
                best_match = key.title()
                best_info = info
        
        # Only return if we have a decent match
        if best_score >= 0.3:
            result = (best_match, best_info)
            # Cache the result
            self.cache.set(cache_key, result)
            return result
            
        return ("", "")
    
    def _calculate_relevance(self, query: str, key: str) -> float:
        """
        Calculate a simple relevance score between query and knowledge base key
        """
        # Exact match gets highest score
        if query == key:
            return 1.0
            
        # Contains whole key as a word
        if f" {key} " in f" {query} ":
            return 0.9
            
        # Key is at the start
        if query.startswith(key):
            return 0.8
            
        # Query contains the key
        if key in query:
            return 0.7
            
        # Key contains the query
        if query in key:
            return 0.5
            
        # Check for word overlap
        query_words = set(query.split())
        key_words = set(key.split())
        
        overlap = query_words.intersection(key_words)
        if overlap:
            return 0.3 * (len(overlap) / max(len(query_words), len(key_words)))
            
        return 0.0

@lru_cache()
def get_wikipedia_service() -> WikipediaService:
    """
    Get a cached Wikipedia service
    """
    return WikipediaService()

@lru_cache()
def get_knowledge_base() -> KnowledgeBase:
    """
    Get a cached knowledge base
    """
    return KnowledgeBase()
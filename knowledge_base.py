import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)

# This module provides additional knowledge sources beyond Wikipedia
# It can be extended with more specialized knowledge bases

class TopicKnowledgeBase:
    """
    Knowledge base for common topics with detailed information
    """
    def __init__(self):
        # Load specialized topic knowledge
        self.topics = {
            # Technology topics
            "artificial intelligence": self._get_ai_knowledge(),
            "machine learning": self._get_ml_knowledge(),
            "programming": self._get_programming_knowledge(),
            "data science": self._get_data_science_knowledge(),
            "blockchain": self._get_blockchain_knowledge(),
            "cybersecurity": self._get_cybersecurity_knowledge(),
            
            # Business topics
            "startups": self._get_startup_knowledge(),
            "marketing": self._get_marketing_knowledge(),
            "finance": self._get_finance_knowledge(),
            
            # Science topics
            "physics": self._get_physics_knowledge(),
            "biology": self._get_biology_knowledge(),
            "chemistry": self._get_chemistry_knowledge(),
            
            # Health topics
            "nutrition": self._get_nutrition_knowledge(),
            "fitness": self._get_fitness_knowledge(),
            "mental health": self._get_mental_health_knowledge(),
            
            # Other topics
            "climate change": self._get_climate_knowledge(),
            "education": self._get_education_knowledge(),
        }
        
    async def search(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Search the specialized knowledge base for the query
        Returns a tuple of (topic_title, knowledge_dict)
        """
        query_lower = query.lower()
        
        # Direct topic match
        for topic, knowledge in self.topics.items():
            if topic in query_lower:
                return topic.title(), knowledge.get("overview", "")
        
        # Keyword match
        for topic, knowledge in self.topics.items():
            keywords = knowledge.get("keywords", [])
            for keyword in keywords:
                if keyword in query_lower:
                    return topic.title(), knowledge.get("overview", "")
        
        return "", ""
    
    # Knowledge getters for different topics
    def _get_ai_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Artificial Intelligence (AI) refers to computer systems designed to perform tasks that normally "
                "require human intelligence. Modern AI is based primarily on machine learning techniques, especially "
                "deep learning. Key areas include natural language processing, computer vision, robotics, and "
                "autonomous systems. AI technologies are used in virtual assistants, recommendation systems, "
                "autonomous vehicles, medical diagnosis, and many other applications. AI development raises "
                "important ethical questions about bias, privacy, job displacement, and safety."
            ),
            "keywords": ["ai", "neural networks", "deep learning", "nlp", "computer vision", "chatbot", "machine intelligence"],
            "subtopics": {
                "deep learning": "A subset of machine learning using neural networks with many layers.",
                "nlp": "Natural Language Processing focuses on interactions between computers and human language.",
                "ethics": "Considers fairness, transparency, privacy, and safety concerns in AI systems."
            }
        }
    
    def _get_ml_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Machine Learning (ML) is a subset of AI that focuses on building systems that learn from data. "
                "The three main types are supervised learning (training with labeled data), unsupervised learning "
                "(finding patterns in unlabeled data), and reinforcement learning (learning through trial and error). "
                "Popular algorithms include linear regression, decision trees, random forests, support vector machines, "
                "and neural networks. ML is used in recommendation systems, fraud detection, image recognition, "
                "predictive maintenance, and many other applications."
            ),
            "keywords": ["supervised learning", "unsupervised learning", "reinforcement learning", "neural networks", "algorithms", "data mining"],
            "subtopics": {
                "supervised learning": "Learning from labeled training data to make predictions or decisions.",
                "neural networks": "Computing systems inspired by biological neural networks in animal brains.",
                "decision trees": "Tree-like models of decisions and their possible consequences."
            }
        }
    
    def _get_programming_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Programming involves creating instructions for computers using programming languages. Popular languages "
                "include Python, JavaScript, Java, C++, and many others, each with different strengths and use cases. "
                "Programming paradigms include procedural, object-oriented, functional, and declarative programming. "
                "Software development often follows methodologies like Agile or DevOps and uses tools like version control "
                "systems (Git), integrated development environments (IDEs), and continuous integration/continuous "
                "deployment (CI/CD) pipelines."
            ),
            "keywords": ["coding", "software development", "python", "javascript", "java", "programming languages", "algorithms"],
            "subtopics": {
                "python": "High-level, interpreted language known for readability and versatility.",
                "web development": "Creating applications that run in web browsers using HTML, CSS, and JavaScript.",
                "version control": "Systems like Git for tracking and managing changes to code."
            }
        }
    
    def _get_data_science_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Data Science is an interdisciplinary field that uses scientific methods, processes, algorithms, and systems "
                "to extract knowledge and insights from structured and unstructured data. It combines aspects of statistics, "
                "mathematics, computer science, and domain expertise. Key components include data collection, cleaning, and "
                "preprocessing; exploratory data analysis; feature engineering; model building and evaluation; and data "
                "visualization. Common tools include Python (with libraries like Pandas, NumPy, scikit-learn), R, SQL, and "
                "visualization tools like Tableau and PowerBI."
            ),
            "keywords": ["data analysis", "statistics", "big data", "data mining", "data visualization", "predictive analytics"],
            "subtopics": {
                "data cleaning": "Process of detecting and correcting inaccurate records in a dataset.",
                "exploratory data analysis": "Analyzing data sets to summarize their main characteristics.",
                "data visualization": "Graphical representation of information and data."
            }
        }
    
    def _get_blockchain_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Blockchain is a distributed ledger technology that maintains a continuously growing list of records (blocks) "
                "that are linked and secured using cryptography. Each block contains a timestamp and transaction data, and "
                "by design is resistant to modification. Key features include decentralization, transparency, immutability, "
                "and security. Blockchain is the underlying technology for cryptocurrencies like Bitcoin and Ethereum, but "
                "has many other applications including supply chain management, digital identity, voting systems, and "
                "smart contracts. Different consensus mechanisms include Proof of Work, Proof of Stake, and others."
            ),
            "keywords": ["cryptocurrency", "bitcoin", "ethereum", "distributed ledger", "consensus", "smart contracts"],
            "subtopics": {
                "cryptocurrency": "Digital or virtual currency that uses cryptography for security.",
                "smart contracts": "Self-executing contracts with the terms directly written into code.",
                "consensus mechanisms": "Methods for achieving agreement on a single data value among distributed systems."
            }
        }
    
    def _get_cybersecurity_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Cybersecurity involves protecting systems, networks, and programs from digital attacks. These attacks "
                "typically aim to access, change, or destroy sensitive information; extort money; or interrupt normal "
                "business processes. Key areas include network security, application security, information security, "
                "operational security, and end-user education. Common threats include malware, phishing, man-in-the-middle "
                "attacks, denial-of-service attacks, SQL injection, and zero-day exploits. Defense strategies include "
                "firewalls, antivirus software, intrusion detection systems, encryption, and regular security assessments."
            ),
            "keywords": ["information security", "network security", "hacking", "malware", "encryption", "threats", "vulnerabilities"],
            "subtopics": {
                "phishing": "Fraudulent attempts to obtain sensitive information by disguising as a trustworthy entity.",
                "malware": "Software designed to damage, disable, or gain unauthorized access to computer systems.",
                "encryption": "Process of encoding information to prevent unauthorized access."
            }
        }
    
    def _get_startup_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Startups are newly established businesses aiming to develop a unique product or service and bring it to market. "
                "They typically start with funding from founders, family, and friends, then seek additional capital from "
                "angel investors, venture capital firms, or crowdfunding. The startup lifecycle includes ideation, validation, "
                "growth, and either scaling, acquisition, or failure. Key challenges include securing funding, product-market fit, "
                "team building, marketing, and scaling operations. Startup ecosystems include Silicon Valley, New York, London, "
                "Berlin, Tel Aviv, and emerging hubs in Asia and Africa."
            ),
            "keywords": ["entrepreneurship", "venture capital", "funding", "product-market fit", "scaling", "incubator", "accelerator"],
            "subtopics": {
                "funding rounds": "Series of investments to fund growth, from seed to Series A, B, C, etc.",
                "minimum viable product": "Version of a product with just enough features to satisfy early customers.",
                "pivot": "Structured course correction designed to test a new hypothesis about a product or business model."
            }
        }
    
    def _get_marketing_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Marketing involves activities that promote and sell products or services, including market research, "
                "advertising, public relations, and sales. Traditional marketing includes print, radio, and TV advertising, "
                "while digital marketing encompasses search engine optimization, content marketing, social media marketing, "
                "email marketing, and pay-per-click advertising. Key concepts include the marketing mix (product, price, "
                "place, promotion), customer segmentation, brand positioning, customer journey, and metrics like customer "
                "acquisition cost, lifetime value, and return on investment."
            ),
            "keywords": ["advertising", "branding", "digital marketing", "seo", "social media", "content marketing", "analytics"],
            "subtopics": {
                "digital marketing": "Promotion of products/services using digital channels and technologies.",
                "content marketing": "Creating and sharing valuable content to attract and retain customers.",
                "search engine optimization": "Process of improving a website to increase visibility in search engines."
            }
        }
    
    def _get_finance_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Finance is the study and management of money, investments, and other financial instruments. Personal finance "
                "involves individual budgeting, saving, investing, and planning for retirement. Corporate finance deals with "
                "funding sources, capital structure, and financial decisions within businesses. Investment involves allocating "
                "resources with the expectation of generating income or profit, through vehicles like stocks, bonds, real estate, "
                "and alternative investments. Key concepts include risk and return, time value of money, diversification, "
                "compound interest, and market efficiency."
            ),
            "keywords": ["investing", "stocks", "bonds", "budgeting", "retirement", "taxes", "banking", "wealth management"],
            "subtopics": {
                "stock market": "Collection of markets where stocks are traded.",
                "portfolio management": "Art and science of selecting and overseeing a group of investments.",
                "financial planning": "Process of meeting financial goals through proper management of finances."
            }
        }
    
    def _get_physics_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Physics is the natural science that studies matter, its motion and behavior through space and time, and the "
                "related entities of energy and force. Major branches include classical mechanics, thermodynamics, electromagnetism, "
                "relativity, quantum mechanics, nuclear physics, particle physics, and astrophysics. Physics forms the foundation "
                "for many other sciences and has applications in engineering, medicine, electronics, material science, and many "
                "other fields. Key concepts include Newton's laws of motion, conservation laws, the laws of thermodynamics, "
                "Maxwell's equations, and the theories of relativity and quantum mechanics."
            ),
            "keywords": ["mechanics", "relativity", "quantum physics", "thermodynamics", "electromagnetism", "particle physics"],
            "subtopics": {
                "quantum mechanics": "Theory describing nature at the smallest scales of energy levels of atoms and subatomic particles.",
                "relativity": "Einstein's theories describing the relationship between space, time, gravity, and energy.",
                "thermodynamics": "Branch dealing with heat and temperature and their relation to energy, work, and properties of matter."
            }
        }
    
    def _get_biology_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Biology is the scientific study of life and living organisms, including their physical structure, chemical "
                "processes, molecular interactions, physiological mechanisms, development, and evolution. Major branches include "
                "molecular biology, cellular biology, physiology, genetics, ecology, evolutionary biology, and microbiology. "
                "Modern biology is a vast and eclectic field, composed of many specialized disciplines. Key concepts include "
                "cell theory, evolution, gene expression, homeostasis, and taxonomy. Biology has applications in medicine, "
                "agriculture, conservation, and biotechnology."
            ),
            "keywords": ["genetics", "evolution", "ecology", "cells", "organisms", "dna", "microbiology", "botany", "zoology"],
            "subtopics": {
                "genetics": "Study of genes, genetic variation, and heredity in organisms.",
                "ecology": "Study of interactions among organisms and their environment.",
                "evolutionary biology": "Study of the processes that have transformed life on Earth."
            }
        }
    
    def _get_chemistry_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Chemistry is the scientific study of the properties, composition, and structure of matter, the changes it "
                "undergoes during chemical reactions, and the energy accompanying these reactions. Major branches include "
                "organic chemistry, inorganic chemistry, physical chemistry, analytical chemistry, and biochemistry. Key "
                "concepts include atoms, molecules, the periodic table, chemical bonds, reactions, and equilibria. Chemistry "
                "has applications in materials science, pharmaceuticals, energy production, environmental science, and "
                "virtually all manufacturing industries."
            ),
            "keywords": ["organic chemistry", "inorganic chemistry", "biochemistry", "elements", "compounds", "reactions", "periodic table"],
            "subtopics": {
                "organic chemistry": "Study of carbon-containing compounds.",
                "chemical reactions": "Processes that lead to the transformation of one set of chemical substances to another.",
                "periodic table": "Tabular arrangement of chemical elements organized by atomic number, electron configuration, and chemical properties."
            }
        }
    
    def _get_nutrition_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Nutrition is the science that interprets the interaction of nutrients and other substances in food in relation "
                "to health and disease. Essential nutrients include proteins, fats, carbohydrates, vitamins, minerals, and water. "
                "Proper nutrition involves consuming a balanced diet that provides necessary nutrients for bodily functions, "
                "growth, and health maintenance. Dietary needs vary based on age, gender, activity level, and health status. "
                "Nutrition plays a role in preventing and managing conditions like obesity, diabetes, cardiovascular disease, "
                "and certain cancers."
            ),
            "keywords": ["diet", "proteins", "carbohydrates", "fats", "vitamins", "minerals", "macronutrients", "micronutrients"],
            "subtopics": {
                "macronutrients": "Nutrients required in large amounts: proteins, carbohydrates, and fats.",
                "micronutrients": "Vitamins and minerals required in small quantities.",
                "balanced diet": "Diet that contains appropriate amounts of all nutrients necessary for health."
            }
        }
    
    def _get_fitness_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Fitness refers to the state of being physically healthy and strong, typically achieved through exercise, "
                "proper nutrition, and adequate rest. Components of fitness include cardiovascular endurance, muscular strength, "
                "muscular endurance, flexibility, and body composition. Exercise types include aerobic (cardio), strength training, "
                "flexibility training, and balance exercises. Regular physical activity has numerous health benefits, including "
                "reduced risk of chronic diseases, improved mental health, better sleep, and enhanced quality of life. Fitness "
                "recommendations generally include at least 150 minutes of moderate activity or 75 minutes of vigorous activity "
                "per week, plus strength training twice weekly."
            ),
            "keywords": ["exercise", "workout", "strength training", "cardio", "endurance", "flexibility", "health", "wellness"],
            "subtopics": {
                "cardiovascular exercise": "Activities that increase heart rate and breathing to improve heart and lung fitness.",
                "strength training": "Exercise using resistance to build muscle strength, size, and endurance.",
                "HIIT": "High-Intensity Interval Training alternating short periods of intense exercise with less intense recovery periods."
            }
        }
    
    def _get_mental_health_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Mental health encompasses emotional, psychological, and social well-being, affecting how people think, feel, "
                "and act. It influences how individuals handle stress, relate to others, and make choices. Mental health "
                "conditions include depression, anxiety disorders, bipolar disorder, schizophrenia, eating disorders, and "
                "addictive behaviors. Treatment approaches include psychotherapy, medication, lifestyle changes, and social "
                "support. Promoting mental well-being involves reducing stigma, increasing awareness, ensuring access to care, "
                "and supporting practices like regular exercise, adequate sleep, stress management, meaningful social connections, "
                "and mindfulness."
            ),
            "keywords": ["psychology", "therapy", "depression", "anxiety", "stress", "mindfulness", "self-care", "counseling"],
            "subtopics": {
                "depression": "Mood disorder causing persistent feelings of sadness and loss of interest.",
                "anxiety disorders": "Conditions characterized by excessive worry, fear, and related behavioral disturbances.",
                "mindfulness": "Psychological process of purposely bringing attention to experiences in the present moment."
            }
        }
    
    def _get_climate_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Climate change refers to long-term shifts in temperatures and weather patterns, primarily caused by human "
                "activities, especially burning fossil fuels. These activities release greenhouse gases like carbon dioxide and "
                "methane, which trap heat in the Earth's atmosphere. Consequences include rising global temperatures, melting "
                "ice caps and glaciers, rising sea levels, more frequent and severe weather events, and ecosystem disruption. "
                "Addressing climate change involves mitigation (reducing emissions through renewable energy, energy efficiency, "
                "and sustainable practices) and adaptation (preparing for unavoidable impacts). International efforts include "
                "the Paris Agreement, which aims to limit global warming to well below 2°C above pre-industrial levels."
            ),
            "keywords": ["global warming", "greenhouse gases", "carbon emissions", "renewable energy", "sustainability", "paris agreement"],
            "subtopics": {
                "greenhouse effect": "Process by which radiation from a planet's atmosphere warms the planet's surface.",
                "renewable energy": "Energy from sources that are naturally replenished, like sunlight, wind, and geothermal heat.",
                "carbon footprint": "Total greenhouse gas emissions caused directly and indirectly by an individual, organization, or product."
            }
        }
    
    def _get_education_knowledge(self) -> Dict[str, Any]:
        return {
            "overview": (
                "Education is the process of facilitating learning, or the acquisition of knowledge, skills, values, morals, "
                "beliefs, and habits. Educational methods include teaching, training, storytelling, discussion, and directed "
                "research. Education frequently takes place under the guidance of educators, but learners can also educate "
                "themselves. Education can take place in formal settings like schools and universities or informal settings. "
                "Educational approaches include student-centered learning, inquiry-based learning, project-based learning, and "
                "competency-based education. Educational technology and online learning have expanded access to education globally."
            ),
            "keywords": ["learning", "teaching", "schools", "curriculum", "pedagogy", "e-learning", "universities", "academic"],
            "subtopics": {
                "online education": "Education that takes place over the Internet.",
                "lifelong learning": "Ongoing, voluntary, and self-motivated pursuit of knowledge throughout life.",
                "early childhood education": "Education of children from birth to age eight, designed to promote school readiness."
            }
        }
    

@lru_cache()
def get_topic_knowledge_base() -> TopicKnowledgeBase:
    """
    Get a cached topic knowledge base instance
    """
    return TopicKnowledgeBase()
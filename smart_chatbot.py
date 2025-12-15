# Save as: smart_chatbot.py
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import re
import random
from datetime import datetime
import urllib.parse

class SmartChatBot:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.conversation_history = []
        self.user_name = None
        
    def is_name_message(self, text):
        """Check if message contains name information"""
        text_lower = text.lower()
        name_patterns = ['my name is', 'i am', 'i\'m', 'call me']
        return any(pattern in text_lower for pattern in name_patterns)
    
    def extract_name(self, text):
        """Extract name from message"""
        text_lower = text.lower()
        
        name_patterns = ['my name is', 'i am', 'i\'m', 'call me']
        for pattern in name_patterns:
            if pattern in text_lower:
                try:
                    rest = text_lower.split(pattern)[1].strip()
                    name = rest.split()[0].title()
                    return name
                except:
                    continue
        return None
    
    def search_google(self, query, num_results=3):
        """Search Google and extract information"""
        try:
            print(f"🔍 Googling: {query}")
            
            # Get Google search results
            search_results = list(search(query, num_results=num_results, lang='en'))
            
            if not search_results:
                return None
            
            # Try each result
            for url in search_results[:2]:
                try:
                    # Fetch page content
                    response = requests.get(url, headers=self.headers, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Remove unwanted elements
                    for element in soup(['script', 'style', 'nav', 'footer', 'aside']):
                        element.decompose()
                    
                    # Get text
                    text = soup.get_text()
                    
                    # Clean text
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    
                    if len(text) > 200:
                        # Extract relevant sentences
                        sentences = re.split(r'(?<=[.!?])\s+', text)
                        
                        # Find sentences with query words
                        query_words = query.lower().split()
                        relevant = []
                        
                        for sentence in sentences:
                            sentence_lower = sentence.lower()
                            if any(word in sentence_lower for word in query_words):
                                if len(sentence) > 20:
                                    relevant.append(sentence)
                            
                            if len(relevant) >= 4:
                                break
                        
                        if relevant:
                            answer = ' '.join(relevant)
                            return {
                                'answer': answer[:800] + '...' if len(answer) > 800 else answer,
                                'source': url,
                                'type': 'google'
                            }
                    
                except Exception as e:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Google search error: {e}")
            return None
    
    def search_wikipedia_api(self, query):
        """Search Wikipedia using API"""
        try:
            print(f"📚 Searching Wikipedia: {query}")
            
            # Clean query
            clean_query = urllib.parse.quote(query.replace(' ', '_'))
            
            # Wikipedia API
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_query}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'extract' in data and data['extract']:
                    return {
                        'answer': data['extract'],
                        'source': data.get('title', 'Wikipedia'),
                        'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                        'type': 'wikipedia'
                    }
            
            # Try search if direct page doesn't exist
            search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(query)}&limit=3&format=json"
            search_response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                
                if len(search_data) >= 3 and search_data[1]:
                    # Try first result
                    first_result = search_data[1][0]
                    page_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(first_result.replace(' ', '_'))}"
                    
                    page_response = requests.get(page_url, headers=self.headers, timeout=10)
                    if page_response.status_code == 200:
                        page_data = page_response.json()
                        
                        if 'extract' in page_data and page_data['extract']:
                            return {
                                'answer': page_data['extract'],
                                'source': page_data.get('title', first_result),
                                'url': page_data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                                'type': 'wikipedia'
                            }
            
            return None
            
        except Exception as e:
            print(f"Wikipedia error: {e}")
            return None
    
    def get_answer(self, query):
        """Get answer from multiple sources"""
        # Try Wikipedia first
        wikipedia_result = self.search_wikipedia_api(query)
        if wikipedia_result:
            return wikipedia_result
        
        # Then try Google
        google_result = self.search_google(query)
        if google_result:
            return google_result
        
        return None
    
    def format_response(self, result, query):
        """Format the response"""
        if not result:
            return self.get_fallback_response(query)
        
        answer = result['answer']
        source = result.get('source', 'Search result')
        url = result.get('url', '')
        
        # Clean answer
        answer = re.sub(r'\s+', ' ', answer).strip()
        
        # Format
        response = f"📚 **About {query}:**\n\n{answer}"
        
        # Add source
        if url:
            if 'wikipedia' in url.lower():
                response += f"\n\n🔗 **Source:** [Wikipedia - {source}]({url})"
            else:
                response += f"\n\n🔗 **Source:** [{source}]({url})"
        else:
            response += f"\n\n🔗 *Information from {source}*"
        
        return response
    
    def get_fallback_response(self, query):
        """Fallback with suggestions"""
        common_topics = [
            "Artificial Intelligence", "Machine Learning", "Quantum Computing",
            "Albert Einstein", "Leonardo da Vinci", "Marie Curie",
            "Solar System", "Black Holes", "Climate Change",
            "Ancient Egypt", "World War II", "Roman Empire",
            "Human Brain", "DNA", "Photosynthesis"
        ]
        
        suggestions = random.sample(common_topics, 3)
        suggestion_text = "\n• " + "\n• ".join(suggestions)
        
        return f"I couldn't find information about '{query}'. Try these topics:{suggestion_text}\n\n💡 **Tip:** Be specific and check spelling!"
    
    def handle_general_conversation(self, user_input):
        """Handle general chat"""
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ['hello', 'hi', 'hey']):
            return random.choice([
                "Hello! 👋 Ask me anything!",
                "Hi there! 😊 What would you like to know?",
                "Hey! Ready to help!"
            ])
        
        elif any(word in user_lower for word in ['bye', 'goodbye']):
            return "Goodbye! 👋"
        
        elif 'thank' in user_lower:
            return "You're welcome! 😊"
        
        elif any(word in user_lower for word in ['your name', 'who are you']):
            return "I'm SmartChatBot! 🤖"
        
        elif 'time' in user_lower:
            return f"⏰ {datetime.now().strftime('%I:%M %p')}"
        
        elif 'date' in user_lower:
            return f"📅 {datetime.now().strftime('%A, %B %d, %Y')}"
        
        elif 'help' in user_lower:
            return "Ask me questions like: 'What is AI?', 'Who was Einstein?', 'Explain quantum physics'"
        
        elif 'fact' in user_lower:
            facts = [
                "🧠 Your brain generates enough electricity to power a small light bulb!",
                "🌌 There are more stars than grains of sand on Earth!",
                "🐜 Ants never sleep!",
                "💧 71% of Earth is water, but only 2.5% is freshwater!"
            ]
            return random.choice(facts)
        
        elif 'joke' in user_lower:
            jokes = [
                "😂 Why don't scientists trust atoms? Because they make up everything!",
                "🐻 What do you call a bear with no teeth? A gummy bear!"
            ]
            return random.choice(jokes)
        
        if len(user_input.split()) <= 2:
            return "Ask me a specific question! 😊"
        
        return None
    
    def extract_query(self, text):
        """Extract search query"""
        text_lower = text.lower().strip().replace('?', '')
        
        patterns = [
            r'what is (.*)',
            r'who is (.*)',
            r'tell me about (.*)',
            r'explain (.*)',
            r'what are (.*)',
            r'how does (.*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                query = match.group(1).strip()
                query = re.sub(r'^(the|a|an|about)\s+', '', query)
                return query.title()
        
        return text_lower.title()
    
    # ADD THIS MISSING METHOD:
    def process_message(self, user_input):
        """Main processing method"""
        user_input = user_input.strip()
        
        if not user_input:
            return "Please type a question!"
        
        # General conversation
        general_response = self.handle_general_conversation(user_input)
        if general_response:
            return general_response
        
        # Extract query
        query = self.extract_query(user_input)
        
        if not query:
            return "I'm not sure what you're asking. Try being more specific!"
        
        # Get answer
        result = self.get_answer(query)
        response = self.format_response(result, query)
        
        # Store history
        self.conversation_history.append({
            'user': user_input,
            'bot': response,
            'timestamp': datetime.now().strftime("%H:%M")
        })
        
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
        
        return response

# Test
if __name__ == "__main__":
    bot = SmartChatBot()
    
    print("🤖 SmartChatBot")
    print("=" * 50)
    
    questions = [
        "What is artificial intelligence?",
        "Who was Albert Einstein?",
        "Tell me about the solar system",
        "Hello"
    ]
    
    for q in questions:
        print(f"\nYou: {q}")
        print(f"Bot: {bot.process_message(q)[:150]}...")
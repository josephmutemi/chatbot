# Save as: chatbot_app.py
from flask import Flask, render_template, request, jsonify, session
import json
import os
from datetime import datetime
# from wikipedia_chatbot import WikipediaChatBot  # Import our new Wikipedia chatbot
# from ai_chatbot import AIChatBot 
from smart_chatbot import SmartChatBot

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this for production

# Initialize Wikipedia chatbot
# bot = WikipediaChatBot()
bot = SmartChatBot()

# User data file
USER_DATA_FILE = 'users_data.json'

def load_user_data(user_id):
    """Load user data from file"""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return data.get(user_id, {})
            except:
                return {}
    return {}

def save_user_data(user_id, user_data):
    """Save user data to file"""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                all_data = json.load(f)
            except:
                all_data = {}
    else:
        all_data = {}
    
    all_data[user_id] = user_data
    
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

@app.route('/')
def home():
    """Render the main chat page"""
    # Initialize session if not exists
    if 'user_id' not in session:
        import uuid
        session['user_id'] = str(uuid.uuid4())
        session['username'] = None
    
    # Load user data
    user_data = load_user_data(session['user_id'])
    if not user_data:
        user_data = {
            'username': None,
            'chat_history': [],
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_user_data(session['user_id'], user_data)
    
    # Set username if available
    if user_data.get('username'):
        session['username'] = user_data['username']
        bot.user_name = user_data['username']  # Pass username to bot
    
    return render_template('index.html', username=session['username'])

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        user_message = request.json.get('message', '').strip()
        user_id = session.get('user_id')
        
        if not user_message:
            return jsonify({'error': 'Empty message'})
        
        # Load user data
        user_data = load_user_data(user_id)
        
        # Check if message is setting a name
        if bot.is_name_message(user_message) and not user_data.get('username'):
            # Extract name from message
            name = bot.extract_name(user_message)
            if name:
                user_data['username'] = name
                session['username'] = name
                bot.user_name = name
                save_user_data(user_id, user_data)
                
                # Create welcome response
                bot_response = f"Nice to meet you, {name}! 😊 I'm your Wikipedia-powered chatbot. Ask me anything!"
                
                # Save to chat history
                timestamp = datetime.now().strftime("%H:%M")
                chat_entry = {
                    'timestamp': timestamp,
                    'user': user_message,
                    'bot': bot_response,
                    'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                user_data['chat_history'] = user_data.get('chat_history', [])
                user_data['chat_history'].append(chat_entry)
                save_user_data(user_id, user_data)
                
                return jsonify({
                    'response': bot_response,
                    'username': name
                })
        
        # Process message through Wikipedia chatbot
        bot_response = bot.process_message(user_message)
        
        # Save to chat history
        timestamp = datetime.now().strftime("%H:%M")
        chat_entry = {
            'timestamp': timestamp,
            'user': user_message,
            'bot': bot_response,
            'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        user_data['chat_history'] = user_data.get('chat_history', [])
        user_data['chat_history'].append(chat_entry)
        
        # Keep only last 100 messages
        if len(user_data['chat_history']) > 100:
            user_data['chat_history'] = user_data['chat_history'][-100:]
        
        save_user_data(user_id, user_data)
        
        # Update bot's user name if we have one
        if user_data.get('username'):
            bot.user_name = user_data['username']
        
        return jsonify({
            'response': bot_response,
            'username': session.get('username')
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error',
            'response': "Sorry, I encountered an error. Please try again! 😊"
        })

@app.route('/history', methods=['GET'])
def get_history():
    """Get chat history"""
    user_id = session.get('user_id')
    if user_id:
        user_data = load_user_data(user_id)
        return jsonify({'history': user_data.get('chat_history', [])})
    return jsonify({'history': []})

@app.route('/clear', methods=['POST'])
def clear_history():
    """Clear chat history"""
    user_id = session.get('user_id')
    if user_id:
        user_data = load_user_data(user_id)
        user_data['chat_history'] = []
        save_user_data(user_id, user_data)
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/update_username', methods=['POST'])
def update_username():
    """Update username"""
    try:
        username = request.json.get('username', '').strip()
        user_id = session.get('user_id')
        
        if username and user_id:
            user_data = load_user_data(user_id)
            user_data['username'] = username
            session['username'] = username
            bot.user_name = username
            save_user_data(user_id, user_data)
            
            bot_response = f"Nice to meet you, {username}! 😊 I'm your Wikipedia-powered chatbot. Ask me anything!"
            
            # Add welcome message to history
            timestamp = datetime.now().strftime("%H:%M")
            chat_entry = {
                'timestamp': timestamp,
                'user': f"My name is {username}",
                'bot': bot_response,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            user_data['chat_history'] = user_data.get('chat_history', [])
            user_data['chat_history'].append(chat_entry)
            save_user_data(user_id, user_data)
            
            return jsonify({
                'success': True,
                'username': username,
                'response': bot_response
            })
        
        return jsonify({'success': False, 'error': 'Invalid username'})
        
    except Exception as e:
        print(f"Error updating username: {e}")
        return jsonify({'success': False, 'error': 'Internal error'})

@app.route('/quick_actions', methods=['POST'])
def quick_actions():
    """Handle quick action buttons"""
    action = request.json.get('action', '')
    user_id = session.get('user_id')
    user_data = load_user_data(user_id) if user_id else {}
    username = user_data.get('username')
    
    responses = {
        'time': f"⏰ The current time is: **{datetime.now().strftime('%I:%M %p')}**",
        'date': f"📅 Today is: **{datetime.now().strftime('%A, %B %d, %Y')}**",
        'joke': "😂 **Joke of the day:** Why don't scientists trust atoms? Because they make up everything! 🤓",
        'weather': "🌤️ I'm not connected to live weather, but I hope it's beautiful where you are! 😊",
        'help': f"""
🤖 **I'm Wikipedia ChatBot - Your Personal Research Assistant!**

📚 **What I can do:**
• Answer questions about **ANY topic** using Wikipedia
• Provide information on **science, history, geography, people, events**
• Explain **concepts and terminology**
• Share **facts and detailed explanations**

💡 **How to use me:**
Just ask questions like:
• "What is artificial intelligence?"
• "Who was Albert Einstein?"
• "Tell me about the Roman Empire"
• "Explain how photosynthesis works"
• "What are black holes?"

{f'Nice chatting with you, {username}! 😊' if username else 'Ask me anything! 😊'}
"""
    }
    
    response = responses.get(action, "I'm not sure what you want me to do. Try asking differently! 😊")
    return jsonify({'response': response})

@app.route('/search', methods=['POST'])
def search_topic():
    """Direct search endpoint for Wikipedia"""
    try:
        topic = request.json.get('topic', '').strip()
        if not topic:
            return jsonify({'error': 'No topic provided'})
        
        # Use the bot's Wikipedia search
        response = bot.search_wikipedia(topic)
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        print(f"Error in search endpoint: {e}")
        return jsonify({'success': False, 'error': 'Search failed'})

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get chatbot statistics"""
    try:
        user_id = session.get('user_id')
        user_data = load_user_data(user_id) if user_id else {}
        
        stats = {
            'total_conversations': len(bot.conversation_history) if hasattr(bot, 'conversation_history') else 0,
            'user_messages': len(user_data.get('chat_history', [])),
            'username': user_data.get('username'),
            'since': user_data.get('created_at', 'Unknown')
        }
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({'error': 'Could not get statistics'})

if __name__ == '__main__':
    print("🤖 Starting Wikipedia ChatBot Server...")
    print("📚 Powered by Wikipedia API")
    print("🌐 Server will run at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
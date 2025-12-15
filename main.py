# Save as: main.py
import webbrowser
import threading
import time
import os
import sys

def launch_chatbot():
    """Launch the Flask chatbot server"""
    try:
        # Import and run the Flask app
        from chatbot_app import app
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(2)  # Wait for server to start
            webbrowser.open('http://localhost:5000')
        
        # Start browser in separate thread
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Run the Flask app
        print("🚀 Starting ChatBot Server...")
        print("🌐 Opening browser at: http://localhost:5000")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 50)
        app.run(debug=True, use_reloader=False)
        
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("Make sure all required files are present.")
        print("Required files: chatbot_app.py, chatbot_logic.py, templates/index.html, static/css/style.css")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    launch_chatbot()
    
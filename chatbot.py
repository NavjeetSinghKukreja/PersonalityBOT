import json
from openai import OpenAI
import re
from datetime import datetime
from config import *

class PersonalChatbot:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.conversation_history = []
        self.system_prompt = ""
        self.avg_message_length = 0

    def process_chat_file(self, file_path):
        """Process a single chat file and extract messaging patterns."""
        messages = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    # Extract username and message using regex
                    match = re.match(r'\[(.*?)\] (.*?): (.*)', line.strip())
                    if match:
                        timestamp, username, message = match.groups()
                        messages.append({
                            'timestamp': timestamp,
                            'username': username,
                            'message': message
                        })
        except Exception as e:
            print(f"Error processing chat file: {e}")
            print("Make sure your chat file follows the format: [timestamp] username: message")
        
        if not messages:
            print("No messages were processed. Please check your chat file format.")
            
        return messages

    def create_personality_prompt(self, your_username, messages):
        """Create a more detailed system prompt based on message history."""
        your_messages = [msg for msg in messages if msg['username'] == your_username]
        
        if not your_messages:
            raise ValueError(f"No messages found for username: {your_username}")
        
        # More detailed message analysis
        self.avg_message_length = sum(len(msg['message']) for msg in your_messages) / len(your_messages)
        
        
        # Analyze capitalization patterns
        uses_caps = sum(msg['message'].isupper() for msg in your_messages) > len(your_messages) * 0.1
        
        # Analyze punctuation patterns
        uses_multiple_punctuation = sum(('!!' in msg['message'] or '??' in msg['message']) 
                                      for msg in your_messages) > len(your_messages) * 0.1
        
        # Get common phrases (3+ word sequences that appear multiple times)
        all_text = ' '.join(msg['message'] for msg in your_messages)
        words = all_text.split()
        phrases = []
        for i in range(len(words)-2):
            phrase = ' '.join(words[i:i+3])
            if all_text.count(phrase) >= 2:  # appears at least twice
                phrases.append(phrase)
        phrases = list(set(phrases))[:5]  # top 5 unique phrases
        
        prompt = f"""You are simulating {your_username}'s messaging style. You must maintain EXACT consistency with these patterns:

CORE PERSONALITY TRAITS:
1. Message Length: Typically writes {int(self.avg_message_length)} characters per message
2. Capitalization: {'Often uses caps for emphasis' if uses_caps else 'Typically uses standard capitalization'}
3. Punctuation: {'Uses multiple punctuation marks (!!, ??)' if uses_multiple_punctuation else 'Uses standard punctuation'}

SIGNATURE PHRASES AND EXPRESSIONS:
{chr(10).join(f'- "{phrase}"' for phrase in phrases)}

VOICE AND TONE:
Here are representative examples of {your_username}'s exact messaging style:"""
        
        # Add more recent and diverse example messages
        recent_messages = your_messages[-15:]  # Last 15 messages
        diverse_examples = set()  # Use set to avoid repetitive message patterns
        for msg in recent_messages:
            if len(diverse_examples) >= 10:  # Keep top 10 diverse examples
                break
            if not any(msg['message'] in existing for existing in diverse_examples):
                diverse_examples.add(msg['message'])
        
        for example in diverse_examples:
            prompt += f"\n- {example}"
        
        self.system_prompt = prompt
        return prompt
    
    def generate_response(self, input_message):
        """Generate a response that better matches the user's style."""
        try:
            # Add the user input to the conversation history
            self.conversation_history.append({"role": "user", "content": input_message})
            
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    *self.conversation_history[-10:],  # Use only last 10 messages to maintain context
                    {"role": "user", "content": input_message}
                ],
                max_tokens=1000,  # Adjusted token limit
                temperature=TEMPERATURE,
                presence_penalty=0.6,
                frequency_penalty=0.2
            )
            
            response_text = response.choices[0].message.content

            # Check response length
            if abs(len(response_text) - int(self.avg_message_length)) > self.avg_message_length * 0.5:
                # Retry if the response is too short
                return self.generate_response(input_message)
            
            # Add response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response_text})
            return response_text
            
        except Exception as e:
            return f"Error generating response: {e}"

def main():
    # Initialize chatbot
    chatbot = PersonalChatbot()
    
    # Process chat file
    print(f"Loading chat data from: {CHAT_FILE}")
    messages = chatbot.process_chat_file(CHAT_FILE)
    
    if not messages:
        print("No messages found. Exiting...")
        return
        
    # Create personality prompt
    print(f"Creating personality profile for: {YOUR_USERNAME}")
    try:
        prompt = chatbot.create_personality_prompt(YOUR_USERNAME, messages)
        print("\nPersonality analysis complete!")
        print(f"Analyzed {len(messages)} messages")
        print(f"Average message length: {int(chatbot.avg_message_length)} characters")
    except Exception as e:
        print(f"Error creating personality profile: {e}")
        return
    
    print("\nChatbot is ready!")
    print("Commands:")
    print("- Type 'quit' or 'exit' to stop")
    print("- Press Ctrl+C to force quit")
    print("-" * 50)
    
    # Interactive chat loop
    while True:
        try:
            user_input = input("\nYou: ").lower()
            if user_input in ['quit', 'exit', 'stop', 'q']:
                print("Shutting down chatbot...")
                break
                
            response = chatbot.generate_response(user_input)
            print(f"\nBot: {response}")
            
        except KeyboardInterrupt:
            print("\nForce quitting chatbot...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Type 'quit' to exit or press Ctrl+C to force quit")

if __name__ == "__main__":
    main()

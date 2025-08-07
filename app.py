import os
import re
import time
import json
from datetime import datetime, timedelta
from threading import Thread

from dotenv import load_dotenv
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import firebase_admin
from firebase_admin import credentials, firestore

# Load environment variables from the .env file
load_dotenv()

# Initialize Firebase Admin SDK using credentials from the .env file
try:
    firebase_config = os.getenv("FIREBASE_CONFIG")
    if not firebase_config:
        print("FIREBASE_CONFIG environment variable is not set. Please check your .env file.")
        exit()
    # Use json.loads instead of eval for safety
    cred = credentials.Certificate(json.loads(firebase_config))
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    print("Please ensure your FIREBASE_CONFIG in the .env file is a valid single-line JSON string.")
    exit()
    

# Your Twilio Account SID, Auth Token, and WhatsApp number
# These are loaded from the .env file
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
client = Client(account_sid, auth_token)

app = Flask(__name__)

# --- Natural Language Processing (NLP) and Reminder Logic ---

def parse_reminder_message(text):
    """
    Parses a user's message to extract the task and a timestamp.
    This is a simple, rule-based approach for demonstration.
    
    Example input: "remind me to buy groceries tomorrow at 5pm"
    """
    text = text.lower()
    
    # A regular expression pattern to find the task and time
    # This pattern is simplified and can be expanded for more complex requests
    match = re.search(r"remind me to (.+) (tomorrow|today|next week|at \d{1,2}(?::\d{2})?(?:am|pm)?|on \w+)", text)
    
    if not match:
        return None, None
        
    task = match.group(1).strip()
    time_string = match.group(2).strip()
    
    now = datetime.now()
    schedule_time = None
    
    # Logic for parsing different time keywords
    if "tomorrow" in time_string:
        schedule_time = now + timedelta(days=1)
        # Check for a specific time like "at 5pm"
        time_match = re.search(r"at (\d{1,2}(?::\d{2})?(?:am|pm))", time_string)
        if time_match:
            time_part = time_match.group(1)
            try:
                hour = int(re.search(r"(\d{1,2})", time_part).group(1))
                minute = int(re.search(r":(\d{2})", time_part).group(1)) if ":" in time_part else 0
                if "pm" in time_part and hour < 12:
                    hour += 12
                schedule_time = schedule_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            except (ValueError, AttributeError):
                schedule_time = schedule_time.replace(hour=9, minute=0, second=0, microsecond=0) # Default 9 AM
                
    elif "today" in time_string:
        schedule_time = now
        time_match = re.search(r"at (\d{1,2}(?::\d{2})?(?:am|pm))", time_string)
        if time_match:
            time_part = time_match.group(1)
            try:
                hour = int(re.search(r"(\d{1,2})", time_part).group(1))
                minute = int(re.search(r":(\d{2})", time_part).group(1)) if ":" in time_part else 0
                if "pm" in time_part and hour < 12:
                    hour += 12
                schedule_time = schedule_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            except (ValueError, AttributeError):
                schedule_time = schedule_time.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0) # Default to 1 hour from now
    
    elif "next week" in time_string:
        schedule_time = now + timedelta(weeks=1)
        schedule_time = schedule_time.replace(hour=9, minute=0, second=0, microsecond=0)
        
    return task, schedule_time

def send_reminder(recipient, task):
    """
    Sends a reminder message via Twilio's WhatsApp API.
    """
    try:
        # The 'to' number must be prefixed with 'whatsapp:'
        client.messages.create(
            from_=twilio_whatsapp_number,
            to=recipient,
            body=f"Reminder: {task}"
        )
        print(f"Sent reminder to {recipient} for task: {task}")
    except Exception as e:
        print(f"Failed to send reminder to {recipient}: {e}")

# --- Background Scheduler with Firestore Integration ---
def run_scheduler():
    """
    This function runs in a separate thread, constantly checking Firestore
    for reminders that are due and sending them.
    """
    while True:
        try:
            # Query Firestore for reminders with a timestamp less than or equal to the current time
            reminders_ref = db.collection('reminders').where('timestamp', '<=', datetime.now())
            reminders_to_send = reminders_ref.stream()

            for reminder_doc in reminders_to_send:
                reminder_data = reminder_doc.to_dict()
                recipient = reminder_data.get('phone_number')
                task = reminder_data.get('task')
                
                if recipient and task:
                    send_reminder(recipient, task)
                    # Delete the reminder from the database after it has been sent
                    db.collection('reminders').document(reminder_doc.id).delete()
                    print(f"Deleted sent reminder: {reminder_doc.id}")

        except Exception as e:
            print(f"Error in scheduler loop: {e}")

        # Sleep for a minute before checking again
        time.sleep(60)

# Start the scheduler in a background thread to prevent it from blocking the Flask app
scheduler_thread = Thread(target=run_scheduler)
scheduler_thread.daemon = True
scheduler_thread.start()

# --- Flask Webhook Endpoint ---
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """
    This endpoint handles all incoming messages from Twilio.
    """
    # Get the user's phone number and the message body from the request
    from_number = request.form.get("From")
    message_body = request.form.get("Body")

    response = MessagingResponse()
    
    if message_body:
        # Check if the message is a reminder command
        if message_body.lower().startswith("remind me to"):
            task, schedule_time = parse_reminder_message(message_body)
            if task and schedule_time:
                # Save the reminder to a new document in the 'reminders' collection in Firestore
                db.collection('reminders').add({
                    'phone_number': from_number,
                    'task': task,
                    'timestamp': schedule_time
                })
                
                # Send a confirmation message back to the user
                response.message(f"Okay, I'll remind you to '{task}' on {schedule_time.strftime('%Y-%m-%d at %H:%M')}.")
            else:
                # If the bot doesn't understand the command
                response.message("I couldn't understand that. Please phrase your reminder like 'remind me to buy milk tomorrow at 5pm'.")
        else:
            # Welcome message for new users or unrecognized commands
            response.message("Hello! I'm your reminder bot. You can ask me to set a reminder like this: 'remind me to call mom tomorrow at 3pm'.")

    return str(response)

if __name__ == "__main__":
    # The eval(firebase_config) is used to parse the string into a valid JSON object.
    app.run(debug=True)
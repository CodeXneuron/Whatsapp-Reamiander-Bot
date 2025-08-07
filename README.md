🤖 WhatsApp Reminder Bot
This is an automated WhatsApp bot built with Python, designed to help users set and receive reminders directly through a messaging interface. By leveraging natural language processing and a cloud-based database, this bot provides a simple yet powerful way to manage personal tasks and appointments.

✨ Features
Automated Reminders: Users can set reminders with simple text messages (e.g., "remind me to call mom tomorrow at 3pm").

Natural Language Processing: The bot's logic can parse messages to understand the task and the scheduled time.

Persistent Storage: All reminders are stored securely in a Firestore database, ensuring no data is lost even if the service is restarted.

Cloud-Powered: The application is designed to be deployed on a serverless platform like Google Cloud Run for continuous, automated operation.

⚙️ Technologies Used
Python: The primary programming language for the bot's logic.

Flask: A lightweight web framework to handle incoming webhooks from Twilio.

Twilio API: Provides the seamless integration with WhatsApp for sending and receiving messages.

Google Cloud Firestore: A NoSQL cloud database for persistent data storage.

Docker: For containerizing the application for easy deployment.

Google Cloud Run: The serverless platform where the bot is deployed to run as a 24/7 automated service.

🚀 Current Project Status
The core functionality of the bot is complete. The project is at the deployment stage, with all the necessary code, including the Dockerfile and configuration files, successfully pushed to this repository. The next step is to finalize the deployment to Google Cloud Run to make the service fully automated.

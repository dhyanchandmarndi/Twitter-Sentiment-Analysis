🐦 Real-Time Twitter Sentiment Analysis
A full-stack web application that fetches real-time tweets based on a user-specified hashtag using the Twitter API (v2), 
processes the text using Natural Language Processing (NLP), and classifies the overall sentiment as positive, negative, or neutral.

🔧 Tech Stack
Backend: Python, Flask, Twitter API v2, VADER
Frontend: HTML, CSS and Bootstrap (for user input and visualization)
Database: MongoDB (for storing tweet data and sentiment results)
Other: dotenv for secure environment variables, Flask-CORS for cross-origin handling

🚀 Features
Search tweets by hashtag or keyword in real-time
NLP-based sentiment classification (positive, neutral, negative)
Sentiment statistics visualization (bar graph)
API rate limit handling (for free-tier Twitter access)
Responsive and user-friendly interface

📌 How It Works
User enters a hashtag on the frontend.
Frontend sends the request to a Flask backend.
Backend calls Twitter API and retrieves recent tweets.
Sentiment analysis is performed using NLP.
Sentiment data is returned and visualized on the client side.

Link: https://real-time-sentiment-analysis.vercel.app/

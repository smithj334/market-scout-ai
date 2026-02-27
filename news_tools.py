import urllib.request
from bs4 import BeautifulSoup
from textblob import TextBlob

def get_news_sentiment(ticker):
    try:
        # Pull directly from Google News RSS for bulletproof reliability
        url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read()
        soup = BeautifulSoup(html, "xml")
        
        # Grab the top 5 most recent articles
        items = soup.find_all("item")[:5]
        
        if not items:
            return f"No recent news found for {ticker}."
        
        headlines = []
        total_polarity = 0
        
        for item in items:
            title = item.title.text
            headlines.append(title)
            # TextBlob calculates sentiment polarity from -1 (very negative) to 1 (very positive)
            blob = TextBlob(title)
            total_polarity += blob.sentiment.polarity
            
        avg_polarity = total_polarity / len(headlines)
        
        if avg_polarity > 0.1:
            sentiment_label = "Positive"
        elif avg_polarity < -0.1:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"
            
        news_summary = f"Recent News Sentiment for {ticker}: {sentiment_label} (Score: {avg_polarity:.2f})\n"
        news_summary += "Top Recent Headlines:\n"
        for h in headlines:
            news_summary += f"- {h}\n"
            
        return news_summary
        
    except Exception as e:
        return f"Error fetching news data: {str(e)}"

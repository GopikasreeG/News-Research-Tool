import random
import time
import logging
from datetime import datetime
import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from newspaper import Article, Config

NEWS_API_KEY = '41acfedd95724cbebe7c43911e95b061'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

countries = {'usa': 'us', 'india': 'in'}
country = countries['india']

def index(request):
    """Render the index page."""
    return render(request, 'news/index.html')

class CustomLoginView(LoginView):
    template_name = 'news/login.html'
    success_url = reverse_lazy('news_list')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('news_list')
    else:
        form = UserCreationForm()
    return render(request, 'news/signin.html', {'form': form})

def get_top_headlines(date, limit=3):
    # Format the date to the required format
    date_str = date.strftime('%Y-%m-%d')
    
    url = f'https://newsapi.org/v2/everything?q=*&from={date_str}&to={date_str}&sortBy=publishedAt&language=en&apiKey={NEWS_API_KEY}'
    response = requests.get(url)
    data = response.json()
    if data['status'] == 'ok' and data['totalResults'] > 0:
        logger.info(f"Fetched {len(data['articles'])} articles")
        return [article['url'] for article in data['articles'][:limit]]
    else:
        raise Exception('Failed to fetch news for the specified date')

def scrape_article(article_url):
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36 Edg/91.0.864.54',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36'
    ]
    user_agent = random.choice(user_agents)  # Choose a random user-agent from the list

    config = Config()
    config.browser_user_agent = user_agent

    article = Article(article_url, config=config)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            article.download()
            article.parse()
            article.nlp()
            logger.info(f"Scraped article from {article_url}")
            return article.text, article.summary, article.keywords
        except Exception as e:
            logger.error(f'Attempt {attempt + 1} to scrape {article_url} failed: {e}')
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise e

def news_list(request):
    articles_data = []
    date_str = request.GET.get('date')
    if date_str:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        try:
            article_urls = get_top_headlines(date)
            for index, article_url in enumerate(article_urls):
                try:
                    text, summary, keywords = scrape_article(article_url)
                    articles_data.append({
                        'url': article_url,
                        'text': text,
                        'summary': summary,
                        'keywords': keywords,
                    })
                    logger.info(f"Added article {index + 1} to articles_data")
                except Exception as e:
                    logger.error(f'Failed to scrape article {article_url}: {e}')
        except Exception as e:
            logger.error(f'Failed to fetch news for the specified date: {e}')
            return render(request, 'news/error.html', {'error': str(e)})

    logger.info(f"Rendering {len(articles_data)} articles")
    return render(request, 'news/news_list.html', {'articles': articles_data})

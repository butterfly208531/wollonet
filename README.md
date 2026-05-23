# WolloNet - Information Retrieval System

A Django-based Information Retrieval System built for Wollo University.

## 🔍 Features

- Full-text search using TF-IDF ranking
- Inverted index for fast document retrieval
- Amharic and English document support
- Admin panel for document management
- Corpus of Wollo University documents

## 🚀 Live Demo

[https://wollonet.onrender.com](https://wollonet.onrender.com)

## 🛠️ Tech Stack

- **Backend:** Django 5.2
- **Search:** TF-IDF, Inverted Index (scikit-learn, NLTK)
- **Database:** SQLite
- **Deployment:** Render
- **Static Files:** WhiteNoise

## 📁 Project Structure

```
wollonet/
├── documents/corpus/        # Text documents for indexing
├── search_app/              # Main Django app
│   ├── indexer.py           # Inverted index builder
│   ├── ranker.py            # TF-IDF ranking
│   ├── preprocessor.py      # Text preprocessing
│   └── views.py             # Search views
├── wollo_search/            # Django project settings
├── manage.py
├── requirements.txt
└── Procfile
```

## ⚙️ Local Setup

```bash
# Clone the repo
git clone https://github.com/butterfly208531/wollonet.git
cd wollonet

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Index documents
python manage.py index_docs

# Start server
python manage.py runserver
```

## 🌐 Deployment

Deployed on [Render](https://render.com) using `build.sh` and `Procfile`.

## 👨‍💻 Author

Wollo University — Information Retrieval Project

# 1) Start from a lightweight Python image
FROM python:3.11-slim

# 2) Install system dependencies for psycopg2, shap, etc.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# 3) Set working directory
WORKDIR /app

# 4) Copy your application code
COPY . .

# 5) Upgrade pip & wheel, then install all Python deps in one go
RUN pip install --upgrade pip wheel \
 && pip install \
      flask \
      flask-login \
      python-dotenv \
      psycopg2-binary \
      numpy \
      pandas \
      scikit-learn \
      imbalanced-learn \
      joblib \
      papermill \
      nbconvert \
      shap \
      jupyter

# 6) Tell Flask where the app lives and listen on all interfaces
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# 7) Expose the port Flask will run on
EXPOSE 5000

# 8) Default command
CMD ["flask", "run"]

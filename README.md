# City Library API

## Introduction

This is a RESTful API built with Django and Django Rest Framework for a city
library service. It allows users to chose books and make borrowings. It also
allows to get notifications about borrowings creation.

## Features

## Running with GitHub

There is `.env.sample` file in the root directory. Copy it to `.env` and change
the values to match your environment.

```bash
git clone https://github.com/dkibalenko/city-library-api.git
cd city-library-api
python3 -m venv env
source venv/Scripts/activate
pip install -r requirements.txt

Create new Postgres DB & User
Copy .env.sample to .env and populate it with your credentials

python manage.py migrate
python manage.py runserver
python python manage.py runserver
```

# City Library API

## Introduction

This is a RESTful API built with Django and Django Rest Framework for a city
library service. It allows users to chose books and make borrowings. It also
allows to get notifications about borrowings creation.

## Features

- **User registration and authentication with JWT tokens.**: Users can register
  and log in with their email and password.
- **Authorization with permissions**: Users can have different levels of access
  based on their permissions. Only admins can manage books and see all borrowings.
- **Book borrowings**: Users can borrow books and return them.
- **Borrowings can be filtered by active status and user ID**: Admins can filter
  borrowings by active status and user ID.
- **Notifications**: Users can get notifications about borrowings creation on Telegram.
- **Swagger Documentation**: Endpoints are documented with requests and responses examples.

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

## Running with Docker

- Copy .env.sample to .env and populate it with your environment variables

```bash
docker compose build
docker compose up
```

## Getting access

- Get access token via `/api/user/token/`
- Enter Test User credentials

## Test User

Email: `admin@test.com`
Password: `admin12345`


## Test Coverage

```bash
coverage run manage.py test
coverage report
```

## Contributing

- Fork the repository
- Create a new branch (`git checkout -b <new_branch_name>`)
- Commit your changes (`git commit -am 'message'`)
- Push the branch to GitHub (`git push origin <new_branch_name>`)
- Create a new Pull Request

# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- User registration and login
- Session management with bearer tokens
- Sign up/unregister with authenticated users
- Admin-only activity creation endpoint

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                            | Description                                                         |
| ------ | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| POST   | `/auth/register`                                                    | Register a user with `email`, `password`, and optional `role`      |
| POST   | `/auth/login`                                                       | Login and receive a bearer token                                   |
| GET    | `/auth/session`                                                     | Get active session user from bearer token                          |
| POST   | `/auth/logout`                                                      | Invalidate current bearer token                                    |
| GET    | `/activities`                                                       | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup`                                | Sign up the logged-in user (admins may pass `?email=` override)     |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a user (self or admin)                                  |
| POST   | `/activities?name=...&description=...&schedule=...&max_participants=...` | Create activity (admin only)                                       |

## Authentication Strategy

- Passwords are hashed with PBKDF2-HMAC-SHA256 and per-user random salts.
- Login returns an opaque bearer token.
- Clients send `Authorization: Bearer <token>` on protected endpoints.
- Tokens are stored in-memory on the server for this demo app.
- Frontend stores token in `localStorage` and updates UI for logged-in/logged-out state.

### Demo Accounts

- `admin@mergington.edu` / `admin123!`
- `student@mergington.edu` / `student123!`

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.

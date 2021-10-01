# Welcome to Django Booking System

Django Booking System is an open-source web application for the taking and managing of bookings. Features include:

 * Creating bookings with clever assignment to available `Tables`
 * Ability to add and manage multiple `Sites` with their own settings, resources and users
 * Asynchronous email sending along with automated reminder emails
 * Management of internal users, with multiple user types and permissions
 * Calendar view of all bookings for multiple `Sites`
 * Plus many more features...

View the project at [github.com](https://github.com/Maxamuss/django-booking-system).

## Development

### Docker

The easiest way to get started with Django Booking System is with Docker. Follow the instructions below to get up and running.

1. Clone the project from GitHub
```bash
git clone https://github.com/Maxamuss/django-booking-system
```

2. Remove the .example suffix from the .env.dev.example file name: 
```
.env.dev.example -> .env.dev
```

3. Build the Docker containers
```bash
docker-compose up -d --build
```

### Virtual Environment 

TODO

## Production

TODO

![Static Badge](https://img.shields.io/badge/Version-v1.3.0-brightgreen?style=flat) ![Static Badge](https://img.shields.io/badge/Python-v3.8-blue) ![Static Badge](https://img.shields.io/badge/Dockercompose-v3.5-blue)
# Orchestrated Event-Driven Architecture (Mediator)

### Introduction to the Wonderland Bookstore OEDA

The Wonderland Book Store system is a simplified example of an **Orchestrated Event-Driven Architecture** designed for e-commerce.
It demonstrates how a user can order books online using a lightweight setup. The system incorporates minimal services to make the architecture easy to understand while showcasing the essential features of such a design.

![Alt text](images/wonderland_welcome.png?raw=true "Wonderland welcome Page")

By utilizing modern tools and technologies, the system ensures smooth communication between services and seamless operation.

### Technology Stack
The technology stack includes **RabbitMQ**, which serves as a message broker, enabling reliable and efficient communication between services. **Python Flask** acts as both a mediator and orchestrator, handling service coordination and providing a foundation for the backend logic. The programming language of choice is **Python**, known for its simplicity and readability.

To ensure consistency in deployment and scalability, the system is containerized using **Docker** and managed with **Docker Compose**.
Data storage is handled by **SQLite**, a lightweight database ideal for small-scale applications, making it suitable for this demonstration for inventory service and **PostgreSQL** and **SQL Alchemy** for customer service.

### Components & Services
The OEDA Wonderland Bookstore is composed of several key components. It consists of two databases, four services, an API to orchestrate the purchase workflow and a broker. In this section, we provide a brief overview of their roles and responsibilities.

The most important component is Orchestrator or Mediator, which acts as an API. Built using Python Flask, it handles customer purchase requests step by step.

**RabbitMQ** acts as a message broker. RPC is mainly used, since there is a need for responses from the client. Also, topic and direct exchanges are used to send to the notification and logging components.

The **Inventory Service** keeps track of available books and updates stock levels as orders are placed. 

The **Logging Service** records system activities, debug messages and errors, creating a record for troubleshooting and monitoring.

![Alt text](images/OEDA1.png?raw=true "Wonderland Book Store")

The **Customer Service** manages user information, such as profiles and order histories.

The **Notification Service** alerts users about their order status, such as confirmations and shipping updates and so on.

Payments are processed securely using the **Payment Service**, which validates transactions and ensures orders are completed successfully.

### How To Run Application
As the Wonderland Application is fully containerized with Docker and orchestrated with Dockercompose, you can simply follow the instruction below:
1. In the project diectory with dockercopose file is, build application.

2. Call Flask API with the command below:

3. To see the logs via Dozzle service, call it in the browser.

![Static Badge](https://img.shields.io/badge/version-v1.3.0-brightgreen?style=flat) ![Static Badge](https://img.shields.io/badge/Python-v3.8-blue)
# Orchestrated Event-Driven Architecture (Mediator)

### Introduction to the Wonderland Book Store System

The Wonderland Book Store system is a simplified example of an **Orchestrated Event-Driven Architecture** designed for e-commerce.
It demonstrates how a user can order books online using a lightweight setup. The system incorporates minimal services to make the architecture easy to understand while showcasing the essential features of such a design. By utilizing modern tools and technologies, the system ensures smooth communication between services and seamless operation.

The technology stack includes **RabbitMQ**, which serves as a message broker, enabling reliable and efficient communication between services. **Python Flask** acts as both a mediator and orchestrator, handling service coordination and providing a foundation for the backend logic. The programming language of choice is **Python**, known for its simplicity and readability.

To ensure consistency in deployment and scalability, the system is containerized using **Docker** and managed with **Docker Compose**. Data storage is handled by **SQLite**, a lightweight database ideal for small-scale applications, making it suitable for this demonstration.

The system is composed of several key services. The **Inventory Service** keeps track of available books and updates stock levels as orders are placed. The **Logging Service** records system activities and errors, creating a record for troubleshooting and monitoring.

The **Customer Service** manages user information, such as profiles and order histories. Additionally, the **Notification Service** alerts users about their order status, such as confirmations and shipping updates. Payments are processed securely using the **Payment Service**, which validates transactions and ensures orders are completed successfully.

To monitor system logs in real time, the setup includes **Dozzle**, a log viewer that displays the application logs stored in CSV format. This allows administrators to oversee the application's performance and troubleshoot issues effectively. Together, these components form a cohesive system that showcases the core principles of orchestrated, event-driven architecture while maintaining simplicity and clarity.

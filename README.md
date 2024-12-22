# 📚 StockStudy 

**A full-stack web application designed to help Stockton students create, search, and join study groups, and explore study spots on an interactive map.**

<img width="1800" alt="Screenshot 2024-12-15 at 5 59 27 PM" src="https://github.com/user-attachments/assets/b3292ecb-c453-43b1-8e64-fc0f643e53d2" />


#### Video Demo: [Here](https://youtu.be/RvGMq054zk4)
#### Live Demo: [StockStudy](https://www.mystockstudy.com) (Requires Stockton Email to register)


## Tech Stack 💻
* **Flask**
* **PostgreSQL**
* **Bootstrap**
* **Javascript**

---

## Features 🛠️
- **🔒 User Registration and Login**: Secure account creation and login with hashed passwords or through Google Single Sign-On (SSO). Users are able to reset their password and verify their account with magic links sent to their email through a custom SMPT server.
- **👥 Group Creation**: Create new study groups and set group details like name, subject, description, and group type (Private or Public).
- **🔎 Search Functionality**: Search for existing study groups based on name, description, and group owner.
- **🤝 Join Study Groups**: Join public study groups right away to view members inside and collaborate or request to join private groups.
- **✉️ Inbox**: Group admins can see all requests for their groups allowing them to accept or reject the requests. Outgoing group request are also shown allowing the user to view when they were sent and allow them to cancel them if they please.
- **🗺️ Interactive Study Map**: Google Maps API is integrated and centered over Stockton University. Study group creation on map and custom map design is still in development and will be implemented soon.
- **👤 Profile Management**: Users can customize their profile with their bio, major, and year of study. Users who signed up manually (not Google SSO) can also change their password form the profile section.

### Authentication 🔒
- **Google SSO**: Allows for secure account sign up / sign in. Only allows users with @go.stockton.edu emails.
- **Flask Limiter**: Used to limit email request sent from SMPT server
- **Bcrypt**: Used for password and email hashing

### Main functionality 👥
- **SQLAlchemy**: ORM for sqlite which adds the ability to create 'model' files which simplify working with sqlite and creating relationships between tables.
- **Flash-Migrate**: Keeps git-like version history of database to allow developer to add new database fields / features while migrating existing data over.
- **Flask-Mail**: Simplifies SMTP usage and allows for a custom email to send from


# Photo API v3 Installation Guide

This guide will help you set up the Photo API v3 project locally.  
You can either **clone the repo from GitHub** or **manually copy your code into a folder** if you’re not using GitHub yet.

---

1) Set up your project folder
-----------------------------

### Option A: Clone from GitHub
Make sure Git is installed, then:

    git clone https://github.com/YOUR-USERNAME/photo_api_v3.git
    cd photo_api_v3

Open the folder in **Visual Studio Code (VSC)**:
- Open VSC
- Go to `File > Open Folder`
- Select the `photo_api_v3` folder you just cloned

### Option B: Manual setup (no GitHub)
If you’re not using Git yet:
1. Create a folder:
    mkdir photo_api_v3
    cd photo_api_v3
2. Open this folder in **Visual Studio Code**.
3. Copy all your project files into this folder so it looks like:
```bash
    photo_api_v3/
    ├── app/
    │   ├── db.py
    │   ├── models.py
    │   ├── schemas.py
    │   ├── main.py
    │   └── routers/
    │       ├── clients.py
    │       ├── invoices.py
    │       ├── payments.py
    │       ├── packages.py
    │       └── shoots.py
    ├── requirements.txt
    ├── installation.txt
    ├── .env.example
    └── README.md
```
---

2) Create a virtual environment
-------------------------------
Make sure you're using **Python 3.12 or higher**.

On macOS or Linux:

    python -m venv .venv
    source .venv/bin/activate

On Windows:

    python -m venv .venv
    .venv\Scripts\activate

You'll know the venv is active when you see `(.venv)` at the start of your terminal line.

---

3) Install dependencies
-----------------------
With your venv active, install the dependencies:

    pip install -r requirements.txt

If `pip` isn't found, check your venv activation.  
If you see errors, upgrade pip:

    python -m pip install --upgrade pip

---

4) Create and configure your database
-------------------------------------
1. Open **MySQL Workbench** (or your preferred client).
2. Create the database:

    CREATE DATABASE photo_db_v3;

3. Copy `.env.example` to `.env`:

    cp .env.example .env

4. Update the `.env` file with your connection string:

    DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/photo_db_v3

---

5) Run the server
-----------------
From your terminal (inside the project folder with the venv activated):

    uvicorn app.main:app --reload

You should see something like:

    INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

---

6) Check the API docs
---------------------
Open your browser and visit:

    http://127.0.0.1:8000/docs

Swagger UI will show all the available endpoints with clear descriptions.

![Photo Client Manager API](./docs/Photo_Client_Manager_API.png)

---

7) Quick health check
---------------------
Confirm the API is running:

    GET http://127.0.0.1:8000/health

Expected response:

    { "status": "ok" }

---

Notes
-----
- Always activate your venv before running any commands.
- Make sure MySQL is running before starting Uvicorn.
- If you add or modify tables, you can recreate them manually with:

    from app.db import Base, engine
    Base.metadata.create_all(bind=engine)

**read me**

discord.py <3

setup:
    $ cd your-bot-source
    $ python -m venv .venv
    $ .venv\Scripts\activate.bat #on windows
    pip install -U discord dotenv psycopg2

include in .env:
    TOKEN, #discord app token
    SERVER_ID, #id to server bot is run in
    POSTGRES_LINK #link to postgres-database
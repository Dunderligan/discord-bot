**read me**

discord.py <3

setup:
    $ cd your-bot-source
    $ python -m venv .venv
    $ .venv\Scripts\activate.bat #on windows
    pip install -U discord dotenv psycopg2-binary typst requests

include in .env:
    TOKEN, #discord app token
    SERVER_ID, #id to server bot is run in
    POSTGRES_LINK #link to postgres-database
    ADMIN_ID # id of role user needs to run some commands
    TEXT_CATEGORY # category to put text-channels in

for typst:
    import fonts: Rajdhani and Inter (semibold, semibold italic)
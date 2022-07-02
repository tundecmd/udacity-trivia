from dotenv import load_dotenv
import os
load_dotenv()
DB_HOST = os.getenv('DB_HOST', '127.0.0.1:5432')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'lateefbabatund')
DB_NAME = os.getenv('DB_NAME', 'trivia_udacity')
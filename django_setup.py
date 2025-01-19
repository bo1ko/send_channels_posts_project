import os
import django
from dotenv import load_dotenv

load_dotenv(override=True)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

django.setup()

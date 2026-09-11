import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'amr_shield_project.settings')

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()

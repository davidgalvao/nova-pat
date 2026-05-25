from django.db import models
from core.models import BasePage

class HomePage(BasePage):
    """
    Página inicial que herda de BasePage.
    """
    template = "home/home_page.html"
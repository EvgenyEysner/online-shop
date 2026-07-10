from django.db import models


class Category(models.Model):
    name = models.CharField("Kategorie", max_length=128)

    def __str__(self):
        return self.name

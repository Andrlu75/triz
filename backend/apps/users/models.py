from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    PLAN_CHOICES = [
        ("free", "Free"),
        ("pro", "Pro"),
        ("business", "Business"),
    ]

    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default="free")
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )
    locale = models.CharField(max_length=10, default="ru")

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return self.username

from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    telegram = models.ForeignKey(
        "TelegramUser", on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "CustomUser"
        verbose_name_plural = "CustomUsers"


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return str(self.telegram_id)

    class Meta:
        verbose_name = "TelegramUser"
        verbose_name_plural = "TelegramUsers"


class TelegramAccount(models.Model):
    phone_number = models.CharField(max_length=32)
    api_hash = models.CharField(max_length=128)
    api_id = models.CharField(max_length=54)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.phone_number

    class Meta:
        verbose_name = "TelegramAccount"
        verbose_name_plural = "TelegramAccounts"


class TelegramChannel(models.Model):
    title = models.CharField(max_length=128, null=True, blank=True)
    url = models.URLField(null=False, blank=False)
    telegram_account = models.ForeignKey(
        TelegramAccount, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return self.title if self.title else self.url

    class Meta:
        verbose_name = "TelegramChannel"
        verbose_name_plural = "TelegramChannels"

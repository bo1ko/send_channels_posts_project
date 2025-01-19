from django.contrib import admin
from . import models

admin.site.register([models.CustomUser, models.TelegramAccount, models.TelegramChannel, models.TelegramUser])

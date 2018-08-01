from django.contrib import admin

from .models import *

class ReturnedTradeAdmin(admin.ModelAdmin): pass
admin.site.register(ReturnedTrade, ReturnedTradeAdmin)

from django.conf.urls import url
from django.contrib import admin
from marketmakestats.views import *

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', MarketMakeStatsView.as_view()),
]

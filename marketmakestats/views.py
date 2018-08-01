from django.shortcuts import render
from django.views import View

from .forms import MarketRequestForm
from .models import ReturnedTrade
from .helpers import makeMarketStats

import datetime

DEFAULT_MARKETS = [
    'BTC/ETH',
    'BTC/EOS',
    'ETH/EOS',
    'STEEM/ETH',
    'ETH/LTC',
    'ETH/USDT',
]


class MarketMakeStatsView(View):
    form_class = MarketRequestForm
    template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {'form': form}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        context = {'form': form}
        if form.is_valid():
            if form.data['market']:
                form.save()
                context['success'] = True
                context['last_entry'] = '{}'.format(ReturnedTrade.objects.last())
            else:
                stats = {}
                interval = form.cleaned_data['interval']
                percent = form.cleaned_data['percent']
                period = form.cleaned_data['period']
                for market in DEFAULT_MARKETS:
                    stats[market] = makeMarketStats(market, interval, percent, period)
                    new_entry = ReturnedTrade.objects.create(
                        market=market,
                        interval=interval,
                        percent=percent,
                        period=period,
                        query_date=datetime.date.today(),
                        returned_trades=stats[market],
                    )
                    new_entry.save()
                    context.update(
                        success=True,
                        interval=interval,
                        percent=percent,
                        period=period,
                        stats=stats,
                    )
        return render(request, self.template_name, context)

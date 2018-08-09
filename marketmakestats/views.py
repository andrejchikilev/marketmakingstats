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
            interval = form.cleaned_data['interval']
            percent = form.cleaned_data['percent']
            period = form.cleaned_data['period']
            if form.data['market']:
                form.save()
                context['success'] = True
                context['last_entry'] = '{}'.format(ReturnedTrade.objects.last())
                if form.data['rate']:
                    raw_chart_data = makeMarketStats(form.cleaned_data['market'], interval, percent, period, rate=form.cleaned_data['rate'], get_data=True)
                else:
                    raw_chart_data = makeMarketStats(form.cleaned_data['market'], interval, percent, period, get_data=True)
                chart_data = list(map(lambda x: {'t': x[0], 'y': x[1]}, raw_chart_data))
                context['chart_data'] = chart_data
            else:
                stats = []
                for market in DEFAULT_MARKETS:
                    stats.append([market, makeMarketStats(market, interval, percent, period)])
                    new_entry = ReturnedTrade.objects.create(
                        market=market,
                        interval=interval,
                        percent=percent,
                        period=period,
                        query_date=datetime.date.today(),
                        returned_trades=stats[len(stats)-1][1],
                    )
                    new_entry.save()
                stats.sort(key=lambda x: x[1], reverse=True)
                context.update(
                    success=True,
                    interval=interval,
                    percent=percent,
                    period=period,
                    stats=stats,
                )
        return render(request, self.template_name, context)

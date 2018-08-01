from django.db import models


class ReturnedTrade(models.Model):
    market = models.CharField(max_length=10)
    interval = models.IntegerField()
    percent = models.IntegerField()
    period = models.IntegerField()
    query_date = models.DateField(blank=True)
    returned_trades = models.IntegerField(blank=True)

    def __str__(self):
        return '{market}:{interval}h:{percent}%:{period}d:{tdate}: {trades} returned trades'.format(
            market=self.market,
            interval=self.interval,
            percent=self.percent,
            period=self.period,
            tdate=self.query_date,
            trades=self.returned_trades,
        )

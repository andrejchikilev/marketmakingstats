from django import forms
from .models import ReturnedTrade
from .helpers import makeMarketStats
import datetime


class MarketRequestForm(forms.ModelForm):
    class Meta:
        model = ReturnedTrade
        fields = ['market', 'interval', 'percent', 'period']

    def save(self, commit=True):
        instance = super(MarketRequestForm, self).save(commit=False)
        instance.query_date = datetime.date.today()
        instance.returned_trades = makeMarketStats(
            self.cleaned_data['market'],
            self.cleaned_data['interval'],
            self.cleaned_data['percent'],
            self.cleaned_data['period'],
        )
        if commit:
            instance.save()
        return instance

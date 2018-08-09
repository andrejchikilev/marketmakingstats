from django import forms
from .models import ReturnedTrade
from .helpers import makeMarketStats
import datetime


class MarketRequestForm(forms.ModelForm):
    rate = forms.FloatField(
        required=False,
        label='Custom market rate',
    )

    class Meta:
        model = ReturnedTrade
        fields = ['market', 'interval', 'percent', 'period']
        widgets = {
            'market': forms.widgets.TextInput(attrs={'placeholder': 'e.g.: STEEM/ETH'}),
            'interval': forms.widgets.NumberInput(attrs={'placeholder': 'hours'}),
            'percent': forms.widgets.NumberInput(attrs={'placeholder': '%'}),
            'period': forms.widgets.NumberInput(attrs={'placeholder': 'days'}),
        }

    def __init__(self, *args, **kwargs):
        super(MarketRequestForm, self).__init__(*args, **kwargs)
        self.fields['market'].required = False

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

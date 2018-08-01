from django.shortcuts import render
from django.views import View

from .forms import MarketRequestForm
from .models import ReturnedTrade


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
            form.save()
            context['success'] = True
            context['last_entry'] = '{}'.format(ReturnedTrade.objects.last())
        return render(request, self.template_name, context)

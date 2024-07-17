# recommendations/views.py

from django.shortcuts import render
from .utils import mine_frequent_itemsets

def frequent_patterns_view(request):
    frequent_itemsets = mine_frequent_itemsets()
    return render(request, 'recommendations/frequent-patterns.html', {'frequent_itemsets': frequent_itemsets})

# Create your views here.
from sales.models import Color, ShirtStyle, ShirtOrder
from django.shortcuts import render_to_response

def shirtorders(request):
    shirtorders = ShirtOrder.objects.all()
    
    return render_to_response('sales/shirtorders/list.html', {'shirtorders':shirtorders})

def shirtorderview(request, orderid):
    shirtorder = ShirtOrder.objects.get(pk=orderid)
    
    return render_to_response('sales/shirtorders/view.html', {'shirtorder':shirtorder})

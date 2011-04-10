# Create your views here.
from sales.models import Color, ShirtStyle, ShirtOrder
from django.shortcuts import render_to_response
from sales.forms import Order, OrderLine

def shirtorders(request):
    shirtorders = ShirtOrder.objects.all()
    
    return render_to_response('sales/shirtorders/list.html', {'shirtorders':shirtorders})

def shirtorderview(request, orderid):
    shirtorder = ShirtOrder.objects.get(pk=orderid)
    
    return render_to_response('sales/shirtorders/view.html', {'shirtorder':shirtorder})
    
def shirtorderadd(request):
    shirtstyles = ShirtStyle.objects.filter(Customer=None)
    return render_to_response('sales/shirtorders/add.html', {'shirtorder':Order(),'shirtstyles':shirtstyles})
    
def orderline(request):
    if "shirtstyleid" in request.GET:
        shirtstyleid = request.GET['shirtstyleid']
        shirtstyle = ShirtStyle.objects.get(pk=shirtstyleid)
        dictionary = {}
        shirtstylevariationid = None
    elif "shirtstylevariationid" in request.GET:
        shirtstylevariationid = request.GET['shirtstylevariationid']
        shirtstylevariation = ShirtStyleVariation.objects.get(pk=shirtstylevariationid)
        shirtstyle = shirtstylevariation.ShirtStyle
        shirtstyleid = shirtstyle.pk
        dictionary = {"shirtstylevariation": shirtstylevariation}
    else:
        print 'hello world'
    dictionary["orderlines"] = [OrderLine(shirtstyleid=shirtstyleid, shirtstylevariationid=shirtstylevariationid, prefix=request.GET['prefix'])]
    dictionary["shirtstyle"] = shirtstyle
    return render_to_response('sales/shirtorders/orderline.html', dictionary)

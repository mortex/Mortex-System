# Create your views here.
from sales.models import Color, ShirtStyle, ShirtOrder, ShirtStyleVariation, ShirtOrderSKU, ShirtPrice
from django.shortcuts import render_to_response
from sales.forms import Order, OrderLine
from django.template import RequestContext
from django.http import HttpResponseRedirect

def shirtorders(request):
    shirtorders = ShirtOrder.objects.all()
    return render_to_response('sales/shirtorders/list.html', {"shirtorders":shirtorders})

def shirtorderview(request, orderid):
    shirtorder = ShirtOrder.objects.get(pk=orderid)
    
    return render_to_response('sales/shirtorders/view.html', {'shirtorder':shirtorder})
    
def shirtorderadd(request, orderid=None):
    if request.method == 'GET': 
        orderlines=[]   
        if orderid != None:
            editshirtorder = ShirtOrder.objects.get(pk=orderid)
            editorderskus = ShirtOrderSKU.objects.filter(ShirtOrder=editshirtorder)
            skustylegroups = {}
            for sku in editorderskus:
                group = (sku.ShirtPrice.ShirtStyle.id, sku.ShirtStyleVariation.id if sku.ShirtStyleVariation else None, sku.Color.id)
                try:
                    skustylegroups[group].append(sku)
                except KeyError:
                    skustylegroups[group] = [sku]
            
            prefixes = (i for i in xrange(1, len(skustylegroups)+1))
            orderlines = [OrderLine(
                            shirtstyleid=shirtstyleid,
                            shirtstylevariationid=shirtstylevariationid,
                            colorid=colorid,
                            prefix=prefixes.next(),
                            existingskus=skustylegroups[(shirtstyleid, shirtstylevariationid, colorid)]
                          ) for shirtstyleid, shirtstylevariationid, colorid
                            in skustylegroups.keys()]

        shirtstyles = ShirtStyle.objects.filter(Customer=None)
        my_context = RequestContext(request, {'shirtorder':Order(instance=editshirtorder) if orderid != None else Order(),'shirtstyles':shirtstyles, "orderlines": orderlines})
        return render_to_response('sales/shirtorders/add.html',my_context)

    else:
        #created variable to test validation
        passedvalidation = True
        order = Order(request.POST)
        
        #if order is not valid, change validation variable
        if not order.is_valid():
            passedvalidation = False
            
        #created separate orderlines from post data
        orderlines = []
        for i in xrange(1, int(request.POST['rows']) + 1):
            orderlines.append(OrderLine(request.POST, prefix=i, shirtstyleid=request.POST[str(i) + "-shirtstyleid"]))
        
        #check each orderline for validity, change validation variable if any of them fail
        for orderline in orderlines:
            if not orderline.is_valid():
                passedvalidation = False
        
        #if any validation failed, send data back to page for revision
        if passedvalidation == False:
            #print orderlines[0]
            shirtstyles = ShirtStyle.objects.filter(Customer=None)
            my_context = RequestContext(request, {"orderlines": orderlines, "shirtorder": order, "shirtstyles":shirtstyles})
            return render_to_response("sales/shirtorders/add.html", my_context)
        
        #if all validation passed, save order, then save orderlines
        else:
            shirtorder = ShirtOrder(Customer=order.cleaned_data['Customer'], CustomerAddress=order.cleaned_data['CustomerAddress'], PONumber=order.cleaned_data['PONumber'])
            shirtorder.save()
            for orderline in orderlines:
                for s in xrange(1, orderline.cleaned_data["sizes"]):
                    if 'quantity'+str(s) in orderline.fields and orderline.cleaned_data['quantity'+str(s)] != None:
                        ShirtOrderSKU( ShirtOrder=shirtorder
                                     , ShirtPrice=ShirtPrice.objects.get(pk=orderline.cleaned_data['pricefkey'+str(s)])
                                     , ShirtStyleVariation=None if orderline.cleaned_data['shirtstylevariationid']==None else ShirtStyleVariation.objects.get(pk=orderline.cleaned_data['shirtstylevariationid'])
                                     , Color=orderline.cleaned_data['color']
                                     , OrderQuantity=orderline.cleaned_data['quantity'+str(s)]

                                     , Price=orderline.cleaned_data['price'+str(s)]
                                     ).save()
            return HttpResponseRedirect('/shirtorders/')
    
def orderline(request):
    if "shirtstyleid" in request.GET:
        shirtstyleid = request.GET['shirtstyleid']
        shirtstylevariationid = None
        print shirtstyleid
    elif "shirtstylevariationid" in request.GET:
        shirtstylevariationid = request.GET['shirtstylevariationid']
        shirtstylevariation = ShirtStyleVariation.objects.get(pk=shirtstylevariationid)
        shirtstyle = shirtstylevariation.ShirtStyle
        shirtstyleid = shirtstyle.pk
    else:
        print 'hello world'
    dictionary = {"orderlines":[OrderLine(shirtstyleid=shirtstyleid, shirtstylevariationid=shirtstylevariationid, prefix=request.GET['prefix'])]}
    return render_to_response('sales/shirtorders/orderline.html', dictionary)

# Create your views here.
from sales.models import Color, ShirtStyle, ShirtOrder, ShirtStyleVariation
from django.shortcuts import render_to_response
from sales.forms import Order, OrderLine
from django.template import RequestContext

def shirtorders(request):
    if request.method == 'GET':
        shirtorders = ShirtOrder.objects.all()
        my_context = RequestContext(request, {'shirtorders':shirtorders})
        return render_to_response('sales/shirtorders/list.html', my_context)
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
            my_context = {"orderlines": orderlines, "shirtorder": order}
            return render_to_response("sales/shirtorders/add.html", my_context)
        
        #if all validation passed, save order, then save orderlines
        else:
            shirtorder = ShirtOrder(CustomerAddress=order.cleaned_data['CustomerAddress'], PONumber=order.cleaned_data['PONumber'])
            shirtorder.save()
            for orderline in orderlines:
                for s in xrange(1, orderline.cleaned_data["sizes"]):
                    if 'quantity'+str(s) in orderline.fields and orderline.cleaned_data['quantity'+str(s)] != None:
                        ShirtOrderSKU( ShirtOrder=shirtorder
                                     , ShirtPrice=ShirtPrice.objects.get(pk=orderline.cleaned_data['pricefkey'+str(s)])
                                     , ShirtStyleVariation= None if orderline.cleaned_data['shirtstylevariation']==None else ShirtStyleVariation.objects.get(pk=orderline.cleaned_data['shirtstylevariation'])
                                     , Color=orderline.cleaned_data['color']
                                     , OrderQuantity=orderline.cleaned_data['quantity'+str(s)]

                                     , Price=orderline.cleaned_data['price'+str(s)]
                                     ).save()
            return super(ShirtOrderAdmin, self).add_view(request, form_url="")

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

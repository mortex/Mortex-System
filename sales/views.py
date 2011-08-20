from django.shortcuts import render_to_response
from django.db.models import Sum
from sales.models import ShirtSKUTransaction, ShirtPrice, Color, ShirtStyleVariation, ShirtSize, ShirtStyle, ShirtOrder, ShirtOrderSKU
from sales.forms import ExistingCutSSIForm, NewCutSSIForm, Order, OrderLine, ShirtSizeForm
from django.template import RequestContext
from django.http import HttpResponseRedirect


def manageinventory(request, shirtstyleid, variationid, colorid):
    if request.method == "GET":
        return manageinventory_get(request, shirtstyleid, variationid, colorid)

    else:
        transactions = []
        passedvalidation = True
        for i in xrange(1, int(request.POST["totalforms"])):
            formtype = request.POST[str(i) + "-FormType"]
            cutorder = request.POST[str(i) + "-CutOrder"]
            shirtprice = request.POST[str(i)+"-ShirtPrice"]
            if formtype == "new":
                transactions.append(NewCutSSIForm(request.POST, prefix=i, shirtprice=shirtprice, cutorder=cutorder))
            else:
                print variationid
                total_pieces = ShirtSKUTransaction.objects.filter(CutOrder=cutorder, 
                                                                ShirtPrice=ShirtPrice.objects.get(pk=shirtprice), 
                                                                Color=Color.objects.get(pk=colorid), 
                                                                ShirtStyleVariation=(ShirtStyleVariation.objects.get(pk=variationid) if variationid!=str(0) else None
                                                                )).aggregate(total_pieces=Sum('Pieces'))
                transactions.append(ExistingCutSSIForm(request.POST, prefix=i, shirtprice=shirtprice, cutorder=cutorder, total_pieces=total_pieces['total_pieces']))
            if not transactions[-1].is_valid():
                passedvalidation = False

        if passedvalidation:
            for transaction in transactions:
                if transaction.cleaned_data["Pieces"]:
                    transaction.save()
            return manageinventory_get(request, shirtstyleid, variationid, colorid)
        
        else:
            transactions.sort(key=lambda i: str(i.shirtsize), reverse=True)
            return render_to_response('sales/inventory/manage.html',RequestContext(request, {'transactionlist': transactions,'totalforms':request.POST["totalforms"]}))


def manageinventory_get(request, shirtstyleid, variationid, colorid):
    transactions = ShirtSKUTransaction.objects.filter(ShirtPrice__ShirtStyle__id=shirtstyleid).filter(Color__id=colorid)
    if variationid != '0':
        transactions = transactions.filter(ShirtStyleVariation__id=variationid)
        variation = ShirtStyleVariation.objects.get(pk=variationid)
    else: 
        variation = None
    
    annotatedtransactions = transactions.values('CutOrder','ShirtPrice','Color','ShirtStyleVariation').annotate(total_pieces=Sum('Pieces'))
    
    transactionlist = []
    prefix = 1
    for transaction in annotatedtransactions:
        cutorder = transaction['CutOrder']
        shirtprice = ShirtPrice.objects.get(pk=transaction['ShirtPrice'])
        color = Color.objects.get(pk=transaction['Color'])
        if transaction['ShirtStyleVariation']:
            shirtstylevariation = ShirtStyleVariation.objects.get(pk=transaction['ShirtStyleVariation'])
        else:
            shirtstylevariation = None
        transactionlist.append(ExistingCutSSIForm(instance=ShirtSKUTransaction(CutOrder=cutorder, 
                                                                                ShirtPrice=shirtprice, 
                                                                                Color=color, 
                                                                                ShirtStyleVariation=shirtstylevariation),total_pieces=transaction['total_pieces'],prefix=prefix))
        prefix += 1
                                                                                
    sizes = ShirtSize.objects.filter(shirtprice__ShirtStyle__id=shirtstyleid).filter(shirtprice__ColorCategory__color__id=colorid).distinct()

    for size in sizes:
        transactionlist.append(NewCutSSIForm(instance=ShirtSKUTransaction(ShirtPrice=ShirtPrice.objects
                                                                            .filter(ShirtStyle__id=shirtstyleid)
                                                                            .filter(ColorCategory__color__id=colorid)
                                                                            .get(ShirtSize__id=size.id),
                                                                        Color=Color.objects.get(pk=colorid),
                                                                        ShirtStyleVariation=variation), prefix=prefix))
        prefix += 1

    transactionlist.sort(key=lambda i: str(i.shirtsize), reverse=True)

    return render_to_response('sales/inventory/manage.html',RequestContext(request, {'transactionlist': transactionlist,'totalforms':prefix}))


# Shirt Orders

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
        editorder = ShirtOrder.objects.get(pk=orderid) if orderid != None else None
        order = Order(request.POST, instance=editorder)
        
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
            shirtorder = order.save()
            ShirtOrderSKU.objects.filter(ShirtOrder=shirtorder).delete()
            for orderline in orderlines:
                for s in xrange(1, orderline.cleaned_data["sizes"]):
                    if 'quantity'+str(s) in orderline.fields and orderline.cleaned_data['quantity'+str(s)] != None:
                        shirtprice = ShirtPrice.objects.get(pk=orderline.cleaned_data['pricefkey'+str(s)])
                        shirtstylevariation = None if orderline.cleaned_data['shirtstylevariationid']==None else ShirtStyleVariation.objects.get(pk=orderline.cleaned_data['shirtstylevariationid'])
                        color = orderline.cleaned_data['color']
                        orderquantity = orderline.cleaned_data['quantity'+str(s)]
                        price = orderline.cleaned_data['price'+str(s)]
                        ShirtOrderSKU( ShirtOrder=shirtorder
                                     , ShirtPrice=shirtprice
                                     , ShirtStyleVariation=shirtstylevariation
                                     , Color=color
                                     , OrderQuantity=orderquantity
                                     , Price=price
                                     ).save()

            return HttpResponseRedirect('/shirtorders/' + str(shirtorder.id))
    
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
    
#size management
def editsizes(request):
    if request.method == 'GET':
        sizes = ShirtSize.objects.all()
        sizeforms = []
        s = 0
        for size in sizes:
            s += 1
            sizeform = ShirtSizeForm(instance=size, prefix=s)
            sizeforms.append(sizeform)
        
        return render_to_response('sales/sizes/edit.html', RequestContext(request, {'forms':sizeforms, 'sizecount':s}))
        
    else:
        sizecount = request.POST['sizecount']
        sizeforms = []
        passedvalidation = True
        
        for s in xrange(1, int(sizecount)+1):
            sizeform = ShirtSizeForm(request.POST, prefix=s)
            sizeforms.append(sizeform)
            if not sizeform.is_valid():
                passedvalidation = False
                
        if passedvalidation == False:
            return render_to_response('sales/sizes/edit.html', RequestContext(request, {'forms':sizeforms, 'sizecount':s}))
            
        else:
            for sizeform in sizeforms:
                size = sizeform.save(commit=False)
                size.pk = sizeform.cleaned_data['pk']
                if sizeform.cleaned_data['delete'] == 0:
                    size.save()
                elif size.pk:
                    size.delete()
        
        return HttpResponseRedirect('/sizes/edit/')
        
def addsize(request):
    prefix = request.GET['prefix']
    sizeform = SizeForm(prefix=prefix)
    return render_to_response('sales/sizes/size.html', {'form':sizeform})

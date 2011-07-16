from django.shortcuts import render_to_response
from django.db.models import Sum
from sales.models import *
from sales.forms import *
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.db import transaction
from django.db.models import Q


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
                total_pieces = ShirtSKUInventory.objects.get(CutOrder=cutorder, 
                                                                ShirtPrice=ShirtPrice.objects.get(pk=shirtprice), 
                                                                Color=Color.objects.get(pk=colorid), 
                                                                ShirtStyleVariation=(ShirtStyleVariation.objects.get(pk=variationid) if variationid!=str(0) else None
                                                                ))
                transactions.append(ExistingCutSSIForm(request.POST, prefix=i, shirtprice=shirtprice, cutorder=cutorder, total_pieces=total_pieces.Inventory))
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
    shirtstylevariation = ShirtStyleVariation.objects.get(id=variationid) if variationid!="0" else None
    inventories = ShirtSKUInventory.objects.filter(ShirtPrice__ShirtStyle__id=shirtstyleid, Color__id=colorid, ShirtStyleVariation=shirtstylevariation)
    inventorylist = []
    prefix = 1
    print inventories
    for inventory in inventories:
        inventorylist.append(ExistingCutSSIForm(instance=ShirtSKUTransaction(CutOrder=inventory.CutOrder, 
                                                                             ShirtPrice=inventory.ShirtPrice, 
                                                                             Color=inventory.Color, 
                                                                             ShirtStyleVariation=shirtstylevariation),
                                                total_pieces=inventory.Inventory, prefix=prefix))
        prefix += 1
                                                                                
    sizes = ShirtSize.objects.filter(shirtprice__ShirtStyle__id=shirtstyleid).filter(shirtprice__ColorCategory__color__id=colorid).distinct()

    for size in sizes:
        inventorylist.append(NewCutSSIForm(instance=ShirtSKUTransaction(ShirtPrice=ShirtPrice.objects
                                                                            .filter(ShirtStyle__id=shirtstyleid)
                                                                            .filter(ColorCategory__color__id=colorid)
                                                                            .get(ShirtSize__id=size.id),
                                                                        Color=Color.objects.get(pk=colorid),
                                                                        ShirtStyleVariation=shirtstylevariation), prefix=prefix))
        prefix += 1

    inventorylist.sort(key=lambda i: str(i.shirtsize), reverse=True)

    return render_to_response('sales/inventory/manage.html',RequestContext(request, {'transactionlist': inventorylist,'totalforms':prefix}))


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
            for orderline in orderlines:
                delete = orderline.cleaned_data['delete']
                for s in xrange(1, orderline.cleaned_data["sizes"]):
                    instanceid = orderline.cleaned_data['instance'+str(s)]
                    orderquantity = orderline.cleaned_data['quantity'+str(s)]
                    if delete == 1 or not orderquantity or orderquantity == 0:
                        if instanceid:
                            ShirtOrderSKU.objects.get(pk=instanceid).delete()
                    else:
                        shirtprice = ShirtPrice.objects.get(pk=orderline.cleaned_data['pricefkey'+str(s)])
                        shirtstylevariation = None if orderline.cleaned_data['shirtstylevariationid']==None else ShirtStyleVariation.objects.get(pk=orderline.cleaned_data['shirtstylevariationid'])
                        color = orderline.cleaned_data['color']
                        price = orderline.cleaned_data['price'+str(s)]
                        ShirtOrderSKU(id = instanceid
                                     , ShirtOrder=shirtorder
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
    elif "shirtstylevariationid" in request.GET:
        shirtstylevariationid = request.GET['shirtstylevariationid']
        shirtstylevariation = ShirtStyleVariation.objects.get(pk=shirtstylevariationid)
        shirtstyle = shirtstylevariation.ShirtStyle
        shirtstyleid = shirtstyle.pk

    dictionary = {"orderlines":[OrderLine(shirtstyleid=shirtstyleid, shirtstylevariationid=shirtstylevariationid, prefix=request.GET['prefix'])]}
    return render_to_response('sales/shirtorders/orderline.html', dictionary)
    
    
def orderaddresses(request):
    addresses = CustomerAddress.objects.filter(shirtorder__Complete=False).distinct()
    return render_to_response('sales/shipping/orderaddresses.html', {'addresses': addresses})
    
def addshipment(request, customeraddressid=None, shipmentid=None):
    if shipmentid:
        editshipment = Shipment.objects.get(pk=shipmentid)
        customeraddressid = editshipment.CustomerAddress.pk
    else:
        editshipment = None
    orderskus = ShirtOrderSKU.objects.filter(ShirtOrder__CustomerAddress__id = customeraddressid).values("ShirtPrice__ShirtStyle", "ShirtStyleVariation", "Color").distinct()
    for ordersku in orderskus:
        ordersku['parentstyle'] = ShirtStyleVariation.objects.get(pk=ordersku['ShirtStyleVariation']) if ordersku['ShirtStyleVariation'] else ShirtStyle.objects.get(pk=ordersku['ShirtPrice__ShirtStyle'])
        ordersku['Color'] = Color.objects.get(pk=ordersku['Color'])
    if request.method == "GET":
        if not editshipment:
            shipment = ShipmentForm(instance=Shipment(CustomerAddress=CustomerAddress.objects.get(pk=customeraddressid)))
            shipmentskus = []
            i = 1
            boxcount = 0
        else:
            shipment = ShipmentForm(instance=editshipment)
            shipmentskus = []
            i = 1
            boxcount = 0
            for sku in ShipmentSKU.objects.filter(Shipment=editshipment):
                form = ShipmentSKUForm(instance=sku, prefix=i)
                form.fields['ShippedQuantity'].widget.attrs['data-savedvalue'] = sku.ShippedQuantity
                shirtorderskuid = sku.ShirtOrderSKU.id
                cutorder = sku.CutOrder
                boxnum = sku.BoxNumber
                shirtordersku, shirtsku, purchaseorder = shipmentskudetails(shirtorderskuid)
                shipmentskus.append({'form':form,'cutorder':cutorder,'purchaseorder':purchaseorder,'shirtskulabel':shirtsku,'boxnum':boxnum})
                i+=1
                boxcount = boxnum if boxnum > boxcount else boxcount
        return render_to_response('sales/shipping/addshipment.html', RequestContext(request, {'ordercolors': orderskus, 'customeraddressid':customeraddressid, 'shipment':shipment, 'shipmentskus':shipmentskus, 'skucount':i-1, 'boxcount':boxcount}))
    
    else:
        passedvalidation = True
        editshipment = Shipment.objects.get(pk=shipmentid) if shipmentid != None else None
        shipment = ShipmentForm(request.POST, instance=editshipment)
        if not shipment.is_valid():
            passedvalidation = False
        
        shipmentskus = []
        skucount = int(request.POST['skucount'])
        boxcount = 0
        forms = []
        for i in xrange(1, skucount + 1):
            postdata = request.POST
            instance = ShipmentSKU.objects.get(pk=postdata[str(i) + '-PK']) if postdata[str(i) + '-PK'] else None
            form = ShipmentSKUForm(postdata, prefix=i, instance=instance)

            forms.append(form)

            if not form.is_valid():
                passedvalidation = False
                
            cutorder = form.data[str(form.prefix) + "-CutOrder"]
            shirtorderskuid = form.data[str(form.prefix) + "-ShirtOrderSKU"]
            boxnum = form.data[str(form.prefix) + "-BoxNumber"]
            shirtordersku, shirtsku, purchaseorder = shipmentskudetails(shirtorderskuid)
            shipmentsku = {'form':form,'cutorder':cutorder,'purchaseorder':purchaseorder,'shirtskulabel':shirtsku,'boxnum':boxnum}
            shipmentskus.append(shipmentsku)
            boxcount = boxnum if boxnum > boxcount else boxcount
        
        
        if passedvalidation == False:
            return render_to_response('sales/shipping/addshipment.html', RequestContext(request, {'ordercolors': orderskus, 'customeraddressid':customeraddressid, 'shipment':shipment, 'shipmentskus':shipmentskus, 'skucount':skucount, 'boxcount':boxcount}))
        
        else:
            savedshipment = shipment.save()
            for form in forms:
                if form.cleaned_data['delete']==1 and form.cleaned_data['PK']:
                    ShipmentSKU.objects.get(pk=form.cleaned_data['PK']).delete()
                else:
                    sku = form.save(commit=False)
                    sku.Shipment = savedshipment
                    sku.save()
            return HttpResponseRedirect('/shipping/' + str(savedshipment.pk) + '/edit/')

    
def addshipmentsku(request):
    shirtordersku, shirtsku, purchaseorder = shipmentskudetails(request.GET['shirtorderskuid'])
    box = request.GET['box']
    cutorder = request.GET['cutorder']
    prefix = request.GET['prefix']
    form = ShipmentSKUForm(instance=ShipmentSKU(ShirtOrderSKU=shirtordersku, BoxNumber=box, CutOrder=cutorder),prefix=prefix)
    shipmentsku = {'form':form,'cutorder':cutorder,'purchaseorder':purchaseorder,'shirtskulabel':shirtsku,'prefix':prefix}
    skucount = 0
    return render_to_response('sales/shipping/shipmentsku.html', {'shipmentskus': [shipmentsku]})
    
def shipmentskudetails(shirtorderskuid):
    shirtordersku = ShirtOrderSKU.objects.get(pk=shirtorderskuid)
    shirtsku = shirtordersku.ShirtPrice.ShirtStyle.ShirtStyleNumber + " " + shirtordersku.Color.ColorName + " " + shirtordersku.ShirtPrice.ShirtSize.ShirtSizeAbbr
    purchaseorder = shirtordersku.ShirtOrder.PONumber
    return (shirtordersku, shirtsku, purchaseorder)
    
def searchcriteria(GET):
    if 'searchfield' in GET:
        querystring = GET['querystring']
        searchfield = GET['searchfield']
    else:
        querystring = ''
        searchfield = ''
    return (querystring, searchfield)
    
def shirtordersearch(request):
    querystring, searchfield = searchcriteria(request.GET)
    
    if searchfield == 'address':
        query = Q(CustomerAddress__Address1__contains=querystring)
    elif searchfield == 'customer':
        query = Q(Customer__CustomerName__contains=querystring)
    elif searchfield == 'ponumber':
        query = Q(PONumber__contains=querystring)
    else:
        query = Q()
        
    shirtorders = ShirtOrder.objects.filter(query)
    
    form = ShirtOrderSearchForm(initial={'searchfield':searchfield, 'querystring':querystring})
    return render_to_response('sales/shirtorders/search.html', {'shirtorders':shirtorders, 'form':form})
    
def shipmentsearch(request):
    querystring, searchfield = searchcriteria(request.GET)
    
    if searchfield == 'address':
        query = Q(CustomerAddress__Address1__contains=querystring)
    elif searchfield == 'customer':
        query = Q(CustomerAddress__Customer__CustomerName__contains=querystring)
    elif searchfield == 'tracking':
        query = Q(TrackingNumber__contains=querystring)
    else:
        query = Q()
    
    shipments = Shipment.objects.filter(query)
    
    form = ShipmentSearchForm(initial={'searchfield':searchfield, 'querystring':querystring})
    return render_to_response('sales/shipping/search.html', {'shipments':shipments, 'form':form})
    
def viewshipment(request, shipmentid):
    shipment = Shipment.objects.get(pk=shipmentid)
    return render_to_response('sales/shipping/view.html', {'shipment':shipment})
    
def editcolors(request):
    colorcategories = ColorCategory.objects.all()
    categoryforms = []
    cc = 0
    for colorcategory in colorcategories:
        cc += 1
        prefix = 'cc'+str(cc)
        categoryforms.append(ColorCategoryForm(instance=colorcategory, prefix=prefix))
    
    colors = Color.objects.all()
    colorforms = []
    c = 0
    for color in colors:
        c += 1
        prefix = 'c'+str(c)
        parentprefix = findparentprefix(categoryforms, color.ColorCategory)
        colorforms.append(ColorForm(instance=color, initial={'parentprefix':parentprefix}, prefix=prefix))
    
    return render_to_response('sales/colors/edit.html', {'categoryforms':categoryforms, 'colorforms':colorforms})
    
def findparentinstance(parentforms, lookupprefix):
    for parentform in parentforms:
        if parentform.prefix == lookupprefix:
            return parentform.instance
    return None
            
def findparentprefix(parentforms, lookupinstance):
    for parentform in parentforms:
        if parentform.instance == lookupinstance:
            return parentform.prefix

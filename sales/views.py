import re

from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.forms import formsets
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from sales.models import *
from sales.forms import *
from sales.util import *

from sales.models import *
from sales.forms import *
from sales.util import *

def findparentinstance(parentforms, lookupprefix):
    for parentform in parentforms:
        if parentform.prefix == lookupprefix:
            return parentform.instance
    return None
            
def findparentprefix(parentforms, lookupinstance):
    for parentform in parentforms:
        if parentform.instance == lookupinstance:
            return parentform.prefix

@login_required
def manageinventory(request, shirtstyleid, colorid):
    shirtstyle = ShirtStyle.objects.get(pk=shirtstyleid)
    color = Color.objects.get(pk=colorid)

    if request.method == "GET":
        return manageinventory_get(request, shirtstyleid, colorid, shirtstyle, color)

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
                total_pieces = ShirtSKUInventory.objects.get(CutOrder=cutorder, 
                                                                ShirtPrice=ShirtPrice.objects.get(pk=shirtprice), 
                                                                Color=Color.objects.get(pk=colorid)
                                                                )
                transactions.append(ExistingCutSSIForm(request.POST, prefix=i, shirtprice=shirtprice, cutorder=cutorder, total_pieces=total_pieces.Inventory))
            if not transactions[-1].is_valid():
                passedvalidation = False

        if passedvalidation:
            for transaction in transactions:
                if transaction.cleaned_data["Pieces"]:
                    savetransaction = transaction.save(commit=False)
                    if transaction.cleaned_data["FormType"] == "existing" and transaction.cleaned_data["addorsubtract"] == "subtract":
                        savetransaction.Pieces = -savetransaction.Pieces
                    savetransaction.save()
            return HttpResponseRedirect('/inventory/' + shirtstyleid + '/' + colorid)
        
        else:
            transactions.sort(key=lambda i: str(i.shirtsize), reverse=True)
            return render_to_response('sales/inventory/manage.html',RequestContext(request, {'transactionlist': transactions,'totalforms':request.POST["totalforms"], 'shirtstyle':shirtstyle, 'color':color}))


def manageinventory_get(request, shirtstyleid, colorid, shirtstyle, color):
    inventories = ShirtSKUInventory.objects.filter(ShirtPrice__ShirtStyle__id=shirtstyleid, Color__id=colorid, Inventory__gt=0)
    inventorylist = []
    prefix = 1
    for inventory in inventories:
        inventorylist.append(ExistingCutSSIForm(instance=ShirtSKUTransaction(CutOrder=inventory.CutOrder, 
                                                                             ShirtPrice=inventory.ShirtPrice, 
                                                                             Color=inventory.Color),
                                                total_pieces=inventory.Inventory, prefix=prefix))
        prefix += 1
                                                                                
    sizes = ShirtSize.objects.filter(shirtprice__ShirtStyle__id=shirtstyleid).filter(shirtprice__ColorCategory__color__id=colorid).distinct()
    sizetotals = []
    for size in sizes:
        inventories = ShirtSKUInventory.objects.filter(ShirtPrice__ShirtStyle__id=shirtstyleid, Color__id=colorid, ShirtPrice__ShirtSize=size).aggregate(totalinventory=Sum('Inventory'))
        sizetotals.append({'sizeid':size.id, 'totalinventory':inventories['totalinventory']})
        try:
            inventorylist.append(NewCutSSIForm(instance=ShirtSKUTransaction(ShirtPrice=ShirtPrice.objects
                                                                                .filter(ShirtStyle__id=shirtstyleid)
                                                                                .filter(ColorCategory__color__id=colorid)
                                                                                .get(ShirtSize__id=size.id),
                                                                            Color=Color.objects.get(pk=colorid)), prefix=prefix))
        except ShirtPrice.DoesNotExist:
            pass
        prefix += 1

    inventorylist.sort(key=lambda i: str(i.shirtsize), reverse=True)

    return render_to_response('sales/inventory/manage.html',RequestContext(request, {'transactionlist': inventorylist,'totalforms':prefix, 'shirtstyle':shirtstyle, 'color':color, 'sizetotals':sizetotals}))

def inventory_summary(request):

    invs = ShirtSKUInventory.objects.filter(
        ShirtPrice__ShirtStyle__id=request.GET["id"]
    ).order_by("ShirtPrice__ShirtSize__SortKey")
    style_name = str(ShirtStyle.objects.get(id=request.GET["id"]))

    qtys = {}
    sizes = set()
    for inv in invs:
        sizes.add(inv.ShirtPrice.ShirtSize.ShirtSizeAbbr)
        if inv.Color in qtys:
            if inv.ShirtPrice.ShirtSize.ShirtSizeAbbr in qtys[inv.Color]:
                qtys[inv.Color][inv.ShirtPrice.ShirtSize.ShirtSizeAbbr] += inv.Inventory
            else:
                qtys[inv.Color][inv.ShirtPrice.ShirtSize.ShirtSizeAbbr] = inv.Inventory
        else:
            qtys[inv.Color] = {}
            qtys[inv.Color][inv.ShirtPrice.ShirtSize.ShirtSizeAbbr] = inv.Inventory

    return render_to_response("sales/inventory/summary.html",
                              {"style_name": style_name, "qtys": qtys, "sizes": sizes})

# Shirt Orders
@login_required
def shirtorders(request):
    shirtorders = ShirtOrder.objects.all()
    return render_to_response('sales/shirtorders/list.html', {"shirtorders":shirtorders})

@login_required
def shirtorderview(request, orderid):
    shirtorder = ShirtOrder.objects.get(pk=orderid)
    orderskus = ShirtOrderSKU.objects.filter(ShirtOrder=shirtorder).order_by('ShirtPrice__ShirtStyle__ShirtStyleNumber','Color__ColorName','ShirtPrice__ShirtSize__SortKey').extra(select = {'Extension': 'Price * OrderQuantity'})
    totalpieces = 0
    totalextension = 0
    for ordersku in orderskus:
        totalpieces += ordersku.OrderQuantity
        totalextension += ordersku.Extension
    
    return render_to_response('sales/shirtorders/view.html', {'shirtorder':shirtorder, 'orderskus':orderskus, 'totalpieces':totalpieces, 'totalextension':totalextension})

@login_required
def printshirtorder(request, orderid):
    shirtorder = ShirtOrder.objects.get(pk=orderid)
    orderskus = ShirtOrderSKU.objects.filter(ShirtOrder=shirtorder).order_by('ShirtPrice__ShirtStyle__ShirtStyleNumber','Color__ColorName','ShirtPrice__ShirtSize__SortKey').extra(select = {'Extension': 'Price * OrderQuantity'})
    totalpieces = 0
    totalextension = 0
    for ordersku in orderskus:
        totalpieces += ordersku.OrderQuantity
        totalextension += ordersku.Extension

    context = {'shirtorder':shirtorder, 'orderskus':orderskus, 'totalpieces':totalpieces, 'totalextension':totalextension, "hide_links": True}
    return printtopdf(request, 'sales/shirtorders/view.html', context, "order " + shirtorder.PONumber)

@login_required
def shirtorderadd(request, orderid=None):
    if request.method == 'GET': 
        orderlines=[]   
        if orderid != None:
            editshirtorder = ShirtOrder.objects.get(pk=orderid)
            editorderskus = ShirtOrderSKU.objects.filter(ShirtOrder=editshirtorder)
            skustylegroups = {}
            for sku in editorderskus:
                group = (sku.ShirtPrice.ShirtStyle.id, sku.Color.id)
                try:
                    skustylegroups[group].append(sku)
                except KeyError:
                    skustylegroups[group] = [sku]
            
            prefixes = (i for i in xrange(1, len(skustylegroups)+1))
            orderlines = [OrderLine(
                            shirtstyleid=shirtstyleid,
                            colorid=colorid,
                            prefix=prefixes.next(),
                            existingskus=skustylegroups[(shirtstyleid, colorid)]
                          ) for shirtstyleid, colorid
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
            shirtstyles = ShirtStyle.objects.filter(Customer=None)
            my_context = RequestContext(request, {"orderlines": orderlines, "shirtorder": order, "shirtstyles":shirtstyles})
            return render_to_response("sales/shirtorders/add.html", my_context)
        
        #if all validation passed, save order, then save orderlines
        else:
            shirtorder = order.save()
            for orderline in orderlines:
                delete = orderline.cleaned_data['delete']
                for s in xrange(1, orderline.cleaned_data["sizes"]+1):
                    instanceid = orderline.cleaned_data['instance'+str(s)]
                    orderquantity = orderline.cleaned_data['quantity'+str(s)]
                    if delete == 1 or not orderquantity or orderquantity == 0:
                        if instanceid:
                            ShirtOrderSKU.objects.get(pk=instanceid).delete()
                    else:
                        shirtprice = ShirtPrice.objects.get(pk=orderline.cleaned_data['pricefkey'+str(s)])
                        color = orderline.cleaned_data['color']
                        price = orderline.cleaned_data['price'+str(s)]
                        if instanceid is None:
                            ShirtOrderSKU(ShirtOrder=shirtorder
                                         , ShirtPrice=shirtprice
                                         , Color=color
                                         , OrderQuantity=orderquantity
                                         , Price=price
                                         ).save()
                        else:
                            existingsku = ShirtOrderSKU.objects.get(pk=instanceid)
                            existingsku.ShirtOrder=shirtorder
                            existingsku.ShirtPrice=shirtprice
                            existingsku.Color=color
                            existingsku.OrderQuantity=orderquantity
                            existingsku.Price=price
                            existingsku.save()

            return HttpResponseRedirect('/shirtorders/' + str(shirtorder.id))

@login_required
def orderline(request):
    shirtstyleid = request.GET['shirtstyleid']

    dictionary = {"orderlines":[OrderLine(shirtstyleid=shirtstyleid, prefix=request.GET['prefix'])]}
    return render_to_response('sales/shirtorders/orderline.html', dictionary)
    
@login_required
def purchaseorders(request):
    purchaseorders = ShirtOrder.objects.all().order_by('DueDate')
    for po in purchaseorders:
        po.totalshirts = 0
        po.fillableshirts = 0
        skus = ShirtOrderSKU.objects.filter(ShirtOrder=po)
        for sku in skus:
            skuinventories = ShirtSKUInventory.objects.filter(ShirtPrice=sku.ShirtPrice,Color=sku.Color).aggregate(Sum('Inventory'))
            if skuinventories['Inventory__sum']:
                skuinventory = skuinventories['Inventory__sum']
            else:
                skuinventory = 0
            
            po.totalshirts += sku.OrderQuantity - sku.ShippedQuantity
            po.fillableshirts += min(skuinventory, sku.OrderQuantity - sku.ShippedQuantity)

    return render_to_response('sales/shipping/purchaseorders.html', {'purchaseorders': purchaseorders})

@login_required
def addshipment(request, customeraddressid=None, shipmentid=None):
    if shipmentid:
        editshipment = Shipment.objects.get(pk=shipmentid)
        customeraddressid = editshipment.CustomerAddress.pk
    else:
        editshipment = None
    customeraddress = CustomerAddress.objects.get(pk=customeraddressid)
    ordercolors = ShirtOrderSKU.objects.filter(ShirtOrder__CustomerAddress__id = customeraddressid).values("ShirtPrice__ShirtStyle", "Color").order_by("ShirtPrice__ShirtStyle", "Color").distinct()
    for ordercolor in ordercolors:
        #total shirts to be shipped
        ordercolor['totalshirts'] = 0
        ordercolor['fillableshirts'] = 0
        skus = ShirtOrderSKU.objects.filter(
            ShirtOrder__CustomerAddress__id = customeraddressid,
            ShirtPrice__ShirtStyle = ordercolor['ShirtPrice__ShirtStyle'],
            Color = ordercolor['Color'])
        for sku in skus:
            skuinventories = ShirtSKUInventory.objects.filter(ShirtPrice=sku.ShirtPrice,Color=sku.Color).aggregate(Sum('Inventory'))
            if skuinventories['Inventory__sum']:
                skuinventory = skuinventories['Inventory__sum']
            else:
                skuinventory = 0
            
            ordercolor['totalshirts'] += sku.OrderQuantity - sku.ShippedQuantity
            ordercolor['fillableshirts'] += min(skuinventory, sku.OrderQuantity - sku.ShippedQuantity)
                                                        
        ordercolor['parentstyle'] = ShirtStyle.objects.get(pk=ordercolor['ShirtPrice__ShirtStyle'])
        ordercolor['Color'] = Color.objects.get(pk=ordercolor['Color'])
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
        return render_to_response('sales/shipping/addshipment.html', RequestContext(request, {'ordercolors': ordercolors, 'customeraddressid':customeraddressid, 'shipment':shipment, 'shipmentskus':shipmentskus, 'skucount':i-1, 'boxcount':boxcount, 'customeraddress':customeraddress}))
    
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
            return render_to_response('sales/shipping/addshipment.html', RequestContext(request, {'ordercolors': ordercolors, 'customeraddressid':customeraddressid, 'shipment':shipment, 'shipmentskus':shipmentskus, 'skucount':skucount, 'boxcount':boxcount, 'customeraddress':customeraddress}))
        
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

@login_required
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
    
@login_required
def shirtordersearch(request):
    querystring, searchfield = searchcriteria(request.GET)
    
    if searchfield == 'address':
        query = Q(CustomerAddress__Address1__contains=querystring)
    elif searchfield == 'customer':
        query = Q(Customer__CustomerName__contains=querystring)
    elif searchfield == 'ponumber':
        query = Q(PONumber__contains=querystring)
    elif searchfield == 'shirtstylenumber':
        query = Q(shirtordersku__ShirtPrice__ShirtStyle__ShirtStyleNumber__contains=querystring)
    else:
        query = Q()
        
    shirtorders = ShirtOrder.objects.filter(query).distinct()
    
    form = ShirtOrderSearchForm(initial={'searchfield':searchfield, 'querystring':querystring})
    return render_to_response('sales/shirtorders/search.html', {'shirtorders':shirtorders, 'form':form})
    
@login_required
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
    
@login_required
def inventorysearch(request):
    querystring, searchfield = searchcriteria(request.GET)
    
    if searchfield == 'stylenumber':
        query = Q(ShirtStyleNumber__contains=querystring)
    else:
        query = Q()
        
    shirtstyles = ShirtStyle.objects.filter(query).order_by('ShirtStyleNumber')
    for shirtstyle in shirtstyles:
        shirtstyle.colors = Color.objects.filter(ColorCategory__shirtprice__ShirtStyle=shirtstyle).distinct()
        shirtstyle.colors_in_stock, shirtstyle.colors_out_of_stock = partition(
            lambda c:
                ShirtSKUInventory.objects
                                 .filter(Color=c)
                                 .filter(Inventory__gt=0)
                                 .filter(ShirtPrice__ShirtStyle=shirtstyle)
                                 .count() > 0,
            shirtstyle.colors
        )

    form = InventorySearchForm(initial={'searchfield':searchfield, 'querystring':querystring})
    return render_to_response(
        "sales/inventory/search.html",
        {"shirtstyles": shirtstyles,
         "form": form}
    )

@login_required
def shirtstylesearch(request):
    querystring, searchfield = searchcriteria(request.GET)
    
    if searchfield == 'stylenumber':
        query = Q(ShirtStyleNumber__contains=querystring)
    elif searchfield == 'knitstyle':
        query = Q(KnitStyleName__contains=querystring)
    elif searchfield == 'customer':
        query = Q(Customer__CustomerName__contains=querystring)
    else:
        query = Q()
        
    shirtstyles = ShirtStyle.objects.filter(query).order_by('ShirtStyleNumber')
        
    form = ShirtStyleSearchForm(initial={'searchfield':searchfield, 'querystring':querystring})
    return render_to_response('sales/shirtstyles/search.html', {'shirtstyles':shirtstyles, 'form':form})
    
@login_required
def viewshipment(request, shipmentid):
    shipment = Shipment.objects.get(pk=shipmentid)
    
    return render_to_response(
        'sales/shipping/view.html',
        {'shipment':shipment}
    )


@login_required
def printshipment(request, shipmentid):
    context = {"shipment": Shipment.objects.get(pk=shipmentid), "hide_links": True}
    return printtopdf(request, "sales/shipping/view.html", context, "packing list for shipment " + str(shipmentid))
    
@login_required
def printboxlabels(request, shipmentid):
    context = {"shipment": Shipment.objects.get(pk=shipmentid), "hide_links": True}
    #return printtopdf(request, "sales/shipping/boxlabels.html", context, "box labels for shipment " + str(shipmentid))
    return render_to_response('sales/shipping/boxlabels.html', context)


@login_required
def editcolors(request):
    if request.method == "GET":
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
        
        return render_to_response('sales/colors/edit.html', RequestContext(request, {'categoryforms':categoryforms, 'colorforms':colorforms, 'categorycount':cc, 'colorcount':c}))
    else:
        categorycount = request.POST['categorycount']
        colorcount = request.POST['colorcount']
        categoryforms = []
        colorforms = []
        passedvalidation = True
        postdata = request.POST

        for cc in xrange(1, int(categorycount) + 1):
            prefix = 'cc'+str(cc)
            instance = ColorCategory.objects.get(pk=postdata['cc' + str(cc) + '-pk']) if postdata['cc' + str(cc) + '-pk'] else None
            categoryform = ColorCategoryForm(request.POST, prefix=prefix, instance=instance)
            if not categoryform.is_valid():
                passedvalidation = False
                print categoryform.errors
            categoryforms.append(categoryform)
        
        for c in xrange(1, int(colorcount) + 1):
            prefix = 'c'+str(c)
            instance = Color.objects.get(pk=postdata['c' + str(c) + '-pk']) if postdata['c' + str(c) + '-pk'] else None
            colorform = ColorForm(request.POST, prefix=prefix, instance=instance)
            if not colorform.is_valid():
                passedvalidation = False
            colorforms.append(colorform)
        
        if passedvalidation == False:
            return render_to_response('sales/colors/edit.html', RequestContext(request, {'categoryforms':categoryforms, 'colorforms':colorforms, 'categorycount':cc, 'colorcount':c}))
            
        else:
            for categoryform in categoryforms:
                categoryform.save()
            
            for colorform in colorforms:
                color = colorform.save(commit=False)
                color.ColorCategory = findparentinstance(categoryforms, colorform.cleaned_data['parentprefix'])
                color.save()
            
            return HttpResponseRedirect('/colors/edit/')

@login_required
def addcategory(request):
    prefix = 'cc' + str(request.GET['prefix'])
    categoryform = ColorCategoryForm(prefix=prefix)
    return render_to_response('sales/colors/category.html', {'categoryform':categoryform})

@login_required
def addcolor(request):
    prefix = 'c' + str(request.GET['prefix'])
    parentprefix = request.GET['parentprefix']
    colorform = ColorForm(initial={'parentprefix':parentprefix}, prefix=prefix)
    return render_to_response('sales/colors/color.html', {'colorform':colorform})

#size management
@login_required
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
            pk = request.POST[str(s) + "-pk"]
            sizeform = ShirtSizeForm(request.POST, prefix=s, instance=ShirtSize.objects.get(pk=pk) if pk else None)
            sizeforms.append(sizeform)
            if not sizeform.is_valid():
                passedvalidation = False
                
        if passedvalidation == False:
            return render_to_response('sales/sizes/edit.html', RequestContext(request, {'forms':sizeforms, 'sizecount':s}))
            
        else:
            for sizeform in sizeforms:
                if sizeform.cleaned_data['delete'] == 0:
                    sizeform.save()
                elif size.pk:
                    sizeform.delete()
        
        return HttpResponseRedirect('/sizes/edit/')

@login_required
def addsize(request):
    prefix = request.GET['prefix']
    sizeform = ShirtSizeForm(prefix=prefix)
    return render_to_response('sales/sizes/size.html', {'form':sizeform})

#customer management
@login_required
def editcustomer(request, customerid=None):
    if request.method == "GET":
        if customerid:
            customer = Customer.objects.get(pk=customerid)
        else:
            customer = None

        addresses = CustomerAddress.objects.filter(Customer=customer)
        addressforms = []
        a = 0
        for address in addresses:
            a += 1
            prefix = 'a'+str(a)
            addressforms.append(CustomerAddressForm(instance=address, prefix=prefix))
            
        customerform = CustomerForm(instance=customer, initial={'addresscount':a})
        
        return render_to_response('sales/customers/edit.html', RequestContext(request, {'form':customerform, 'addressforms':addressforms}))
    else:
        addresscount = request.POST['addresscount']
        addressforms = []
        passedvalidation = True
        
        customerform = CustomerForm(request.POST)
        if not customerform.is_valid():
            passedvalidation = False
        
        for a in xrange(1, int(addresscount) + 1):
            prefix = 'a'+str(a)
            addressform = CustomerAddressForm(request.POST, prefix=prefix)
            if not addressform.is_valid():
                passedvalidation = False
            addressforms.append(addressform)
        
        if passedvalidation == False:
            return render_to_response('sales/customers/edit.html', RequestContext(request, {'form':customerform, 'addressforms':addressforms}))
            
        else:
            customer = customerform.save(commit=False)
            customer.pk = customerform.cleaned_data['pk']
            customer.save()
            
            for addressform in addressforms:
                address = addressform.save(commit=False)
                address.pk = addressform.cleaned_data['pk']
                address.Customer = customer
                address.save()
            
            return HttpResponseRedirect('/customers/' + str(customer.id) + '/edit/')

@login_required
def addcustomeraddress(request):
    prefix = 'a' + str(request.GET['prefix'])
    addressform = CustomerAddressForm(prefix=prefix)
    return render_to_response('sales/customers/address.html', {'addressform':addressform})

@login_required
def customersearch(request):
    querystring, searchfield = searchcriteria(request.GET)
    
    if searchfield == 'customername':
        query = Q(CustomerName__contains=querystring)
    elif searchfield == 'contactname':
        query = Q(customeraddress__ContactName__contains=querystring)
    else:
        query = Q()
    
    customers = Customer.objects.filter(query)
    
    form = CustomerSearchForm(initial={'searchfield':searchfield, 'querystring':querystring})
    return render_to_response('sales/customers/search.html', {'customers':customers, 'form':form})

@login_required
def add_style(request, shirtstyleid=None):
    """Add a new garment style to the database"""

    def render(form):
        return render_to_response(
            "sales/shirtstyles/add.html",
            RequestContext(request, {
                "form": form,
                "ccNames": ColorCategory.objects.all()
                                        .values_list("ColorCategoryName",
                                                     flat=True),
                "sizeNames": ShirtSize.objects.all()
                                      .values_list("ShirtSizeName", flat=True)
            })
        )

    if request.method == "GET":

        # Add
        if shirtstyleid == None:
            return render(ShirtStyleForm())

        # Edit
        else:
            return render(
                ShirtStyleForm(
                    instance=ShirtStyle.objects.get(pk=shirtstyleid)
                ),
            )

    if request.method == "POST":

        # Add (Instantiate unbound ModelForm)
        if not request.POST["pk"]:
            form = ShirtStyleForm(request.POST)

        # Edit (Bind form to existing model instance)
        else:
            form = ShirtStyleForm(
                request.POST,
                instance=ShirtStyle.objects.get(pk=request.POST["pk"])
            )

        if form.is_valid():
            form.save()
        else:
            return render(form)

        return HttpResponseRedirect("/shirtstyles/search/")

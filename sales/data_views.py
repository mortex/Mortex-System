from sales.models import CustomerAddress, ShirtStyle, ShirtPrice, ShirtStyleVariation, ShirtSKUInventory, Color, ShirtOrderSKU
from django.core import serializers
from django.http import HttpRequest, HttpResponse
from django.db.models import Sum
import json

#this function allows us to traverse relationships if necessary
def serialize(dictionary, relations=None):
    json_serializer = serializers.get_serializer("json")()
    response = HttpResponse(mimetype="application/json")
    if relations==None:
        json_serializer.serialize(dictionary, ensure_ascii=False, stream=response)
    else:
        json_serializer.serialize(dictionary, ensure_ascii=False, stream=response, relations=relations)
    
    return response
    
def styleprices(request):
    shirtstyleid = request.GET['shirtstyleid']
    colorid = request.GET['colorid']
    shirtprices = ShirtPrice.objects.filter(ColorCategory__color__exact=colorid).filter(ShirtStyle__exact=shirtstyleid)
    return serialize(shirtprices)

def customeraddresses(request):
    customerid = request.GET['customerid']
    addresses = CustomerAddress.objects.filter(Customer__exact=customerid)
    return serialize(addresses)

def shirtstyles(request):
    if "customerid" in request.GET:
        customerid = request.GET['customerid']
        shirtstyles = ShirtStyle.objects.filter(Customer__exact=customerid)
    else:
        shirtstyleid = request.GET['id']
        shirtstyles = ShirtStyle.objects.filter(id=shirtstyleid) #must be filter and not get because JSON requires an array
    
    return serialize(shirtstyles)

def shirtstylevariations(request):
    if "customerid" in request.GET:
        customerid = request.GET['customerid']
        shirtstylevariations = ShirtStyleVariation.objects.filter(Customer__exact=customerid)
        
    else:
        shirtstylevariationid = request.GET['id']
        shirtstylevariations = ShirtStyleVariation.objects.filter(id=shirtstylevariationid)
        if "getparent" in request.GET and request.GET['getparent'] == "true":
            return serialize(shirtstylevariations, relations=('ShirtStyle',))

    return serialize(shirtstylevariations)
    
def shippingorderskus(request):
    'gets the specific orders of each size of a given style/color'
    shirtstyleid = request.GET['shirtstyleid']
    variationid = request.GET['variationid']
    shirtstylevariation = ShirtStyleVariation.objects.get(pk=variationid) if variationid!=str(0) else None
    colorid = request.GET['colorid']
    addressid = request.GET['addressid']
    sizeinventories = ShirtSKUInventory.objects.filter(ShirtPrice__ShirtStyle__id=shirtstyleid, 
                                                    Color__id=colorid, 
                                                    ShirtStyleVariation=(shirtstylevariation
                                                    )).values('ShirtPrice', 'ShirtPrice__ShirtSize__ShirtSizeAbbr').annotate(total=Sum('Inventory'))

    #gets the active orders for skus of a given style/color
    allorderedpieces = ShirtOrderSKU.objects.filter(ShirtPrice__ShirtStyle__id=shirtstyleid,
                                                    Color__id=colorid,
                                                    ShirtStyleVariation=shirtstylevariation,
                                                    ShirtOrder__CustomerAddress__id=addressid)
                                                    
    #gets the inventory broken out by cut order of a given style/color
    cutinventory = ShirtSKUInventory.objects.filter(ShirtPrice__ShirtStyle__id=shirtstyleid, 
                                                    Color__id=colorid, 
                                                    ShirtStyleVariation=shirtstylevariation)

    for size in sizeinventories:
        size['abbr'] = size['ShirtPrice__ShirtSize__ShirtSizeAbbr']
        del size['ShirtPrice__ShirtSize__ShirtSizeAbbr']
        size['orderedpieces'] = [{'shirtprice':piece.ShirtPrice.id,'shirtordersku':piece.id,'orderquantity':piece.OrderQuantity-piece.ShippedQuantity,'ponumber':piece.ShirtOrder.PONumber} for piece in allorderedpieces if piece.ShirtPrice.id == size['ShirtPrice']]
        size['cutpieces'] = [{'shirtprice':piece.ShirtPrice.id,'inventory':piece.Inventory,'cutorder':piece.CutOrder} for piece in cutinventory if piece.ShirtPrice.id == size['ShirtPrice']]
                                                    
    return HttpResponse(json.dumps(list(sizeinventories)))

def shippinginventoryskus(request):
    'gets the specific cut order inventory of each size of a given style/color'
    shirtstyleid = request.GET['shirtstyleid']

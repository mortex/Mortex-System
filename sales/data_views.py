from sales.models import CustomerAddress, ShirtStyle, ShirtPrice, ShirtStyleVariation, ShirtSKUInventory, Color
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
    
def skuinventory(request):
    'gets the inventory of each size of a given style/color'
    shirtstyleid = request.GET['shirtstyleid']
    variationid = request.GET['variationid']
    colorid = request.GET['colorid']
    total_pieces = ShirtSKUInventory.objects.filter(ShirtPrice__ShirtStyle__id=shirtstyleid, 
                                                    Color__id=colorid, 
                                                    ShirtStyleVariation=(ShirtStyleVariation.objects.get(pk=variationid) if variationid!=str(0) else None
                                                    )).values('ShirtPrice', 'ShirtPrice__ShirtSize__ShirtSizeAbbr').annotate(total=Sum('Inventory'))
    return HttpResponse(json.dumps(list(total_pieces)))

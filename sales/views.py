# Create your views here.
from sales.models import Color, ShirtStyle, ShirtSKUInventory, ShirtSKU, CustomerAddress, ShirtPrice, ShirtSize, ShirtStyleVariation, Customer
from django.shortcuts import render_to_response
from django.db.models import Sum
from django.core import serializers
from django.http import HttpRequest, HttpResponse
from django.db.models import Count

def serialize(dictionary, relations=None):
    json_serializer = serializers.get_serializer("json")()
    response = HttpResponse(mimetype="application/json")
    if relations==None:
        json_serializer.serialize(dictionary, ensure_ascii=False, stream=response)
    else:
        json_serializer.serialize(dictionary, ensure_ascii=False, stream=response, relations=relations)
    
    return response
    
def styleorder(request, object_id):
    colors = Color.objects.all()
    shirtstyle = ShirtStyle.objects.get(pk=object_id)
    return render_to_response('sales/styleorder.html', {'colors': colors, 'shirtstyle': shirtstyle})

def manageinventory(request, object_id):

    shirtinventory = ShirtSKU.objects.annotate(total_inventory=Sum('shirtskuinventory__Pieces')).filter(total_inventory__gt=0)
    shirtstylecolors = Color.objects.annotate().filter(shirtsku__ShirtPrice__ShirtStyle__id=object_id)

    display_colors = {} #empty dictionary
    for color in set([sku.Color for sku in shirtinventory]): #conversion to 'set' eliminates duplicates
        display_colors[color] = [s for s in shirtinventory if s.Color == color]

    shirt_style = ShirtStyle.objects.get(pk=object_id)

    return render_to_response('sales/manageinventory.html', {'display_colors': display_colors, 'shirt_style': shirt_style, 'priced_colors': shirtstylecolors})
    
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
    
def colors(request):
    shirtstyleid = request.GET['shirtstyleid']
    colors = Color.objects.distinct().filter(ColorCategory__shirtprice__ShirtStyle__id=shirtstyleid)
    return serialize(colors)
    
def styleprices(request):
    shirtstyleid = request.GET['shirtstyleid']
    colorid = request.GET['colorid']
    shirtprices = ShirtPrice.objects.filter(ColorCategory__color__exact=colorid).filter(ShirtStyle__exact=shirtstyleid)
    return serialize(shirtprices)
    
def shirtsizes(request):
    shirtstyleid = request.GET['shirtstyleid']
    shirtsizes = ShirtSize.objects.filter(shirtprice__ShirtStyle__exact=shirtstyleid).annotate(Count('ShirtSizeAbbr'))
    return serialize(shirtsizes)

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

def customers(request):
    #customerfilter = request.GET['term']
    customers = Customer.objects.all()
    return serialize(customers)

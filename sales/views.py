# Create your views here.
from sales.models import Color, ShirtStyle, ShirtSKUInventory, ShirtSKU, CustomerAddress, ShirtPrice, ShirtSize
from django.shortcuts import render_to_response
from django.db.models import Sum
from django.core import serializers
from django.http import HttpRequest, HttpResponse
from django.db.models import Count

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
    json_serializer = serializers.get_serializer("json")()
    response = HttpResponse(mimetype="application/json")
    json_serializer.serialize(addresses, ensure_ascii=False, stream=response)
    
    return response
    
def shirtstyles(request):
    if "customerid" in request.GET:
        customerid = request.GET['customerid']
        shirtstyles = ShirtStyle.objects.filter(Customer__exact=customerid)
    else:
        shirtstyleid = request.GET['shirtstyleid']
        shirtstyles = ShirtStyle.objects.filter(id=shirtstyleid)
    
    json_serializer = serializers.get_serializer("json")()
    response = HttpResponse(mimetype="application/json")
    json_serializer.serialize(shirtstyles, ensure_ascii=False, stream=response)
    
    return response
    
def colors(request):
    shirtstyleid = request.GET['shirtstyleid']
    colors = Color.objects.annotate().filter(ColorCategory__shirtprice__ShirtStyle__id=shirtstyleid)
    
    json_serializer = serializers.get_serializer("json")()
    response = HttpResponse(mimetype="application/json")
    json_serializer.serialize(colors, ensure_ascii=False, stream=response)
    
    return response
    
def styleprices(request):
    shirtstyleid = request.GET['shirtstyleid']
    colorid = request.GET['colorid']
    
    shirtprices = ShirtPrice.objects.filter(ColorCategory__color__exact=colorid).filter(ShirtStyle__exact=shirtstyleid)
        
    json_serializer = serializers.get_serializer("json")()
    response = HttpResponse(mimetype="application/json")
    json_serializer.serialize(shirtprices, ensure_ascii=False, stream=response)
    
    return response
    
def shirtsizes(request):
    shirtstyleid = request.GET['shirtstyleid']
    
    shirtsizes = ShirtSize.objects.filter(shirtprice__ShirtStyle__exact=shirtstyleid).annotate(Count('ShirtSizeAbbr'))
    
    json_serializer = serializers.get_serializer("json")()
    response = HttpResponse(mimetype="application/json")
    json_serializer.serialize(shirtsizes, ensure_ascii=False, stream=response)
    
    return response

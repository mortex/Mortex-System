from sales.models import CustomerAddress
from django.core import serializers
from django.http import HttpRequest, HttpResponse

def serialize(dictionary, relations=None):
    json_serializer = serializers.get_serializer("json")()
    response = HttpResponse(mimetype="application/json")
    if relations==None:
        json_serializer.serialize(dictionary, ensure_ascii=False, stream=response)
    else:
        json_serializer.serialize(dictionary, ensure_ascii=False, stream=response, relations=relations)
    
    return response

def colors(request):
    shirtstyleid = request.GET['shirtstyleid']
    colors = Color.objects.distinct().filter(ColorCategory__shirtprice__ShirtStyle__id=shirtstyleid)
    return serialize(colors)
    
def styleprices(request):
    shirtstyleid = request.GET['shirtstyleid']
    colorid = request.GET['colorid']
    shirtprices = ShirtPrice.objects.filter(ColorCategory__color__exact=colorid).filter(ShirtStyle__exact=shirtstyleid)
    return serialize(shirtprices)

def customeraddresses(request):
    customerid = request.GET['customerid']
    addresses = CustomerAddress.objects.filter(Customer__exact=customerid)
    return serialize(addresses)

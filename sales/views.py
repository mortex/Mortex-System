# Create your views here.
from sales.models import StyleColor, ShirtStyle, ShirtSKUInventory, ShirtStyleSKU
from django.shortcuts import render_to_response
from django.db.models import Sum

def styleorder(request, object_id):
	colors = StyleColor.objects.all()
	shirtstyle = ShirtStyle.objects.get(pk=object_id)
	return render_to_response('sales/styleorder.html', {'colors': colors, 'shirtstyle': shirtstyle})

def manageinventory(request, object_id):
	#ss = ShirtStyle.objects.get(pk=object_id)
	#skuinventory = ShirtSKUInventory.objects.filter(ShirtStyleSKU__ShirtStylePrice__ShirtStyle__exact=object_id)
	#return render_to_response('sales/manageinventory.html', {'skuinventory': skuinventory})
	shirtstyleinventory = ShirtStyleSKU.objects.annotate(total_inventory=Sum('shirtskuinventory__Pieces')).filter(total_inventory__gt=0)
	return render_to_response('sales/manageinventory.html', {'shirtstyleinventory': shirtstyleinventory})

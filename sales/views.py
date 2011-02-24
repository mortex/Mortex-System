# Create your views here.
from sales.models import StyleColor, ShirtStyle, ShirtSKUInventory, ShirtStyleSKU
from django.shortcuts import render_to_response
from django.db.models import Sum

def styleorder(request, object_id):
    colors = StyleColor.objects.all()
    shirtstyle = ShirtStyle.objects.get(pk=object_id)
    return render_to_response('sales/styleorder.html', {'colors': colors, 'shirtstyle': shirtstyle})

def manageinventory(request, object_id):

    shirtstyleinventory = ShirtStyleSKU.objects.annotate(total_inventory=Sum('shirtskuinventory__Pieces')).filter(total_inventory__gt=0)

    display_colors = {}
    for color in set([sku.StyleColor for sku in shirtstyleinventory]):
        display_colors[color] = [s for s in shirtstyleinventory if s.StyleColor == color]

    return render_to_response('sales/manageinventory.html', {'display_colors': display_colors})

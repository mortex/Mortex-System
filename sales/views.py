from django.shortcuts import render_to_response


def inventorymanagement(request, shirtstyleid, variationid, colorid):
    inventorytransaction = ShirtSKUInventory.objects.filter(shirtprice__shirtstyle.id=shirtstyleid).filter(color.id=colorid)
    if variationid != 0:
        inventorytransaction.filter(shirtstylevariation.id=variationid)
    
    inventorytransaction.values('CutOrder','ShirtPrice').annotate(total_pieces=Sum(Pieces))

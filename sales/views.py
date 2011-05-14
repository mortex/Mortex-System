from django.shortcuts import render_to_response
from django.db.models import Sum
from sales.models import ShirtSKUInventory, ShirtPrice, Color, ShirtStyleVariation, ShirtSize
from sales.forms import ExistingCutSSIForm, NewCutSSIForm
from django.template import RequestContext
from django.http import HttpResponseRedirect

def manageinventory(request, shirtstyleid, variationid, colorid):
    if request.method == "GET":
        return manageinventory_get(request, shirtstyleid, variationid, colorid)

    else:
        transactions = []
        passedvalidation = True
        for i in xrange(1, int(request.POST["totalforms"])):
            formtype = request.POST[str(i) + "-FormType"]
            classname = NewCutSSIForm if formtype == "new" else ExistingCutSSIForm
            transactions.append(classname(request.POST, prefix=i))
            if not transactions[-1].is_valid():
                passedvalidation = False

        if passedvalidation:
            for transaction in transactions:
                if transaction.cleaned_data["Pieces"]:
                    transaction.save()
            return manageinventory_get(request, shirtstyleid, variationid, colorid)
        
        else:
            return render_to_response('sales/inventory/manage.html',RequestContext(request, {'transactionlist': transactions,'totalforms':request.POST["totalforms"]}))


def manageinventory_get(request, shirtstyleid, variationid, colorid):
    transactions = ShirtSKUInventory.objects.filter(ShirtPrice__ShirtStyle__id=shirtstyleid).filter(Color__id=colorid)
    if variationid != '0':
        transactions = transactions.filter(ShirtStyleVariation__id=variationid)
        variation = ShirtStyleVariation.objects.get(pk=variationid)
    else: 
        variation = None
    
    annotatedtransactions = transactions.values('CutOrder','ShirtPrice','Color','ShirtStyleVariation').annotate(total_pieces=Sum('Pieces'))
    
    transactionlist = []
    prefix = 1
    for transaction in annotatedtransactions:
        cutorder = transaction['CutOrder']
        shirtprice = ShirtPrice.objects.get(pk=transaction['ShirtPrice'])
        color = Color.objects.get(pk=transaction['Color'])
        if transaction['ShirtStyleVariation']:
            shirtstylevariation = ShirtStyleVariation.objects.get(pk=transaction['ShirtStyleVariation'])
        else:
            shirtstylevariation = None
        transactionlist.append(ExistingCutSSIForm(instance=ShirtSKUInventory(CutOrder=cutorder, 
                                                                                ShirtPrice=shirtprice, 
                                                                                Color=color, 
                                                                                ShirtStyleVariation=shirtstylevariation),total_pieces=transaction['total_pieces'],prefix=prefix))
        prefix += 1
                                                                                
    sizes = ShirtSize.objects.filter(shirtprice__ShirtStyle__id=shirtstyleid).filter(shirtprice__ColorCategory__color__id=colorid).distinct()

    for size in sizes:
        transactionlist.append(NewCutSSIForm(instance=ShirtSKUInventory(ShirtPrice=ShirtPrice.objects
                                                                            .filter(ShirtStyle__id=shirtstyleid)
                                                                            .filter(ColorCategory__color__id=colorid)
                                                                            .get(ShirtSize__id=size.id),
                                                                        Color=Color.objects.get(pk=colorid),
                                                                        ShirtStyleVariation=variation), prefix=prefix))
        prefix += 1

    transactionlist.sort(key=lambda i: str(i.shirtsize), reverse=True)

    return render_to_response('sales/inventory/manage.html',RequestContext(request, {'transactionlist': transactionlist,'totalforms':prefix}))

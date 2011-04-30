from django import forms
from django.forms import fields

from sales.models import ShirtOrder, ShirtOrderSKU, CustomerAddress, Color, ShirtSize, ShirtStyle, ShirtStyleVariation

class Order(forms.ModelForm):
    class Meta:
        model = ShirtOrder
        exclude = ("Complete")

class OrderLine(forms.Form):
    def __init__(self, *args, **kwargs):

        shirtstyleid = kwargs.pop("shirtstyleid")
        shirtstylevariationid = kwargs.pop("shirtstylevariationid", None)
        colorid = kwargs.pop("colorid", None)
        existingskus = kwargs.pop("existingskus", None)
        
        self.color = Color.objects.get(pk=colorid) if colorid else None
        if shirtstylevariationid != None:
            self.shirtstylevariation = ShirtStyleVariation.objects.get(pk=shirtstylevariationid)
        self.shirtstyle = ShirtStyle.objects.get(pk=shirtstyleid)

        super(OrderLine, self).__init__(*args, **kwargs)

        self.fields["shirtstylevariationid"] = forms.IntegerField(widget=forms.HiddenInput(), required=False, initial=shirtstylevariationid)

        self.fields["shirtstyleid"] = forms.IntegerField(widget=forms.HiddenInput(), initial=shirtstyleid)
        self.fields["color"] = forms.ModelChoiceField(queryset=Color.objects.distinct().filter(ColorCategory__shirtprice__ShirtStyle__id=shirtstyleid), initial=self.color, widget=forms.Select(attrs={"class":"colorselector","onChange":"selectcolor(this.value, " + str(shirtstyleid) + ", " + str(self.prefix) + ")"}))
        shirtsizes = ShirtSize.objects.filter(shirtprice__ShirtStyle__exact=shirtstyleid).distinct()
        i = 1

        self.quantitylist = []
        self.pricelist = []
        self.pricefkeylist = []

        for size in shirtsizes:
            quantityid = 'quantity'+str(i)
            priceid = 'price'+str(i)
            pricefkeyid = 'pricefkey'+str(i)
            
            try:
                sku = [sku for sku in existingskus if sku.ShirtPrice.ShirtSize == size][0]
                skuquantity = sku.OrderQuantity
                skuprice = sku.Price
            except IndexError:
                skuquantity = None
                skuprice = None
            
            self.fields[quantityid] = forms.IntegerField(label=size.ShirtSizeAbbr, initial=skuquantity, min_value=0, required=False, widget=forms.TextInput(attrs={"disabled":None, "size":"6","class":"quantity size"+str(size.pk)}))
            self.quantitylist.append(self[quantityid])
            self.fields[priceid] = forms.DecimalField(label=None, initial=skuprice, min_value=0, max_digits=8, decimal_places=2, required=False, widget=forms.TextInput(attrs={"size":"6","class":"price size"+str(size.pk)}))
            self.pricelist.append(self[priceid])
            self.fields[pricefkeyid] = forms.IntegerField(label='fkey', required=False, widget=forms.HiddenInput(attrs={"class":"pricefkey size"+str(size.pk)}))
            self.pricefkeylist.append(self[pricefkeyid])
            i+=1

        self.fieldlist = zip(self.quantitylist, self.pricelist, self.pricefkeylist)
        self.fields["sizes"] = forms.IntegerField(widget=forms.HiddenInput(), initial=i-1)

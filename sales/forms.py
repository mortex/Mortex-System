from django import forms
from django.forms import fields

from sales.models import *

class CutSSIForm(forms.ModelForm):
    'allows you to create transactions for new cut orders of a shirt SKU'
    class Meta:
        model = ShirtSKUTransaction
        widgets = {
            "Color": forms.HiddenInput(),
            "ShirtPrice": forms.HiddenInput(),
            "ShirtStyleVariation": forms.HiddenInput(),
        }
        exclude = ("Date",)
    Pieces = forms.IntegerField(required=False, min_value=0)
    def __init__(self, *args, **kwargs):
        if "instance" in kwargs:
            self.shirtsize = kwargs["instance"].ShirtPrice.ShirtSize
            self.cutorder = kwargs["instance"].CutOrder
        else:
            self.shirtsize = ShirtSize.objects.get(shirtprice__id=kwargs.pop("shirtprice"))
            self.cutorder = kwargs.pop("cutorder")
        super(CutSSIForm, self).__init__(*args, **kwargs)

class NewCutSSIForm(CutSSIForm):
    FormType = forms.CharField(initial='new', widget=forms.HiddenInput())
    CutOrder = forms.CharField(required=False)

class ExistingCutSSIForm(CutSSIForm):
    'allows you to create transactions for existing cut orders of a shirt SKU'
    class Meta:
        model = ShirtSKUTransaction
        widgets = {
            "CutOrder":forms.HiddenInput(),
            "Color": forms.HiddenInput(),
            "ShirtPrice": forms.HiddenInput(),
            "ShirtStyleVariation": forms.HiddenInput(),
        }
        exclude = ("Date",)
    FormType = forms.CharField(initial='existing', widget=forms.HiddenInput())
    def __init__(self, *args, **kwargs):
        self.totalpieces = kwargs.pop("total_pieces", None)
        super(ExistingCutSSIForm, self).__init__(*args, **kwargs)

class Order(forms.ModelForm):
    class Meta:
        model = ShirtOrder
        exclude = ("Complete")

class OrderLine(forms.Form):
    def __init__(self, *args, **kwargs):

        shirtstyleid = kwargs.pop("shirtstyleid")
        shirtstylevariationid = kwargs.pop("shirtstylevariationid", None)
        colorid = kwargs.pop("colorid", None)
        existingskus = kwargs.pop("existingskus", [])
        
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
        self.instancelist = []

        for size in shirtsizes:
            quantityid = 'quantity'+str(i)
            priceid = 'price'+str(i)
            pricefkeyid = 'pricefkey'+str(i)
            instanceid = 'instance'+str(i)
            
            try:
                sku = [sku for sku in existingskus if sku.ShirtPrice.ShirtSize == size][0]
                skuquantity = sku.OrderQuantity
                skuprice = sku.Price
                skuinstance = sku.pk
            except IndexError:
                skuquantity = None
                skuprice = None
                skuinstance = None
            
            self.fields[quantityid] = forms.IntegerField(label=size.ShirtSizeAbbr, initial=skuquantity, min_value=0, required=False, widget=forms.TextInput(attrs={"disabled":None, "size":"6","class":"quantity size"+str(size.pk)}))
            self.quantitylist.append(self[quantityid])
            self.fields[priceid] = forms.DecimalField(label=None, initial=skuprice, min_value=0, max_digits=8, decimal_places=2, required=False, widget=forms.TextInput(attrs={"size":"6","class":"price size"+str(size.pk)}))
            self.fields[instanceid] = forms.IntegerField(required=False, initial=skuinstance, widget=forms.HiddenInput())
            
            #add fields to lists
            self.pricelist.append(self[priceid])
            self.fields[pricefkeyid] = forms.IntegerField(label='fkey', required=False, widget=forms.HiddenInput(attrs={"class":"pricefkey size"+str(size.pk)}))
            self.pricefkeylist.append(self[pricefkeyid])
            self.instancelist.append(self[instanceid])
            i+=1

        self.fieldlist = zip(self.quantitylist, self.pricelist, self.pricefkeylist, self.instancelist)
        self.fields["sizes"] = forms.IntegerField(widget=forms.HiddenInput(), initial=i-1)
        self.fields['delete'] = forms.IntegerField(initial=0, widget=forms.HiddenInput())
        
class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        
class ShipmentSKUForm(forms.ModelForm):
    class Meta:
        model = ShipmentSKU
        exclude = {
            "Shipment"
        }
        widgets = {
            "ShirtOrderSKU":forms.HiddenInput(),
            "BoxNumber":forms.HiddenInput(),
            "CutOrder":forms.HiddenInput(),
            "ShippedQuantity":forms.TextInput(attrs={"class":"shippedquantity"}),
        }
    def __init__(self, *args, **kwargs):
        super(ShipmentSKUForm, self).__init__(*args, **kwargs)
        self.fields['PK'] = forms.IntegerField(required=False, initial=self.instance.pk, widget=forms.HiddenInput())
        self.fields['delete'] = forms.IntegerField(initial=0, widget=forms.HiddenInput())
        self.fields['ShippedQuantity'].widget.attrs['data-savedvalue'] = 0
        self.fields['ShippedQuantity'].widget.attrs['onChange'] = 'quantityupdated(this);'
        
class SearchForm(forms.Form):
    searchfield = forms.ChoiceField(label='Search By', widget=forms.RadioSelect())
    querystring = forms.CharField(label='Criteria', max_length=200)
    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['searchfield'].choices = self.choices
        
class ShirtOrderSearchForm(SearchForm):
    choices = [('address','Address'),('customer','Customer Name'),('ponumber','PO Number')]

class ShipmentSearchForm(SearchForm):
    choices = [('address','Address'),('customer','Customer Name'),('tracking','Tracking Number')]
    
class ColorCategoryForm(forms.ModelForm):
    class Meta:
        model = ColorCategory

class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        exclude = {
            'ColorCategory'
        }
    def __init__(self, *args, **kwargs):
        super(ColorForm, self).__init__(*args, **kwargs)
        self.fields['parentprefix'] = forms.CharField(widget=forms.HiddenInput())

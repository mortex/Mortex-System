from django import forms
from django.forms import fields, ModelForm
from django.forms.fields import DecimalField, IntegerField
from django.forms.widgets import HiddenInput, TextInput
from django.core import exceptions

from sales.models import *

from itertools import product

from templatetags.templatetags import orderform_extras

import types

def auto_error_class(field, error_class="error"):
    """
       Monkey-patch a Field instance at runtime in order to automatically add a CSS
       class to its widget when validation fails and provide any associated error
       messages via a data attribute
    """

    inner_clean = field.clean

    def wrap_clean(self, *args, **kwargs):
        try:
            return inner_clean(*args, **kwargs)
        except exceptions.ValidationError as ex:
            self.widget.attrs["class"] = self.widget.attrs.get(
                "class", ""
            ) + " " + error_class
            self.widget.attrs["title"] = ", ".join(ex.messages)
            raise ex

    field.clean = types.MethodType(wrap_clean, field, field.__class__)

    return field
    
class AutoErrorModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AutoErrorModelForm, self).__init__(*args, **kwargs)
        for f in self.fields:
            self.fields[f] = auto_error_class(self.fields[f])

def wrap_clean_dec_maker(error_class="error"):
    def wrap_clean_dec(clean_mthd):
        """
            Decorator to accomplish the same thing as the above wrap_clean (defined
            inside auto_error_class)
        """

        def new_clean_mthd(self, *args, **kwargs):
            try:
                return clean_mthd(self, *args, **kwargs)
            except ValidationError as ex:
                widget_attrs = self.fields[clean_mthd.__name__[6:]].widget.attrs
                widget_attrs["class"] = widget_attrs.get(
                    "class", ""
                ) + " " + error_class
                widget_attrs["title"] = ", ".join(ex.messages)
                raise ex

        return new_clean_mthd
    return wrap_clean_dec

class DeleteableForm(forms.Form):
    """
    Extension of Form which swallows validation failures if the form's "delete"
    field is provided and evaluates to True in a boolean context
    """

    def is_valid(self):
        if self.fields.get("delete") and self.data[str(self.prefix) + "-delete"] != "0":

            def swallow_validation_errors(f, *args, **kwargs):
                try:
                    return f(*args, **kwargs)
                except ValidationError:
                    pass

            for fld in self.fields.values():
                old_to_python = fld.to_python
                fld.to_python = lambda value: swallow_validation_errors(old_to_python, value)
                fld.validate = lambda value: True

        return super(DeleteableForm, self).is_valid()

class CutSSIForm(AutoErrorModelForm):
    'allows you to create transactions for new cut orders of a shirt SKU'
    class Meta:
        model = ShirtSKUTransaction
        widgets = {
            "Color": forms.HiddenInput(),
            "ShirtPrice": forms.HiddenInput()
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
        self.fields['Pieces'].widget.attrs = {'class':'input-mini'}

class NewCutSSIForm(CutSSIForm):
    FormType = forms.CharField(initial='new', widget=forms.HiddenInput())
    CutOrder = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'input-mini', 'placeholder':'new'}))

class ExistingCutSSIForm(CutSSIForm):
    'allows you to create transactions for existing cut orders of a shirt SKU'
    class Meta:
        model = ShirtSKUTransaction
        widgets = {
            "CutOrder":forms.HiddenInput(),
            "Color": forms.HiddenInput(),
            "ShirtPrice": forms.HiddenInput()
        }
        exclude = ("Date",)
    FormType = forms.CharField(initial='existing', widget=forms.HiddenInput())
    def __init__(self, *args, **kwargs):
        self.totalpieces = kwargs.pop("total_pieces", None)
        super(ExistingCutSSIForm, self).__init__(*args, **kwargs)
        self.fields["addorsubtract"] = forms.ChoiceField(initial="add", choices=(('add','add'),('subtract','subtract')), widget=forms.RadioSelect())

class Order(AutoErrorModelForm):
    CustomerAddress = forms.ModelChoiceField(queryset=CustomerAddress.objects.all(), label='Address')
    class Meta:
        model = ShirtOrder
    def __init__(self, *args, **kwargs):
        super(Order, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"tabindex":"1"}

class OrderLine(DeleteableForm):
    def __init__(self, *args, **kwargs):

        shirtstyleid = kwargs.pop("shirtstyleid")
        colorid = kwargs.pop("colorid", None)
        existingskus = kwargs.pop("existingskus", [])
        
        self.color = Color.objects.get(pk=colorid) if colorid else None
        self.shirtstyle = ShirtStyle.objects.get(pk=shirtstyleid)

        super(OrderLine, self).__init__(*args, **kwargs)

        self.fields["shirtstyleid"] = forms.IntegerField(widget=forms.HiddenInput(), initial=shirtstyleid)
        
        colorstyleclass = 'ss' + str(self.shirtstyle.id)
        if self.color:
            colorid = self.color.id
        else:
            colorid = ''
        self.fields["color"] = forms.ModelChoiceField(queryset=Color.objects.distinct().filter(ColorCategory__shirtprice__ShirtStyle__id=shirtstyleid), initial=self.color, widget=forms.Select(attrs={"class":"input-medium colorselector " + colorstyleclass,"onChange":"selectcolor(this, " + str(shirtstyleid) + ", " + str(self.prefix) + ", '" + colorstyleclass + "')", "tabindex":"1", "data-oldvalue":colorid}))
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
            
            self.fields[quantityid] = forms.IntegerField(label=size.ShirtSizeAbbr, initial=skuquantity, min_value=0, required=False, widget=forms.TextInput(attrs={"disabled":None, "class":"input-mini quantity size"+str(size.pk), "tabindex":"1"}))
            self.quantitylist.append(self[quantityid])
            self.fields[priceid] = forms.DecimalField(label=None, required=False, initial=skuprice, min_value=0, max_digits=8, decimal_places=2, widget=forms.TextInput(attrs={"size":"6","class":"price size"+str(size.pk)}))
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
        for f in self.fields:
            self.fields[f] = auto_error_class(self.fields[f])
        
class ShipmentForm(AutoErrorModelForm):
    class Meta:
        model = Shipment
        widgets = {
            'CustomerAddress': forms.HiddenInput(),
        }
        
class ShipmentSKUForm(AutoErrorModelForm):
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
    choices = [('address','Address'),('customer','Customer Name'),('ponumber','PO Number'),('shirtstylenumber','Garment Style Number')]

class ShipmentSearchForm(SearchForm):
    choices = [('address','Address'),('customer','Customer Name'),('tracking','Tracking Number')]
    
class InventorySearchForm(SearchForm):
    choices = [('stylenumber','Style Number')]

class CustomerSearchForm(SearchForm):
    choices = [('customername','Customer Name'),('contactname','Contact Name')]

class ShirtStyleSearchForm(SearchForm):
    choices = [('stylenumber','Style Number'),('knitstyle','Knit Style'),('customer','Customer')]
    
class ColorCategoryForm(AutoErrorModelForm):

    class Meta:
        model = ColorCategory

    def __init__(self, *args, **kwargs):
        super(ColorCategoryForm, self).__init__(*args, **kwargs)
        self.fields['pk'] = forms.IntegerField(required=False, initial=self.instance.pk, widget=forms.HiddenInput())

    @wrap_clean_dec_maker()
    def clean_ColorCategoryName(self):
        '''Ensure that ColorCategoryName does not contain "__"'''
        if "__" in self.cleaned_data["ColorCategoryName"]:
            raise ValidationError('Color category name may not contain "__"')
        return self.cleaned_data["ColorCategoryName"]

class ColorForm(AutoErrorModelForm):
    class Meta:
        model = Color
        exclude = {
            'ColorCategory'
        }
    def __init__(self, *args, **kwargs):
        super(ColorForm, self).__init__(*args, **kwargs)
        self.fields['parentprefix'] = forms.CharField(widget=forms.HiddenInput())
        self.fields['pk'] = forms.IntegerField(required=False, initial=self.instance.pk, widget=forms.HiddenInput())
        
#size management
class ShirtSizeForm(AutoErrorModelForm):

    class Meta:
        model = ShirtSize

    def __init__(self, *args, **kwargs):
        super(ShirtSizeForm, self).__init__(*args, **kwargs)
        self.fields['SortKey'].widget = forms.HiddenInput()
        self.fields['SortKey'].widget.attrs = {'class':'sort'}
        self.fields['pk'] = forms.IntegerField(required=False, initial=self.instance.pk, widget=forms.HiddenInput())
        self.fields['ShirtSizeAbbr'].widget.attrs = {'class':'digit'}
        self.fields['delete'] = forms.IntegerField(initial=0, widget=forms.HiddenInput())

    @wrap_clean_dec_maker()
    def clean_ShirtSizeName(self):
        '''Ensure that ShirtSizeName does not contain "__"'''
        if "__" in self.cleaned_data["ShirtSizeName"]:
            raise ValidationError('Shirt size name may not contain "__"')
        return self.cleaned_data["ShirtSizeName"]
        
#customer management
class CustomerForm(AutoErrorModelForm):
    class Meta:
        model = Customer
    def __init__(self, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        self.fields['pk'] = forms.IntegerField(required=False, initial=self.instance.pk, widget=forms.HiddenInput())
        self.fields['addresscount'] = forms.IntegerField(initial=0, widget=forms.HiddenInput())
        
class CustomerAddressForm(AutoErrorModelForm):
    class Meta:
        model = CustomerAddress
        exclude = ('Customer',)
    def __init__(self, *args, **kwargs):
        super(CustomerAddressForm, self).__init__(*args, **kwargs)
        self.fields['pk'] = forms.IntegerField(required=False, initial=self.instance.pk, widget=forms.HiddenInput())
        self.fields['delete'] = forms.IntegerField(initial=0, widget=forms.HiddenInput())

class ShirtStyleForm(ModelForm):
    """Form for adding/changing garment styles"""

    class Meta:
        model = ShirtStyle

    def __init__(self, *args, **kwargs):

        super(ShirtStyleForm, self).__init__(*args, **kwargs)

        # Include PK as hidden field so we can identify when we're editing an
        # existing record
        self.fields["pk"] = IntegerField(initial=self.instance.pk,
                                         widget=HiddenInput(),
                                         required=False)

        # Get all shirtprices associated with this form's ShirtStyle instance
        shirtprices = ShirtPrice.objects.filter(ShirtStyle=self.instance)

        # Add matrix fields for each size/color category combination
        for (cc, size) in product(ColorCategory.objects.all(), ShirtSize.objects.all()):
            ccName = cc.ColorCategoryName
            sizeName = size.ShirtSizeAbbr
            new_field = DecimalField(
                label=ccName + " " + sizeName,
                widget=TextInput(attrs={"size": "4"}),
                required=False
            )
            shirtprice = shirtprices.filter(ColorCategory=cc, ShirtSize=size)
            if shirtprice:
                new_field.initial = shirtprice[0].ShirtPrice
            new_field.ccName = ccName
            new_field.sizeName = size.ShirtSizeName
            unspaced_size_name = orderform_extras.unspace(size.ShirtSizeName)
            new_field.widget.attrs = {
                "class": "mcol_" + unspaced_size_name,
                "data-cc": orderform_extras.unspace(ccName),
                "data-size": unspaced_size_name,
            }
            self.fields["price__" + ccName + "__" + sizeName] = new_field

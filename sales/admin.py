from django import forms
from django.contrib import admin
from django.shortcuts import render_to_response

#Style Creation
from sales.models import ShirtStyle
from sales.models import ShirtPrice
from sales.models import ShirtSKU
from sales.models import ShirtSKUInventory
from sales.models import ShirtSize
from sales.models import ShirtStyleVariation
from sales.models import ShirtOrderSKU

class ShirtPriceInline(admin.TabularInline):
	model = ShirtPrice
	extra = 1

class ShirtStyleVariationInline(admin.TabularInline):
    model = ShirtStyleVariation
    extra = 1

class ShirtStyleAdmin(admin.ModelAdmin):
	inlines = [ShirtPriceInline, ShirtStyleVariationInline]
	search_fields = ['ShirtStyleNumber', 'ShirtStyleDescription']

class ShirtSKUInventoryInline(admin.TabularInline):
	model = ShirtSKUInventory
	extra = 5

class ShirtSKUAdmin(admin.ModelAdmin):
	model = ShirtSKU
	list_display = ['__unicode__', 'ShirtPrice', 'Color']
	list_editable = ['ShirtPrice', 'Color']
	inlines = [ShirtSKUInventoryInline]

admin.site.register(ShirtStyle, ShirtStyleAdmin)
admin.site.register(ShirtSize)

#Customer Creation
from sales.models import Customer
from sales.models import CustomerAddress

class CustomerAddressInline(admin.StackedInline):
	model = CustomerAddress
	extra = 1

class CustomerAdmin(admin.ModelAdmin):
	inlines = [CustomerAddressInline]

admin.site.register(Customer, CustomerAdmin)

#Color Management
from sales.models import ColorCategory
from sales.models import Color

class ColorInline(admin.TabularInline):
    model = Color
    extra = 3

class ColorCategoryAdmin(admin.ModelAdmin):
    inlines = [ColorInline]

admin.site.register(ColorCategory, ColorCategoryAdmin)

#Shirt Order Interface
from sales.models import ShirtOrder

class Order(forms.ModelForm):
    class Meta:
        model = ShirtOrder
        exclude = ('Complete')
        fields = ("customer", "CustomerAddress", "PONumber")
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), widget=forms.Select(attrs={"onChange":"selectcustomer(this.value)"}))
    CustomerAddress = forms.ModelChoiceField(queryset=CustomerAddress.objects.all())
    def clean_customeraddress(self):
        data=self.cleaned_data['CustomerAddress']
        if 1!=1:
            raise forms.ValidationError("Hey that's not right!")
        return data     
    
class ShirtOrderAdmin(admin.ModelAdmin):

    form = Order

    def add_view(self, request, form_url="", extra_context=None):

        if request.method == "GET":
            customers = Customer.objects.all()
            shirtstyles = ShirtStyle.objects.all()
            my_context = {"customers": customers, "shirtstyles": shirtstyles, "existing": []}
            return super(ShirtOrderAdmin, self).add_view(request, form_url="", extra_context=my_context)

        else:
            #created variable to test validation
            passedvalidation = True
            response = super(ShirtOrderAdmin, self).add_view(request, form_url="")
            order = Order(request.POST)
            
            #if order is not valid, change validation variable
            if not order.is_valid():
                passedvalidation = False
                
            #created separate orderlines from post data
            orderlines = []
            for i in xrange(1, int(request.POST['rows']) + 1):
                orderlines.append(OrderLine(request.POST, prefix=i, shirtstyleid=request.POST[str(i) + "-shirtstyleid"]))
            
            #check each orderline for validity, change validation variable if any of them fail
            for orderline in orderlines:
                if not orderline.is_valid():
                    passedvalidation = False
            
            #if any validation failed, send data back to page for revision
            if passedvalidation == False:
                print orderlines[0]
                customers = Customer.objects.all()
                shirtstyles = ShirtStyle.objects.all()
                my_context = {"customers": customers, "shirtstyles": shirtstyles, "orderlines": orderlines}
                return super(ShirtOrderAdmin, self).add_view(request, form_url="", extra_context=my_context)
            
            #if all validation passed, save order, then save orderlines
            else:
                shirtorder = ShirtOrder(CustomerAddress=order.cleaned_data['CustomerAddress'], PONumber=order.cleaned_data['PONumber'])
                shirtorder.save()
                for orderline in orderlines:
                    for s in xrange(1, orderline.cleaned_data["sizes"]):
                        if 'quantity'+str(s) in orderline.fields and orderline.cleaned_data['quantity'+str(s)] != None:
                            ShirtOrderSKU( ShirtOrder=shirtorder
                                         , ShirtPrice=ShirtPrice.objects.get(pk=orderline.cleaned_data['pricefkey'+str(s)])
                                         , ShirtStyleVariation= None if orderline.cleaned_data['shirtstylevariation']==None else ShirtStyleVariation.objects.get(pk=orderline.cleaned_data['shirtstylevariation'])
                                         , Color=orderline.cleaned_data['color']
                                         , OrderQuantity=orderline.cleaned_data['quantity'+str(s)]

                                         , Price=orderline.cleaned_data['price'+str(s)]
                                         ).save()
            return response

    class Media:
        css = {
            "all": ("css/jquery-ui-1.8.10.custom.css",)
        }
        js = ("js/jquery-1.4.4.min.js", "js/jquery-ui-1.8.10.custom.min.js", "js/jstree/jquery.jstree.js")

admin.site.register(ShirtOrder, ShirtOrderAdmin)

class OrderLine(forms.Form):
    def __init__(self, *args, **kwargs):

        shirtstyleid = kwargs.pop("shirtstyleid")
        shirtstylevariationid = kwargs.pop("shirtstylevariationid", None)

        super(OrderLine, self).__init__(*args, **kwargs)

        self.fields["shirtstylevariation"] = forms.IntegerField(widget=forms.HiddenInput(), required=False, initial=shirtstylevariationid)

        self.fields["shirtstyleid"] = forms.IntegerField(widget=forms.HiddenInput(), initial=shirtstyleid)
        self.fields["color"] = forms.ModelChoiceField(queryset=Color.objects.distinct().filter(ColorCategory__shirtprice__ShirtStyle__id=shirtstyleid), widget=forms.Select(attrs={"onChange":"selectcolor(this.value, " + str(shirtstyleid) + ", " + str(self.prefix) + ")"}))
        shirtsizes = ShirtSize.objects.filter(shirtprice__ShirtStyle__exact=shirtstyleid).distinct()
        self.fieldset = []
        i = 1

        for size in shirtsizes:
            quantityid = 'quantity'+str(i)
            priceid = 'price'+str(i)
            pricefkeyid = 'pricefkey'+str(i)
            self.fieldset.append((quantityid, priceid, pricefkeyid))
            self.fields[quantityid] = forms.IntegerField(label=size.ShirtSizeAbbr, min_value=0, required=False, widget=forms.TextInput(attrs={"disabled":None, "size":"6","class":"quantity size"+str(size.pk)}))
            self.fields[priceid] = forms.DecimalField(label=None, min_value=0, max_digits=8, decimal_places=2, required=False, widget=forms.TextInput(attrs={"size":"6","class":"price size"+str(size.pk)}))
            self.fields[pricefkeyid] = forms.IntegerField(label='fkey', required=False, widget=forms.HiddenInput(attrs={"class":"pricefkey size"+str(size.pk)}))
            i+=1

        self.fields["sizes"] = forms.IntegerField(widget=forms.HiddenInput(), initial=i-1)

def orderform(request):
    if "shirtstyleid" in request.GET:
        shirtstyleid = request.GET['shirtstyleid']
        shirtstyle = ShirtStyle.objects.get(pk=shirtstyleid)
        dictionary = {}
        shirtstylevariationid = None
    elif "shirtstylevariationid" in request.GET:
        shirtstylevariationid = request.GET['shirtstylevariationid']
        shirtstylevariation = ShirtStyleVariation.objects.get(pk=shirtstylevariationid)
        shirtstyle = shirtstylevariation.ShirtStyle
        shirtstyleid = shirtstyle.pk
        dictionary = {"shirtstylevariation": shirtstylevariation}
    else:
        print 'hello world'
    dictionary["orderlines"] = [OrderLine(shirtstyleid=shirtstyleid, shirtstylevariationid=shirtstylevariationid, prefix=request.GET['prefix'])]
    dictionary["shirtstyle"] = shirtstyle
    return render_to_response('admin/sales/form.html', dictionary)

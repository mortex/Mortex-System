import itertools
import re

from decimal import Decimal

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

#Style Creation
from sales.models import ShirtStyle
from sales.models import ShirtPrice
from sales.models import ColorCategory
from sales.models import ShirtSize
from sales.models import ShirtSKUInventory
from sales.models import ColorCategory

class ShirtPriceMatrixRow(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ShirtPriceMatrixRow, self).__init__(*args, **kwargs)
        for size in [s.ShirtSizeAbbr for s in ShirtSize.objects.all()]:
            self.fields[size] = forms.DecimalField(min_value=Decimal(0), decimal_places=2)

class ShirtStyleAdmin(admin.ModelAdmin):
	
    def add_view(self, request, form_url="", extra_context=None):

        if request.method == "POST":
            response = super(ShirtStyleAdmin, self).add_view(request, form_url="")
            new_style = ShirtStyle.objects.get(ShirtStyleNumber=request.POST["ShirtStyleNumber"])
            new_prices = []
            for param in [p for p in request.POST if p.startswith("price__") and request.POST[p] != ""]:
                match = re.match(r"price__(?P<cc>.*)__(?P<size>.*)", param)
                try:
                    cc = ColorCategory.objects.get(ColorCategoryName=match.group("cc"))
                    size = ShirtSize.objects.get(ShirtSizeAbbr=match.group("size"))
                    price = float(request.POST[param])
                except ColorCategory.DoesNotExist:
                    raise ValidationError("Invalid color category")
                except ShirtSize.DoesNotExist:
                    raise ValidationErorr("Invalid shirt size")
                except ValueError:
                    raise ValidationError("Price must be a number")
                new_prices.append(ShirtPrice( ShirtStyle=new_style
                                            , ColorCategory=cc
                                            , ShirtSize=size
                                            , ShirtPrice=price
                                            , Active=True
                                            ))
            for price in new_prices:
                price.save()
            return response

        else:
            matrix = [ShirtPriceMatrixRow(prefix="price__{0}".format(cc)) for cc in ColorCategory.objects.all()]
            my_context = {"matrix": matrix}
            return super(ShirtStyleAdmin, self).add_view(request, form_url="", extra_context=my_context)

admin.site.register(ShirtStyle, ShirtStyleAdmin)
admin.site.register(ShirtSKUInventory)
admin.site.register(ShirtSize)

#Customer Creation
from sales.models import Customer
from sales.models import CustomerAddress

class CustomerAddress(admin.StackedInline):
	model = CustomerAddress
	extra = 1

class CustomerAdmin(admin.ModelAdmin):
	inlines = [CustomerAddress]

admin.site.register(Customer, CustomerAdmin)

#Color Management
from sales.models import Color

class ColorInline(admin.TabularInline):
    model = Color
    extra = 3

class ColorCategoryAdmin(admin.ModelAdmin):
    inlines = [ColorInline]

admin.site.register(ColorCategory, ColorCategoryAdmin)

#Order Management
from sales.models import ShirtOrder

class ShirtOrderAdmin(admin.ModelAdmin):
    def add_view(self, request, form_url="", extra_context=None):
        shirtstyles = ShirtStyle.objects.all()
        my_context = {"shirtstyles": shirtstyles}
        return super(ShirtOrderAdmin, self).add_view(request, form_url="", extra_context=my_context)

admin.site.register(ShirtOrder, ShirtOrderAdmin)

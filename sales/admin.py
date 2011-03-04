import re

from django.contrib import admin
from django.core.exceptions import ValidationError

#Style Creation
from sales.models import ShirtStyle
from sales.models import ShirtPrice
from sales.models import ShirtSKU
from sales.models import ShirtSKUInventory
from sales.models import ShirtSize
from sales.models import ColorCategory

class ShirtPriceInline(admin.TabularInline):
	model = ShirtPrice
	extra = 1

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
            my_context = { "color_categories": ColorCategory.objects.all()
                         , "sizes": ShirtSize.objects.all()
                         }
            return super(ShirtStyleAdmin, self).add_view(request, form_url="", extra_context=my_context)

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

class CustomerAddress(admin.StackedInline):
	model = CustomerAddress
	extra = 1

class CustomerAdmin(admin.ModelAdmin):
	inlines = [CustomerAddress]

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

class ShirtOrderAdmin(admin.ModelAdmin):
    def add_view(self, request, form_url="", extra_context=None):
        customers = Customer.objects.all()
        shirtstyles = ShirtStyle.objects.all()
        my_context = {"customers": customers, "shirtstyles": shirtstyles}
        return super(ShirtOrderAdmin, self).add_view(request, form_url="", extra_context=my_context)
    class Media:
        css = {
            "all": ("css/jquery-ui-1.8.10.custom.css",)
        }
        js = ("js/jquery-1.4.4.min.js","js/jquery-ui-1.8.10.custom.min.js","js/jstree/jquery.jstree.js")

admin.site.register(ShirtOrder, ShirtOrderAdmin)

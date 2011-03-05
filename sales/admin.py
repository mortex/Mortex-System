from django.contrib import admin

#Style Creation
from sales.models import ShirtStyle
from sales.models import ShirtPrice
from sales.models import ShirtSKU
from sales.models import ShirtSKUInventory
from sales.models import ShirtSize
from sales.models import ShirtStyleVariation

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

from django.contrib import admin

#Style Creation
from sales.models import ShirtStyle
from sales.models import ShirtPrice
from sales.models import ColorCategory
from sales.models import ShirtSKU
from sales.models import ShirtSKUInventory


class ShirtPriceInline(admin.TabularInline):
	model = ShirtPrice
	extra = 1

class ShirtStyleAdmin(admin.ModelAdmin):
	inlines = [ShirtPriceInline]
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
admin.site.register(ColorCategory)
admin.site.register(ShirtSKU, ShirtSKUAdmin)

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

class ShirtSKUInline(admin.TabularInline):
	model = ShirtSKU
	extra = 5

class ColorAdmin(admin.ModelAdmin):
	inlines = [ShirtSKUInline]

admin.site.register(Color, ColorAdmin)

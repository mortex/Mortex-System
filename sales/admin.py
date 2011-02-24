from django.contrib import admin

#Style Creation
from sales.models import ShirtStyle
from sales.models import ShirtStylePrice
from sales.models import StyleColorCategory
from sales.models import ShirtStyleSKU
from sales.models import ShirtSKUInventory


class ShirtStylePriceInline(admin.TabularInline):
	model = ShirtStylePrice
	extra = 1

class ShirtStyleAdmin(admin.ModelAdmin):
	inlines = [ShirtStylePriceInline]
	search_fields = ['ShirtStyleNumber', 'ShirtStyleDescription']

class ShirtSKUInventoryInline(admin.TabularInline):
	model = ShirtSKUInventory
	extra = 5

class ShirtStyleSKUAdmin(admin.ModelAdmin):
	model = ShirtStyleSKU
	list_display = ['__unicode__', 'ShirtStylePrice', 'StyleColor']
	list_editable = ['ShirtStylePrice', 'StyleColor']
	inlines = [ShirtSKUInventoryInline]

admin.site.register(ShirtStyle, ShirtStyleAdmin)
admin.site.register(StyleColorCategory)
admin.site.register(ShirtStyleSKU, ShirtStyleSKUAdmin)

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
from sales.models import StyleColor

class ShirtStyleSKUInline(admin.TabularInline):
	model = ShirtStyleSKU
	extra = 5

class StyleColorAdmin(admin.ModelAdmin):
	inlines = [ShirtStyleSKUInline]

admin.site.register(StyleColor, StyleColorAdmin)

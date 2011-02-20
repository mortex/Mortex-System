from django.contrib import admin

#Style Creation
from sales.models import ShirtStyle
from sales.models import ShirtStylePrice
from sales.models import StyleColorCategory

class ShirtStylePriceInline(admin.TabularInline):
	model = ShirtStylePrice
	extra = 1

class ShirtStyleAdmin(admin.ModelAdmin):
	inlines = [ShirtStylePriceInline]

admin.site.register(ShirtStyle, ShirtStyleAdmin)
admin.site.register(StyleColorCategory)

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

admin.site.register(StyleColor)

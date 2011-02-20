from sales.models import ShirtStyles
from sales.models import ShirtStyleSKUs
from sales.models import ShirtStyleColors
from sales.models import ShirtColors
from django.contrib import admin

class ShirtStyleSKUsInline(admin.TabularInline):
	model = ShirtStyleSKUs
	extra = 1
	
class ShirtStyleColorsAdmin(admin.ModelAdmin):
	inlines = [ShirtStyleSKUsInline]

class ShirtStyleColorsInline(admin.TabularInline):
	model = ShirtStyleColors
	extra = 1

class ShirtStylesAdmin(admin.ModelAdmin):
	inlines = [ShirtStyleColorsInline]

admin.site.register(ShirtStyles, ShirtStylesAdmin)
admin.site.register(ShirtColors)
admin.site.register(ShirtStyleColors, ShirtStyleColorsAdmin)
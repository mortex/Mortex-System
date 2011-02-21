# Create your views here.
from sales.models import StyleColor, ShirtStyle
from django.shortcuts import render_to_response

def styleorder(request, object_id):
	colors = StyleColor.objects.all()
	shirtstyle = ShirtStyle.objects.get(pk=object_id)
	return render_to_response('sales/styleorder.html', {'colors': colors, 'shirtstyle': shirtstyle})

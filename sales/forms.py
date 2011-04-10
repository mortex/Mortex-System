from django import forms
from django.forms import fields

from sales.models import ShirtOrder, ShirtOrderSKU, CustomerAddress

class Order(forms.ModelForm):
    class Meta:
        model = ShirtOrder
        exclude = ("Complete")
    CustomerAddress = forms.ModelChoiceField(label="Address",queryset=CustomerAddress.objects.none())

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

from django import forms
from sales.models import ShirtSKUInventory, ShirtSize

class CutSSIForm(forms.ModelForm):
    'allows you to create transactions for new cut orders of a shirt SKU'
    class Meta:
        model = ShirtSKUInventory
        widgets = {
            "Color": forms.HiddenInput(),
            "ShirtPrice": forms.HiddenInput(),
            "ShirtStyleVariation": forms.HiddenInput(),
        }
        exclude = ("Date",)
    Pieces = forms.IntegerField(required=False, min_value=0)
    def __init__(self, *args, **kwargs):
        if "instance" in kwargs:
            self.shirtsize = kwargs["instance"].ShirtPrice.ShirtSize
            self.cutorder = kwargs["instance"].CutOrder
        else:
            self.shirtsize = ShirtSize.objects.get(shirtprice__id=kwargs.pop("shirtprice"))
            self.cutorder = kwargs.pop("cutorder")
        super(CutSSIForm, self).__init__(*args, **kwargs)

class NewCutSSIForm(CutSSIForm):
    FormType = forms.CharField(initial='new', widget=forms.HiddenInput())
    CutOrder = forms.CharField(required=False)

class ExistingCutSSIForm(CutSSIForm):
    'allows you to create transactions for existing cut orders of a shirt SKU'
    class Meta:
        model = ShirtSKUInventory
        widgets = {
            "CutOrder":forms.HiddenInput(),
            "Color": forms.HiddenInput(),
            "ShirtPrice": forms.HiddenInput(),
            "ShirtStyleVariation": forms.HiddenInput(),
        }
        exclude = ("Date",)
    FormType = forms.CharField(initial='existing', widget=forms.HiddenInput())
    def __init__(self, *args, **kwargs):
        self.totalpieces = kwargs.pop("total_pieces", None)
        super(ExistingCutSSIForm, self).__init__(*args, **kwargs)

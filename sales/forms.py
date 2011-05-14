

class ShirtSKUInventoryForm(forms.ModelForm):
    class Meta:
        model = ShirtSKUInventory
        widgets = {
            "Color": HiddenInput(),
            "ShirtPrice": HiddenInput(),
            "ShirtStyleVariation": HiddenInput(),
        }

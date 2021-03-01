from django import forms
from menu.models import Order, Menu


class MenuForm(forms.ModelForm):
    """Form-level validation to ensure that options are always clean"""
    def clean_options(self):
        options = self.cleaned_data['options']
        options = filter(lambda o: isinstance(o, str), options)
        options = map(lambda o: o.strip(), options)
        options = filter(bool, options)
        options = list(options)
        if not options:
            raise forms.ValidationError('the options are invalid')
        return options

    class Meta:
        model = Menu
        fields = ['options', 'date']


class OrderForm(forms.ModelForm):
    """Form-level validation to ensure that orders wont change after the cut"""
    def clean(self):
        cleaned_data = super(OrderForm, self).clean()
        if self.instance.is_expired:
            raise forms.ValidationError(
                'it\'s too late! you can\'t change your selection now 😢')

        return cleaned_data

    class Meta:
        model = Order
        fields = ['selected', 'notes']

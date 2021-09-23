from django import forms

from core.fields import BooleanSelectField
from .models import User


class UserForm(forms.ModelForm):
    """
    Form for dealing with a User model.
    """

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'username',
            'is_manager',
            'site',
        ]

    def __init__(self, remove_fields=False, *args, **kwargs):
        self.remove_fields = remove_fields
        super().__init__(*args, **kwargs)

        self.fields['first_name'].required = True
        self.fields['email'].required = True
        self.fields['is_manager'] = BooleanSelectField()

        if remove_fields:
            del self.fields['is_manager']
            del self.fields['site']

    def clean(self):
        cleaned_data = super().clean()

        if not self.remove_fields:
            # Ensure the site field is populated if the User is not a manager.
            is_manager = bool(cleaned_data.get('is_manager'))
            site = cleaned_data.get('site')

            if not is_manager and site is None:
                raise forms.ValidationError(
                    {'site': 'Site must be populated for a non-manager user.'}
                )

            # Remove specific Site if the user is a manager.
            if is_manager:
                cleaned_data['site'] = None

        return cleaned_data

from django import forms

from .models import Site, Table


class EmailTemplateForm(forms.Form):
    """
    Form for parsing the data for updating an email template.
    """

    template = forms.CharField(required=True)
    email_subject = forms.CharField(required=True)
    email_content = forms.CharField(required=True)

    def save(self, site):
        """
        Save the data to the correct email template.
        """
        template = self.cleaned_data.get('template')
        email_subject = self.cleaned_data.get('email_subject')
        email_content = self.cleaned_data.get('email_content')

        if template == 'updated':
            site.client_email_booking_updated_subject = email_subject
            site.client_email_booking_updated_content = email_content
        elif template == 'cancelled':
            site.client_email_booking_cancelled_subject = email_subject
            site.client_email_booking_cancelled_content = email_content
        elif template == 'reminder':
            site.client_email_booking_reminder_subject = email_subject
            site.client_email_booking_reminder_content = email_content
        elif template == 'admin-created':
            site.admin_email_booking_created_subject = email_subject
            site.admin_email_booking_created_content = email_content
        else:
            site.client_email_booking_created_subject = email_subject
            site.client_email_booking_created_content = email_content

        site.save()


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        exclude = []


class BaseTableFormSet(forms.BaseInlineFormSet):
    def clean(self):
        """
        Checks that no two tables have the same seats.
        """
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return

        tables_names = []

        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue

            table_name = form.cleaned_data.get('table_name')
            if table_name in tables_names:
                form.add_error('table_name', 'You cannot have two tables with the same name.')
                form.add_error('number_of_seats', '')
            else:
                tables_names.append(table_name)


TableFormSet = forms.inlineformset_factory(
    Site,
    Table,
    form=TableForm,
    formset=BaseTableFormSet,
    fields=['table_name', 'number_of_seats'],
    extra=0,
    min_num=1,
    can_delete=True,
)

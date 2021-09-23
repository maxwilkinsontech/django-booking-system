from django.forms import Select, TypedChoiceField


def BooleanSelectField(**kwargs):
    return TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=((True, 'Yes'), (False, 'No')),
        widget=Select,
        required=True,
        **kwargs,
    )

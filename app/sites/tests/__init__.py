from model_bakery import baker


def generate_phone_number():
    return '+447713155097'


baker.generators.add(
    'phonenumber_field.modelfields.PhoneNumberField', generate_phone_number
)

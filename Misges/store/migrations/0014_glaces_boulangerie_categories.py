from django.db import migrations, models


def create_default_categories(apps, schema_editor):
    Category = apps.get_model('store', 'Category')
    for name in ('Glaces', 'Boulangerie'):
        Category.objects.get_or_create(name=name)


def remove_default_categories(apps, schema_editor):
    Category = apps.get_model('store', 'Category')
    Category.objects.filter(name__in=('Glaces', 'Boulangerie')).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0013_product_image_background_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='unit',
            field=models.CharField(
                choices=[
                    ('kg', 'Kilogramme'),
                    ('l', 'Litre'),
                    ('pièce', 'Pièce'),
                    ('sachet', 'Sachet'),
                    ('boîte', 'Boîte'),
                    ('cornet', 'Cornet'),
                    ('pot', 'Pot'),
                    ('baguette', 'Baguette'),
                    ('paquet', 'Paquet'),
                ],
                default='pièce',
                max_length=20,
                verbose_name='Unité',
            ),
        ),
        migrations.RunPython(create_default_categories, remove_default_categories),
    ]

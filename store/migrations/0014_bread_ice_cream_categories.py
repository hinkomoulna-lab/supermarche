from django.db import migrations


def add_sales_categories(apps, schema_editor):
    Category = apps.get_model('store', 'Category')
    for name in ['Pain', 'Glaces']:
        Category.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0013_product_image_background_image'),
    ]

    operations = [
        migrations.RunPython(add_sales_categories, migrations.RunPython.noop),
    ]

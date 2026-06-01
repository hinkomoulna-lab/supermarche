from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0007_product_code_product_min_stock_product_unit_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='saleitem',
            name='quantity',
            field=models.DecimalField(max_digits=10, decimal_places=2),
        ),
    ]

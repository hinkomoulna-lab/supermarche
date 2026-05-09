from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0012_burgundy_theme'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.FileField(blank=True, upload_to='products/', verbose_name='Image article'),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='background_image',
            field=models.FileField(blank=True, upload_to='backgrounds/', verbose_name='Image de fond'),
        ),
    ]

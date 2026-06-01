from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0022_stockloss'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storesettings',
            name='theme',
            field=models.CharField(choices=[('burgundy', 'Rouge bordeaux'), ('blue', 'Bleu moderne'), ('green', 'Vert commerce'), ('dark', 'Sombre'), ('light', 'Clair')], default='burgundy', max_length=20, verbose_name='Thème'),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_alter_saleitem_quantity'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoreSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('store_name', models.CharField(default='Supermarché', max_length=150, verbose_name='Nom du magasin')),
                ('logo', models.FileField(blank=True, upload_to='logos/', verbose_name='Logo')),
                ('theme', models.CharField(choices=[('blue', 'Bleu moderne'), ('green', 'Vert commerce'), ('dark', 'Sombre'), ('light', 'Clair')], default='blue', max_length=20, verbose_name='Thème')),
                ('invoice_layout', models.CharField(choices=[('classic', 'Classique'), ('compact', 'Compacte'), ('modern', 'Moderne')], default='classic', max_length=20, verbose_name='Disposition de facture')),
            ],
            options={
                'verbose_name': 'Paramètres du magasin',
                'verbose_name_plural': 'Paramètres du magasin',
            },
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0046_add_label_settings'),
    ]

    operations = [
        migrations.CreateModel(
            name='PurchasePriceHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Ancien prix d'achat")),
                ('new_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Nouveau prix d'achat")),
                ('source', models.CharField(choices=[('manual', 'Modification manuelle'), ('supply', 'Approvisionnement')], default='manual', max_length=20, verbose_name='Source')),
                ('changed_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de modification')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='price_history', to='store.product', verbose_name='Produit')),
            ],
            options={
                'verbose_name': "Historique prix d'achat",
                'verbose_name_plural': "Historique des prix d'achat",
                'ordering': ['-changed_at'],
            },
        ),
    ]

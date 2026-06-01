from django.db import migrations, models
import datetime
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0024_expense_investment_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='carton_size',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=10, verbose_name='Paquets par carton'),
        ),
        migrations.CreateModel(
            name='StockSupply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Quantité reçue')),
                ('supply_mode', models.CharField(choices=[('piece', 'Pièce'), ('paquet', 'Paquet'), ('carton', 'Carton')], default='piece', max_length=10, verbose_name='Conditionnement')),
                ('units_per_package', models.DecimalField(decimal_places=2, default=1, max_digits=10, verbose_name='Unités par paquet')),
                ('packages_per_carton', models.DecimalField(decimal_places=2, default=1, max_digits=10, verbose_name='Paquets par carton')),
                ('total_units', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Unités ajoutées au stock')),
                ('unit_cost_price', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name="Prix d'achat unitaire (FCFA)")),
                ('unit_sale_price', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Prix de vente unitaire (FCFA)')),
                ('total_cost', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Coût total approvisionnement (FCFA)')),
                ('date', models.DateField(default=datetime.date.today, verbose_name="Date d'approvisionnement")),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplies', to='store.product')),
            ],
            options={
                'verbose_name': 'Approvisionnement',
                'verbose_name_plural': 'Approvisionnements',
                'ordering': ['-date', '-created_at'],
            },
        ),
    ]

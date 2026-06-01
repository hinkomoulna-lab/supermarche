from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0023_default_burgundy_theme'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='category',
            field=models.CharField(choices=[('amenagement_boutique', 'Aménagement boutique'), ('achat_materiel', 'Achat matériel'), ('carburant', 'Carburant'), ('credit_telephonique', 'Crédit téléphonique'), ('nourriture', 'Nourriture'), ('loyer', 'Loyer'), ('wifi', 'Abonnement wifi'), ('salaire_proprietaire', 'Mon salaire'), ('salaire_employe', 'Salaire employé'), ('autre', 'Autre')], default='autre', max_length=120, verbose_name='Catégorie'),
        ),
    ]

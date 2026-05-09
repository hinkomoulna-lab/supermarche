from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0010_appfeature'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='category',
            field=models.CharField(choices=[('carburant', 'Carburant'), ('credit_telephonique', 'Crédit téléphonique'), ('nourriture', 'Nourriture'), ('loyer', 'Loyer'), ('wifi', 'Abonnement wifi'), ('salaire_proprietaire', 'Mon salaire'), ('salaire_employe', 'Salaire employé'), ('autre', 'Autre')], default='autre', max_length=120, verbose_name='Catégorie'),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='monthly_expense_limit',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Limite mensuelle de dépenses (FCFA)'),
        ),
    ]

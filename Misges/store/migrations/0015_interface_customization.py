from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0014_bread_ice_cream_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='storesettings',
            name='card_size',
            field=models.CharField(
                choices=[
                    ('small', 'Petits cadres'),
                    ('medium', 'Cadres moyens'),
                    ('large', 'Grands cadres'),
                ],
                default='medium',
                max_length=20,
                verbose_name='Taille des cadres',
            ),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='font_family',
            field=models.CharField(
                choices=[
                    ('system', 'Police système'),
                    ('serif', 'Sérif élégante'),
                    ('rounded', 'Arrondie'),
                    ('mono', 'Monospace'),
                ],
                default='system',
                max_length=20,
                verbose_name='Police de l’interface',
            ),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='interface_layout',
            field=models.CharField(
                choices=[
                    ('comfortable', 'Confortable'),
                    ('compact', 'Compacte'),
                    ('wide', 'Large'),
                ],
                default='comfortable',
                max_length=20,
                verbose_name='Disposition de l’interface',
            ),
        ),
    ]

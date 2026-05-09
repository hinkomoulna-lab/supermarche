from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0009_storesettings'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppFeature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=180, verbose_name='Fonctionnalité')),
                ('description', models.TextField(verbose_name='Description')),
                ('code_notes', models.TextField(blank=True, verbose_name='Notes de code')),
                ('status', models.CharField(choices=[('idea', 'Idée'), ('planned', 'À faire'), ('coding', 'En cours'), ('done', 'Terminé')], default='idea', max_length=20, verbose_name='Statut')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Fonctionnalité',
                'verbose_name_plural': 'Fonctionnalités',
                'ordering': ['status', '-updated_at'],
            },
        ),
    ]

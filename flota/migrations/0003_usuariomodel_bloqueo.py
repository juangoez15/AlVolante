from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flota', '0002_usuariomodel_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuariomodel',
            name='intentos_fallidos',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='usuariomodel',
            name='bloqueado_hasta',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

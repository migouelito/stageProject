# Generated by Django 5.1.6 on 2025-04-10 08:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('utilisateurs', '0006_alter_user_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
    ]

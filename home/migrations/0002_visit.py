# Generated by Django 5.1.5 on 2025-02-17 17:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Visit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('path', models.CharField(max_length=255)),
                ('ip', models.GenericIPAddressField()),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]

# Generated by Django 3.2.8 on 2021-11-02 17:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('razorback', '0002_auto_20211101_2017'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='link',
            unique_together={('point_a', 'point_b')},
        ),
    ]
# Generated by Django 4.2.8 on 2024-01-04 05:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ecommapp", "0005_cart_qty"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cart", name="qty", field=models.IntegerField(default=1),
        ),
    ]
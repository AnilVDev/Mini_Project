# Generated by Django 4.2.5 on 2023-10-10 12:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_billingaddress_order_shippingaddress_orderitem_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('Processing', 'Processing'), ('Confirmed', 'Confirmed'), ('Shipped', 'Shipped'), ('Out for Delivery', 'Out for Delivery'), ('Delivered', 'Delivered'), ('Cancelled', 'Cancelled')], default='Processing', max_length=100),
        ),
    ]

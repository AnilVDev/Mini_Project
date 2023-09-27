from django import template

register = template.Library()

@register.filter(name='filter_brand')
def filter_brand(products, brand_name):
    # Implement your filter logic here
    return products.filter(brand__name=brand_name)
from .models import Category
# so links can be used by all templates
# requested by templates
# returns dictionary of data as context
def menu_links(request):
    links = Category.objects.all()
    return dict(links=links) 

def menu_three(request):
    three = Category.objects.all()[:3]
    return dict(three=three)

    
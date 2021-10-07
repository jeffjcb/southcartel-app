from .models import Product, Variation, ViewedProduct, ReviewRating
from accounts.models import FavoriteItem, Preferences
from orders.models import OrderProduct
from carts.models import CartItem

def critical_products(request):
    crit_products = Product.objects.filter(stock__lte = 10).order_by('stock')[:6]
    return dict(crit_products=crit_products) 




def update_stock(request):
    # Updates stock
    try:
        asku = 0
        bsku = 0
        variation = Variation.objects.filter(is_active=True)
        for var in variation:
            specific_var = Variation.objects.filter(product__id=var.product.id)
            # if marami
            if specific_var.count() > 1:
                # bawat product 
                for spec in specific_var:
                    asku += spec.stock
                Product.objects.filter(id=spec.product.id).update(stock=asku)
                asku=0
                
            else:
                bsku = var.stock
                Product.objects.filter(id=var.product.id).update(stock=bsku)
                bsku = 0
    except:
        pass
    return dict()


def gather_preferences(request):
    viewed = ViewedProduct.objects.all()
    favorites = FavoriteItem.objects.all()
    bought = OrderProduct.objects.all()
    cart = CartItem.objects.all()
    ratings = ReviewRating.objects.all()

    for v in viewed:
        Preferences.objects.update_or_create(user=v.user, product=v.product, rating=1)


    for c in cart:
        Preferences.objects.update_or_create(user=c.user, product=c.product, rating=3)
    

    for f in favorites:
        Preferences.objects.update_or_create(user=f.user, product=f.product, rating=4)

        # di pa gumagana
        # elif Preferences.objects.filter(user=c.user, product=c.product, rating__lte=3) not in cart:
        #     preferences = Preferences.objects.filter(user=c.user, product=c.product, rating__lte=3).delete()


    for b in bought:
        Preferences.objects.update_or_create(user=b.user, product=b.product, rating=5)

    for r in ratings:
        Preferences.objects.update_or_create(user=b.user, product=b.product, rating=r.rating)
    #     else:
    #         preferences = Preferences(user=b.user, product=b.product, rating=r.rating)
    #         preferences.save()
    #         pass



    return dict()



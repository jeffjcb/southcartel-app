from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# Create your views here.
#get session id
def _cart_id(request):
    cart = request.session.session_key
    #if there is no session
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):

    current_user = request.user
     #get product
    #if single product is clicked to add to cart
    product = Product.objects.get(id=product_id) #get the productid from the url to get the product
    #if authenticated
    if current_user.is_authenticated:
        #get variations
        product_variation = []
        if request.method == 'POST':     
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)

                except:
                    pass
        #GET CART ITEM
        #put product inside the cart/session
        #when you put the product inside the cart, it becomes a cart item
        #if cart item exists
        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()
        if is_cart_item_exists:
            #get the products associated with the cart/session
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            ex_var_list=[]
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                #this stores the variations
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                #increase cart item quantity if it is in already
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                try:
                    vary = Variation.objects.get(product=product, variation_value=product_variation[0])
                    if item.quantity >= vary.stock:
                        messages.error(request, 'Sorry, unfortunately you can no longer add any more of those item(s) to your cart.')
                        item.quantity = vary.stock
                        item.save()

                    elif item.quantity >= product.stock:
                        messages.error(request, 'Sorry, unfortunately you can no longer add any more of those item(s) to your cart.')
                        item.quantity = product.stock
                        item.save()
                    else:
                        item.quantity += 1
                        item.save()
                except:
                    if item.quantity >= product.stock:
                        messages.error(request, 'Sorry, unfortunately you can no longer add any more of those item(s) to your cart.')
                        item.quantity = product.stock
                        item.save()
                    else:
                        item.quantity += 1
                        item.save()

            else:
                #create new cart item
                item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                #check if variation is empty
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                #if added to cart again, add 1
                # cart_item.quantity += 1
                item.save()
                #if cart item does not exist create a cart item
        else:
            cart_item = CartItem.objects.create(
                product = product,
                quantity = 1,
                user = current_user,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        return redirect('cart')

    #If not authenticated
    else:

        #get variations
        product_variation = []
        if request.method == 'POST':     
            for item in request.POST:
                key = item
                value = request.POST[key]
                
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass
        #get cart
        try:
            #cart id = session, if no session, create a session
            cart = Cart.objects.get(cart_id=_cart_id(request)) #get cart using cart id present in the session key
        except Cart.DoesNotExist:
            #if no cart id exists with the user, create a cart id 
            cart = Cart.objects.create(
                cart_id = _cart_id(request)
            )
        cart.save()

        #GET CART ITEM
        #put product inside the cart/session
        #when you put the product inside the cart, it becomes a cart item

        #if cart item exists
        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        if is_cart_item_exists:
            #get the products associated with the cart/session
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            #existing variations in cart 
            #if current variation is existing in the cart, add item to the cart item, else create new cart item
            ex_var_list=[]
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                #this stores the variations
                ex_var_list.append(list(existing_variation))
                id.append(item.id)
            if product_variation in ex_var_list:
                #increase cart item quantity if it is in already
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                try:
                    vary = Variation.objects.get(product=product, variation_value=product_variation[0])
                    if item.quantity >= vary.stock:
                        messages.error(request, 'Sorry, unfortunately you can no longer add any more of those item(s) to your cart.')
                        item.quantity = vary.stock
                        item.save()

                    elif item.quantity >= product.stock:
                        messages.error(request, 'Sorry, unfortunately you can no longer add any more of those item(s) to your cart.')
                        item.quantity = product.stock
                        item.save()
                    else:
                        item.quantity += 1
                        item.save()
                except:
                    if item.quantity >= product.stock:
                        messages.error(request, 'Sorry, unfortunately you can no longer add any more of those item(s) to your cart.')
                        item.quantity = product.stock
                        item.save()
                    else:
                        item.quantity += 1
                        item.save()
            else:
                #create new cart item
                item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                #check if variation is empty
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                #if added to cart again, add 1
                # cart_item.quantity += 1
                item.save()
                #if cart item does not exist create a cart item
        else:
            cart_item = CartItem.objects.create(
                product = product,
                quantity = 1,
                cart = cart,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        return redirect('cart')
    


#decrease cart item quantity
def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')



#remove cart item quantity
def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')

#there are many cart items in a cart
#a cart belongs to one user
#cart = session


def cart(request, total=0, quantity=0, cart_items=None):

    #compute for the total
    try:
        
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            #get the cart id
            cart = Cart.objects.get(cart_id=_cart_id(request))
            #filter cart items based on the cart and if active
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            #no of total price
            total += (cart_item.product.price * cart_item.quantity)
            #no of total items
            quantity += cart_item.quantity
        #depende kung ilang percentage ng tax gusto mo, in this case 2% is applied
        grand_total = total
    except ObjectDoesNotExist:
        pass
    #pass the computed values to the template    
    context = {
        'total':total,
        'quantity':quantity,
        'cart_items':cart_items,
        'grand_total':grand_total,
    }
    return render(request, 'cart.html', context)




@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    if request.method == 'POST':
        quanti = request.POST.get('cart_quantity')
        print(quanti)
    #compute for the total
    try:
        grand_total = 0
        #get the cart id
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            #get the cart id
            cart = Cart.objects.get(cart_id=_cart_id(request))
            #filter cart items based on the cart and if active
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
 
            #no of total price
            total += (cart_item.product.price * cart_item.quantity)
            #no of total items
            quantity += cart_item.quantity
        #depende kung ilang percentage ng tax gusto mo, in this case 2% is applied
        grand_total = total
    except ObjectDoesNotExist:
        pass
    subtotal = int(quanti) * grand_total
    #pass the computed values to the template    
    context = {
        
        'subtotal':subtotal,
        'quanti':quanti,
        'total':total,
        'quantity':quantity,
        'cart_items':cart_items,
        'grand_total':grand_total,
    }
    return render(request, 'store/order.html', context)
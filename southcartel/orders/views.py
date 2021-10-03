from django.shortcuts import render, redirect
from carts.models import CartItem
from .forms import OrderForm    
from .models import Order, Payment, OrderProduct, ShippingMethod
from django.http import HttpResponse, JsonResponse
import datetime
from carts.models import Cart
from carts.views import _cart_id
from django.core.exceptions import ObjectDoesNotExist
from store.models import Product, Variation
import json
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
# Create your views here.


def place_order(request, total=0, quantity=0,):
    current_user = request.user
    # If the cart count is less than or equal to 0, then redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')
    

    grand_total = 0
    shipping_fee = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    # compute ng shipping_fee
    shipping_fee = 0
    grand_total = total + shipping_fee

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            #store form submitted to order model
            data = Order()
            request.session['first_name'] = form.cleaned_data['first_name']
            request.session['last_name'] = form.cleaned_data['last_name']
            request.session['phone'] = form.cleaned_data['phone']
            request.session['email'] = form.cleaned_data['email']
            request.session['address_line_1'] = form.cleaned_data['address_line_1']
            request.session['address_line_2'] = form.cleaned_data['address_line_2']
            request.session['country'] = form.cleaned_data['country']
            request.session['region'] = form.cleaned_data['region']
            request.session['city'] = form.cleaned_data['city']
            request.session['district'] = form.cleaned_data['district']
            request.session['street_name'] = form.cleaned_data['street_name']
            request.session['unit'] = form.cleaned_data['unit']
            request.session['order_note'] = form.cleaned_data['order_note']
            request.session['order_total'] = grand_total
            request.session['shipping_fee'] = shipping_fee
            request.session['ip'] = request.META.get('REMOTE_ADDR')
            return redirect('shipping')

    else:
        return redirect('checkout')



def shipping(request, total=0, quantity=0, cart_items=None):
    
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
    
    #get shipping methods
    shipping_methods = ShippingMethod.objects.all()
    first_name = request.session.get('first_name')
    last_name = request.session.get('last_name')
    full_name = first_name + ' ' + last_name
    address_line_1 = request.session.get('address_line_1')
    region = request.session.get('region')
    shipping_fee = 0
    if region == 'Laguna':
        shipping_fee = 0;
    else:
        shipping_fee = 0;

    grand_total += shipping_fee

    context = {
        'shipping_methods':shipping_methods,
        'total':total,
        'quantity':quantity,
        'cart_items':cart_items,
        'grand_total':grand_total,
        'shipping_fee':shipping_fee,
        'full_name': full_name,
        'address_line_1': address_line_1,
    }
    return render(request, 'store/courier.html', context)


def payments(request, total=0, quantity=0, cart_items=None):
    # Get courier
    if request.method == 'POST':
        request.session['courier'] = request.POST['courier']
    # Get cart items
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
    # Get information
    first_name = request.session.get('first_name')
    last_name = request.session.get('last_name')
    full_name = first_name + ' ' + last_name
    address_line_1 = request.session.get('address_line_1')
    region = request.session.get('region')
    shipping_fee = 0
    if region == 'Laguna':
        shipping_fee = 0;
    else:
        shipping_fee = 0;
    grand_total += shipping_fee
    courier = request.session.get('courier')

    request.session['shipping_fee'] = shipping_fee
    context = {
        'courier': courier,
        'grand_total': grand_total,
        'total': total,
        'cart_items': cart_items,
        'shipping_fee': shipping_fee,
        'full_name': full_name,
        'address_line_1': address_line_1,
    }
    return render(request, 'store/payments.html', context)


def payment_process(request):
    current_user = request.user
    courier = request.session.get('courier')
    shipping_method = ShippingMethod.objects.get(courier = courier)
    # get data from json file
    body = json.loads(request.body)
    print(body)
    # Save Order
    data = Order()
    data.shipping_method = shipping_method
    data.user = current_user
    data.first_name = request.session.get('first_name')
    data.last_name = request.session.get('last_name')
    data.phone = request.session.get('phone')
    data.email = request.session.get('email')
    data.address_line_1 = request.session.get('address_line_1')
    data.address_line_2 = request.session.get('address_line_2')
    data.country = request.session.get('country')
    data.region = request.session.get('region')
    data.city = request.session.get('city')
    data.district = request.session.get('district')
    data.street_name = request.session.get('street_name')
    data.unit = request.session.get('unit')
    data.order_note = request.session.get('order_note')
    data.order_total = body['amount']
    data.shipping_fee = request.session.get('shipping_fee')
    data.ip = request.META.get('REMOTE_ADDR')
    data.is_ordered = True
    data.save()
    # Generate order number
    yr = int(datetime.date.today().strftime('%Y'))
    dt = int(datetime.date.today().strftime('%d'))
    mt = int(datetime.date.today().strftime('%m'))
    d = datetime.date(yr,mt,dt)
    current_date = d.strftime("%Y%m%d") #20210305
    order_number = current_date + str(data.id)
    data.order_number = order_number
    data.save()

    # Store payment details in model
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = body['amount'],
        status = body['status'],
    )
    payment.save()
    data.payment = payment
    data.save()

    # move cart items to order products table
    order = Order.objects.get(user=request.user, order_number=order_number)
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct =OrderProduct.objects.get(id = orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()
        # reduce inventory
        if cart_item.variations:
            for var in product_variation:     
                vary = Variation.objects.get(id=var.id)
                vary.stock -=item.quantity
                vary.save()

        else:
            product = Product.objects.get(id=item.product_id)
            product.stock -= item.quantity
            product.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()

    # send order received email to customer
    mail_subject = 'Thank you for your order!'
    message = render_to_string('store/order_received.html', {
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

   
    # Send order number and transaction id back to sendData method via JsonResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)



def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'store/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
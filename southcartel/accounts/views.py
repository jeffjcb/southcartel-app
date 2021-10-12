from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile, RefundRequests, FavoriteItem
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required

#email verification
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from carts.views import _cart_id
from carts.models import Cart, CartItem
from orders.models import Order, OrderProduct
from store.models import Product, Variation
import requests




def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            username = email.split('@')[0]
            password = form.cleaned_data['password']
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.save()
            
            # Create User Profile
            profile = UserProfile()
            profile.user_id = user.id
            profile.save()

            # EMAIL VERIFICATION
            current_site = get_current_site(request)
            mail_subject = "Please activate your account"
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                # to encode primary key of user
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            # messages.success(request, 'Thank you for signing up! We have sent you a verification link to your email address.')
            return redirect('/accounts/login/?command=verification&email='+email)

    else:
        form = RegistrationForm()
    context = {
        'form':form,
    }
    return render(request, 'accounts/signup.html', context)


def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = auth.authenticate(email=email, password=password)
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id =_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)

                    #Getting product Variation
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))
                    #Get the cart items ftom the user to access his product variations
                    #get the products associated with the cart/session
                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list=[]
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        #this stores the variations
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)
                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart= cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass
            auth.login(request, user)
            # messages.success(request, 'You are now logged in.')
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage=params['next']
                    return redirect(nextPage)
            except:
                return redirect('home')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')
    return render(request, 'accounts/login.html')



#can only logout if user is logged in
@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are now logged out.')
    return redirect('login')


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user= None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active=True
        user.save()
        messages.success(request, 'Congratulations, Your account is now activated')
        return redirect('login')
    else:
        messages.error(request, 'Invalid Activation Link')
        return redirect('register')



@login_required(login_url = 'login')
def dashboard(request):
    orders = Order.objects.order_by('created_at').filter(user_id = request.user.id, is_ordered=True)
    orders_count = orders.count()
    context = {
        'orders_count': orders_count,
        }
    return render(request, 'accounts/dashboard.html', context)



#sends email
def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

             # send VERIFICATION for reset
            current_site = get_current_site(request)
            mail_subject = "Reset your password"
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                # to encode primary key of user
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, 'Password reset link was sent to your email address.')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')


#link from email redirect to reset password page if valid link
def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user= None
    
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password below')
        return redirect('resetPassword')
    else:
        messages.error(request, 'This link has expired.')
        return redirect('login')

#shows the reset password page
def resetPassword(request):
    if request.session.get('uid') is not None:
        if request.method == 'POST':
            password = request.POST['password']
            confirm_password = request.POST['confirm_password']
            if password == confirm_password:
                uid = request.session.get('uid')
                user = Account.objects.get(pk = uid)
                user.set_password(password)
                user.save()
                messages.success(request, 'Password reset was successful!')
                return redirect('login')
            else:
                messages.error(request, 'Password do not match!')
                return redirect('resetPassword')
        else:
            return render(request, 'accounts/resetPassword.html')
    else:
        return redirect('login')


def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {
        'orders':orders,
    }
    return render(request, 'accounts/my_orders.html', context)


@login_required(login_url='login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    context = {
        'user_form': user_form,
        'profile_form':profile_form,
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                # auth.logout(request)
                messages.success(request, 'Password updated successfully.')
                return redirect('change_password')
            else:
                messages.error(request, 'Please enter valid current password')
                return redirect('change_password')
        else:
            messages.error(request, 'Password does not match!')
            return redirect('change_password')
    return render(request, 'accounts/change_password.html')


@login_required(login_url='login')
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.product_price * i.quantity

    context = {
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
    }
    return render(request, 'accounts/order_detail.html', context)


@login_required(login_url='login')
def order_tracking(request):
    if request.method == 'POST':
        order_number = request.POST.get('order_num')
        tracked_order = Order.objects.get(order_number=order_number)
    context ={
        'num':order_number,
        'tracked_order':tracked_order,
    }
    return render(request, 'accounts/order_tracking.html', context)


@login_required(login_url='login')
def cancel_order(request, order_id):
    tracked_order = Order.objects.get(order_number=order_id)
    tracked_order_products = OrderProduct.objects.all().filter(order__order_number=order_id)
    print(tracked_order.payment.payment_id)
    if tracked_order.status == "To Ship":
        tracked_order.status = "Cancelled"
        tracked_order.save()
        # refund product stock
        for t in tracked_order_products:         
            if t.variations.all().count() != 0:
                for n in t.variations.all():
                    v = Variation.objects.get(product=t.product, variation_value=n)
                    v.stock += t.quantity
                    v.save()
            else:
                p = Product.objects.get(id=t.product.id)
                p.stock += t.quantity
                p.save()

        messages.success(request, 'Your Order has been cancelled.')
        return redirect('my_orders')
    else:
        messages.error(request, 'The packed is already to receive. Cancellation is not available.')
        return redirect('order_tracking')




@login_required(login_url='login')
def request_refund(request):
    order_number = request.GET.get('order_number')
    context = {
        'order_number': order_number,
        }
    return render(request, 'accounts/request_refund.html', context)


def send_refund_request(request):
    current_user = request.user
    if request.method == 'POST':
        data = RefundRequests()
        #get the data
        order_number = request.POST.get('order_number')
        reason = request.POST.get('reason')
        order = Order.objects.get(order_number=order_number)
        amount_paid = order.payment.amount_paid
        #save or update the data
        created = RefundRequests.objects.update_or_create(user=current_user, order_number = order_number, amount_paid = amount_paid, defaults={'reason': reason})
        messages.success(request, 'Your Refund Request has been sent. The manager will contact you if the refund is approved.')
    return redirect('my_orders')

@login_required(login_url='login')
def favorites(request):
    current_user = request.user
    favorite_items = FavoriteItem.objects.filter(user=current_user)
    context = {
        'favorite_items' : favorite_items,
    }
    return render(request, 'accounts/favorites.html', context)

@login_required(login_url='login')
def add_favorites(request):
    current_user = request.user
    #get product
    #if single product is clicked to add to cart
    #if authenticated
    if current_user.is_authenticated:
        #get variations    
        product_id = request.GET.get('product_number')
        product = Product.objects.get(id=product_id)
        #if cart item exists
        is_favorite_item_exists = FavoriteItem.objects.filter(product=product, user=current_user).exists()
        if is_favorite_item_exists:
            #do not add anymore
            pass
        #if cart item does not exist create a favorite item
        else:
            favorite_item = FavoriteItem.objects.create(
                user = current_user,
                product = product,
            )
            favorite_item.save()
        return redirect('favorites')
    #If not authenticated
    else:  
        return redirect('login')

@login_required(login_url='login')
def remove_favorites(request, product_id, favorite_item_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        if request.user.is_authenticated:
            favorite_item = FavoriteItem.objects.get(product=product, user=request.user, id=favorite_item_id)
        else:
            pass
        favorite_item.delete()
    except Exception as e:
        raise e
    return redirect('favorites')


    


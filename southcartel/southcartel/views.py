from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from store.models import Product, Variation
from django.utils import timezone
from accounts.models import Preferences
import datetime
import pandas as pd
import numpy as np
import sklearn
from scipy.sparse import csr_matrix
from collections import Counter
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import process
import re 
from django.db.models import Q
import random
from category.models import Category
from django.core.paginator import Paginator
from random import shuffle
# for carts pos
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from carts.models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from orders.models import Order, Payment, OrderProduct
# Create your views here.


def create_X(df):
    """
    Generates a sparse matrix from ratings dataframe.
    
    Args:
        df: pandas dataframe
    
    Returns:
        X: sparse matrix
        user_mapper: dict that maps user id's to user indices
        user_inv_mapper: dict that maps user indices to user id's
        movie_mapper: dict that maps movie id's to movie indices
        movie_inv_mapper: dict that maps movie indices to movie id's
    """
    N = df['id'].nunique()
    M = df['product'].nunique()

    user_mapper = dict(zip(np.unique(df["user"]), list(range(N))))
    movie_mapper = dict(zip(np.unique(df["product"]), list(range(M))))
    
    user_inv_mapper = dict(zip(list(range(N)), np.unique(df["user"])))
    movie_inv_mapper = dict(zip(list(range(M)), np.unique(df["product"])))
    
    user_index = [user_mapper[i] for i in df['user']]
    movie_index = [movie_mapper[i] for i in df['product']]

    X = csr_matrix((df["rating"], (movie_index, user_index)), shape=(M, N))
    
    return X, user_mapper, movie_mapper, user_inv_mapper, movie_inv_mapper




# Finding similar movies using k-Nearest Neighbours
# you use "manhattan" or "euclidean" instead of "cosine".
def find_similar_movies(movie_id, X, k, metric='cosine', show_distance=False):
    """
    Finds k-nearest neighbours for a given movie id.
    Args:
        movie_id: id of the movie of interest
        X: user-item utility matrix
        k: number of similar movies to retrieve
        metric: distance metric for kNN calculations
    Returns:
        list of k similar movie ID's
    """
    neighbour_ids = []
    
    movie_ind = movie_mapper[movie_id]
    movie_vec = X[movie_ind]
    k+=1
    kNN = NearestNeighbors(n_neighbors=k, algorithm="brute", metric=metric)
    kNN.fit(X)
    if isinstance(movie_vec, (np.ndarray)):
        movie_vec = movie_vec.reshape(1,-1)
    neighbour = kNN.kneighbors(movie_vec, return_distance=show_distance)
    for i in range(0,k):
        n = neighbour.item(i)
        neighbour_ids.append(movie_inv_mapper[n])
    neighbour_ids.pop(0)
    return neighbour_ids




def home(request):
    
    #recommender  system
    qs = Product.objects.all().values('id','product_name','tags', 'description','price')
    qt = Preferences.objects.all().values('id','user','product', 'rating')
    try:
        product_data = pd.DataFrame(qs)
        preferences_data = pd.DataFrame(qt)
    # if preferences is enough, run the collab and contentbased filtering, else, hybrid products = get 10 random products from products

   #####################################
    # COLLABORATIVE FILTERING
    # create matrix
        X, user_mapper, movie_mapper, user_inv_mapper, movie_inv_mapper = create_X(preferences_data)
    except:
        pass 

    # GET RANDOM PRODUCT FORM PREFERENCES
    try:
        k=8
        movie_titles = dict(zip(product_data['id'], product_data['product_name']))
        pref = list(Preferences.objects.all().filter(user=request.user.id).values('product'))
        pref_random = random.sample(pref, 1)
        movie_id = pref_random[0]['product']

        
        # function getting similar products collaborative filtering
        neighbour_ids = []
        
        movie_ind = movie_mapper[movie_id]
        movie_vec = X[movie_ind]
        k+=1
        kNN = NearestNeighbors(n_neighbors=k, algorithm="brute", metric='cosine')
        kNN.fit(X)
        if isinstance(movie_vec, (np.ndarray)):
            movie_vec = movie_vec.reshape(1,-1)
        neighbour = kNN.kneighbors(movie_vec, return_distance=False)
        for i in range(0,k):
            n = neighbour.item(i)
            neighbour_ids.append(movie_inv_mapper[n])
        neighbour_ids.pop(0)


        similar_ids = neighbour_ids
        movie_title = movie_titles[movie_id]

        # print(f"Collaborative Filtering: Because you like {movie_title}")
        # for i in similar_ids:
        #     print(movie_titles[i])
    except:
        # random ids
        pref = list(Product.objects.all().values('id'))
        if pref:
            pref_random = random.sample(pref, 8)
            similar_ids = [d['id'] for d in pref_random]
        else:
            pass



############################################
    # CONTENT BASED FILTERING
    try:
        product_data['tags'] = product_data['tags'].apply(lambda x: x.split(","))
        product_data.head()
        genres_counts = Counter(g for product_data in product_data['tags'] for g in product_data)
        product_data = product_data[product_data['tags']!='(no tags listed)']
        del genres_counts['(no tags listed)']
        genres_counts_df = pd.DataFrame([genres_counts]).T.reset_index()
        genres_counts_df.columns = ['tags', 'count']
        genres_counts_df = genres_counts_df.sort_values(by='count', ascending=False)
        genres = list(genres_counts.keys())
        for g in genres:
            product_data[g] = product_data['tags'].transform(lambda x: int(g in x))

        movie_features = pd.concat([product_data[genres]], axis=1)
        cosine_sim = cosine_similarity(movie_features, movie_features)
        def movie_finder(title):
            all_titles = product_data['product_name'].tolist()
            closest_match = process.extractOne(title,all_titles)
            return closest_match[0]
    
        title = movie_finder('Orange Shirt')
        movie_idx = dict(zip(product_data['product_name'], list(product_data.index)))
        idx = movie_idx[title]
        
        n_recommendations=3
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:(n_recommendations+1)]
        similar_movies = [i[0] for i in sim_scores]
        product_data['product_name'].iloc[similar_movies]

    
        def get_content_based_recommendations(title_string, n_recommendations=3):
            cb = []
            title = movie_finder(title_string)
            idx = movie_idx[title]
            sim_scores = list(enumerate(cosine_sim[idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            sim_scores = sim_scores[1:(n_recommendations+1)]
            similar_movies = [i[0] for i in sim_scores]
            # print(sim_scores)
            # print(f"Contentbased filtering: Recommendations for {title}:")
            # print(product_data['product_name'].iloc[similar_movies])
            for i in product_data['id'].iloc[similar_movies]:
                cb.append(i)
            return cb

        # Get random preference from preferences and perform CB filtering
        contb = list(Preferences.objects.all().filter(user=request.user.id).values('product'))
        contb_random = random.sample(contb, 1)
        cb__random_prod_name = Product.objects.get(id=contb_random[0]['product'])
        cb_ids = get_content_based_recommendations(str(cb__random_prod_name), 8)
        
    except:
        # random ids
        prefer = list(Product.objects.all().values('id'))
        if prefer:
            pref_randoms = random.sample(prefer, 8)
            cb_ids = [d['id'] for d in pref_randoms]
        else:
            pass
        
    try:
        # Get hybrid list and eliminate duplicates
        hybrid_list = cb_ids + similar_ids
        final_hybrid_list = set(hybrid_list)

        
        hybrid_products = Product.objects.all().filter(pk__in=list(final_hybrid_list))
    except:
        hybrid_products = None
  
    limited_products = list(Product.objects.all()[:16])
    shuffle(limited_products)
    #main  
    products = Product.objects.all().filter(is_available=True)
    #get the latest products
    latest = Product.objects.all().filter(is_available=True).order_by('-created_date')[:10]

    # get products added 15 days ago
    recents = Product.objects.filter(created_date__range=[datetime.datetime.now(tz=timezone.utc) - datetime.timedelta(days=15),datetime.datetime.now(tz=timezone.utc)])

    bydates = Product.objects.all().order_by('created_date')
    context = {
        'products':products,
        'recents':recents,
        'bydates':bydates,
        'latest':latest,
        'hybrid_products': hybrid_products,
        'limited_products':limited_products,
    }
    return render(request, 'home.html', context)


#####################################################
# POS


@staff_member_required
def pos(request):
    products = None 
    products = Product.objects.all().filter(is_available=True).order_by('id')
    # get url og page
    product_count = products.count()
    
    context = {
        'products':products,
        'product_count' : product_count,
        # 'recents': recents,
    }
    return render(request, 'pos.html', context)


def searches(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        #if keyword has something
        if keyword:
            #search using description i contains with the keyword
            #'Q' is for using or operator in complex queries
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword)| Q(tags__icontains=keyword)).distinct()
            product_count = products.count()
    context = {
        'products':products,
        'product_count':product_count,
    }
    return render(request, 'pos.html', context)




# Create your views here.
#get session id
def _cart_id(request):
    cart = request.session.session_key
    #if there is no session
    if not cart:
        cart = request.session.create()
    return cart

@staff_member_required
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
        return redirect('pos_cart')

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
        return redirect('pos_cart')


@staff_member_required
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
    return redirect('pos_cart')


@staff_member_required
#remove cart item quantity
def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('pos_cart')

#there are many cart items in a cart
#a cart belongs to one user
#cart = session

@staff_member_required
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
    return render(request, 'pos/pos_cart.html', context)




@staff_member_required
def checkout(request, total=0, quantity=0, cart_items=None):
        #compute for the total
    if request.method == 'POST':
        cash =request.POST.get('cash')
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
        grand_total = total
    except ObjectDoesNotExist:
        pass
    try:
        if float(cash) < float(grand_total):
                messages.error(request, 'The cash tendered is less than the grand total.')
                return redirect('pos_cart')
        else:
            pass
    except Exception as e:
        return e

    #pass the computed values to the template    
    context = {
        'total':total,
        'quantity':quantity,
        'cart_items':cart_items,
        'grand_total':grand_total,
        'cash':cash,
    }
    request.session['cash']=cash
    request.session['grand_total']=grand_total

    return redirect('pos_payment_process')



@staff_member_required
def payment_process(request):
    try:
        cash = request.session.get('cash')
        grand_total = request.session.get('grand_total')
        change = float(cash) - float(grand_total)
        current_user = request.user
        courier = ''
        # Save Order
        data = Order()
        data.user = current_user
        data.first_name = 'Staff'
        data.last_name = 'Account'
        data.phone = '521238'
        data.email = 'staff@account.com'
        data.address_line_1 = 'South Cartel, Calamba, Laguna'
        data.address_line_2 = ''
        data.country = 'Philippines'
        data.region = 'Laguna'
        data.city = 'Calamba'
        data.district = 'Laguna'
        data.street_name = 'south cartel'
        data.unit = ''
        data.order_note = ''
        data.order_total = grand_total
        data.shipping_fee = 0
        data.ip = request.META.get('REMOTE_ADDR')
        data.is_ordered = True
        data.status = 'Delivered'
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
            payment_id = order_number,
            payment_method = 'Through Walk-in',
            amount_paid = cash,
            status = 'Done',
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
            product = Product.objects.get(id=item.product_id)
            product.stock -= item.quantity
            product.save()
            if cart_item.variations:
                for var in product_variation:     
                    vary = Variation.objects.get(id=var.id)
                    vary.stock -=item.quantity
                    vary.save()
            else:
                pass

        # Clear cart
        CartItem.objects.filter(user=request.user).delete()

        # Send order number and transaction id back to sendData method via JsonResponse
        # data = {
        #     'order_number': order.order_number,
        #     'transID': payment.payment_id,
        # }
        try:
            order = Order.objects.get(order_number=order_number, is_ordered=True)
            ordered_products = OrderProduct.objects.filter(order_id=order.id)
            subtotal = 0
            for i in ordered_products:
                subtotal += i.product_price * i.quantity

        except OrderProduct.DoesNotExist:
            pass
        context = {
            'order_number':order_number,
            'order': order,
            'ordered_products': ordered_products,
            'subtotal': subtotal,
            'cash':cash,
            'change':change,
        }

        return render(request, 'pos/pos_order_complete.html', context)
    except Exception as e:
        return e



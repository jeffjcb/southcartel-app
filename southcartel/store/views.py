from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Product, ReviewRating, ProductGallery, ViewedProduct
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct
import datetime
from accounts.models import Preferences
import pandas as pd
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import process
import random

# Create your views here.

def store(request, category_slug=None):

    categories = None
    products = None
    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
        # recents = Product.objects.filter(created_date__range=[datetime.datetime.now() - datetime.timedelta(days=15),datetime.datetime.now()])
        paginator = Paginator(products, 10)
        # get url og page
        page = request.GET.get('page')
        paged_product = paginator.get_page(page)
        product_count = products.count()
    else:     
        products = Product.objects.all().filter(is_available=True).order_by('id')
        paginator = Paginator(products, 10)
        # get url og page
        page = request.GET.get('page')
        paged_product = paginator.get_page(page)
        product_count = products.count()
    
    context = {
        'products' :paged_product,
        'product_count':product_count,
        # 'recents': recents,
    }
    return render(request, 'store.html', context)


def product_detail(request, category_slug, product_slug):
    current_user = request.user
    if current_user.is_authenticated: 
        product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        is_viewed_item_exists = ViewedProduct.objects.filter(product=product, user=current_user).exists()
        if is_viewed_item_exists:
            #do not add anymore
            pass
        #if cart item does not exist create a item
        else:
            viewed_item = ViewedProduct.objects.create(
                user = current_user,
                product = product,
            )
            viewed_item.save()
    #If not authenticated
    else:
        pass




    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        #check if single item is added to cart, filter cart items with the cart id and the product if it exists in the cart
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e
    
    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct=None
    else:
        orderproduct = None
    
    #recommender  system
    # CONTENT BASED FILTERING
    try:
        qs = Product.objects.all().values('id','product_name','tags', 'description','price')
        product_data = pd.DataFrame(qs)
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
            for i in product_data['id'].iloc[similar_movies]:
                cb.append(i)
            return cb
            
        # Get random preference from preferences and perform CB filtering
        cb_ids = get_content_based_recommendations(str(single_product.product_name), 8)
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
        hybrid_list = cb_ids
        final_hybrid_list = set(hybrid_list)
        hybrid_products = Product.objects.all().filter(pk__in=list(final_hybrid_list))
    except:
        hybrid_products = None


    # get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)
    # get product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    
    context ={
        'single_product':single_product,
        'in_cart':in_cart,
        'orderproduct':orderproduct,
        'reviews':reviews,
        'product_gallery': product_gallery,
        'hybrid_products':hybrid_products,
    }
    return render(request, 'product_detail.html', context)






def search(request):

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
    return render(request, 'store.html', context)


def submit_review(request, product_id):
    # get the url
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            #instance is for updating the review rather than adding a new one
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            # redirect back to the current page
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)




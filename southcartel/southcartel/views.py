from django.db.models.expressions import F
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
from django.contrib.admin.views.decorators import staff_member_required

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


@staff_member_required
def pos(request):
    asd = []
    x = request.GET.get('item')
    asd.append(x)
    bagonglist = asd
    print(bagonglist)


    
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


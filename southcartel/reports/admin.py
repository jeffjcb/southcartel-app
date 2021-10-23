from django.contrib import admin
from django.http import HttpResponse
from django.urls import path
from django.db import models
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from orders.models import OrderProduct, Order
from django.db.models import Sum
import pandas as pd
import numpy as np
from django.db.models.functions import ExtractWeek, ExtractYear, ExtractMonth
from django.db.models import Sum, Count
import datetime
# for forecasting
from math import sqrt
from sklearn.metrics import mean_squared_error
from pmdarima.arima import auto_arima

from taggit.admin import Tag
from .filters import OrderFilter

admin.site.unregister(Tag)

# Register your models here.

# my dummy model
class Report(models.Model):
    class Meta:
        verbose_name_plural = 'Reports'
        app_label = 'reports'

@staff_member_required
def my_custom_view(request):
    sales = OrderProduct.objects.exclude(order__status='Cancelled').values('product', 'product__product_name').annotate(sold = Sum('quantity'), amount = Sum('order__order_total')).order_by('-amount')
    top_categories = OrderProduct.objects.exclude(order__status='Cancelled').values('product__category', 'product__category__category_name').annotate(sold = Sum('quantity'), amount = Sum('order__order_total')).order_by('-amount')
    top_brands = OrderProduct.objects.exclude(order__status='Cancelled').values('product__brand', 'product__brand__brand_name').annotate(sold = Sum('quantity'), amount = Sum('order__order_total')).order_by('-amount')
    general_sales = OrderProduct.objects.exclude(order__status='Cancelled').values('product', 'product__product_name', 'product__brand__brand_name').annotate(sold = Sum('quantity'), amount = Sum('order__order_total'))

    # Filter
    myFilter = OrderFilter(request.GET, queryset =general_sales)
    general_sales = myFilter.qs

    context = {
        'sales' : sales,
        'top_categories': top_categories,
        'top_brands': top_brands,
        'general_sales': general_sales,
        'myFilter':myFilter,
    }
    return render(request, 'reports/reports.html', context )


class ReportAdmin(admin.ModelAdmin):
    model = Report

    def get_urls(self):
        view_name = '{}_{}_changelist'.format(
            self.model._meta.app_label, self.model._meta.model_name)
        return [
            path('reports/', my_custom_view, name=view_name),
        ]
    def has_view_permission(self, request, obj=None):
        if request.user.is_admin:
            return True
        if request.user.groups.filter(name='Partners').exists():
            return True




class SalesForecasting(models.Model):
    class Meta:
        verbose_name_plural = 'Sales Forecasting'
        app_label = 'reports'

@staff_member_required
def salesforecasting(request):
    try:
        month = Order.objects.exclude(status='Cancelled').annotate(month=ExtractMonth('created_at'), year=ExtractYear('created_at')).values('month', 'year').annotate(c=Count('id'), amount = Sum('order_total')).values('year','month', 'c', 'amount').order_by('month')
        week = Order.objects.exclude(status='Cancelled').annotate(week=ExtractWeek('created_at'), year=ExtractYear('created_at')).values('week', 'year').annotate(c=Count('id'), amount = Sum('order_total')).values('year','week', 'c','amount').order_by('week') 
        
        # MONTHLY
        st = pd.DataFrame(month)
        # testing
        st = st.sort_values(["year", 'month'])
        st["datey"] = st["year"].astype(str) +'-'+ st["month"].astype(str)
        data = st[['datey', 'amount']]
        #divide into train and validation set
        train = data[:int(0.7*(len(data)))]
        valid = data[int(0.7*(len(data))):]
        #preprocessing (since arima takes univariate series as input)
        train.drop('datey',axis=1,inplace=True)
        valid.drop('datey',axis=1,inplace=True)
        model = auto_arima(train, trace=True, error_action='ignore', suppress_warnings=True)
        model.fit(train)
        forecast = model.predict(n_periods=len(valid))
        forecast = pd.DataFrame(forecast,index = valid.index,columns=['Prediction'])
        x = train['amount'].values.tolist()
        x1 = valid['amount'].values.tolist()
        fc = forecast['Prediction'].values.tolist()
        # print(fc)
        amunt = x + x1 +fc
        st["date"] =  st["month"].astype(str) +" - "+ st["year"].astype(str)
        # make to list for charts js to understand
        df1 = st['date'].tolist()
        df1.append('Forecasted')
        df = amunt
        

        # weekly
        we = pd.DataFrame(week)
        we = we.sort_values(["year", 'week'])
        we["datey"] = we["year"].astype(str) +'-'+ we["week"].astype(str)
        data2 = we[['datey', 'amount']]
        #divide into train and validation set
        train2 = data2[:int(0.7*(len(data2)))]
        valid2 = data2[int(0.7*(len(data2))):]
        #preprocessing (since arima takes univariate series as input)
        train2.drop('datey',axis=1,inplace=True)
        valid2.drop('datey',axis=1,inplace=True)
        model2 = auto_arima(train2, trace=True, error_action='ignore', suppress_warnings=True)
        model2.fit(train2)

        forecast2 = model2.predict(n_periods=len(valid2))
        forecast2 = pd.DataFrame(forecast2,index = valid2.index,columns=['Prediction'])

        y = train2['amount'].values.tolist()
        y1 = valid2['amount'].values.tolist()
        fc2 = forecast2['Prediction'].values.tolist()
        amunt2 = y + y1 +fc2

        we["date"] = "Week "+ we["week"].astype(str) +" - "+ we["year"].astype(str)
        # print(we["date"])
        we1 = we['date'].tolist()
        we1.append('Forecasted')
        we2 = amunt2
        context = {
            'df':df,
            'df1':df1,
            'we1':we1,
            'we2':we2,
        }
    except:
        context = {
        }

    return render(request, 'reports/salesforecasting.html', context )


class SalesForecastingAdmin(admin.ModelAdmin):
    model = SalesForecasting

    def get_urls(self):
        view_name = '{}_{}_changelist'.format(
            self.model._meta.app_label, self.model._meta.model_name)
        return [
            path('reports/', salesforecasting, name=view_name),
        ]

admin.site.register(Report, ReportAdmin)
admin.site.register(SalesForecasting, SalesForecastingAdmin)




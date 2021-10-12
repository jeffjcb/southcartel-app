from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
# Create your models here.


# methods to create users/superusers
class MyAccountManager(BaseUserManager):
    def create_user(self,first_name, last_name, username, email, password=None):
        # run errror if we dont get the username and email adrres
        if not email:
            raise ValueError("User must have an email address")

        if not username:
            raise ValueError('User must have an username')
        # else
        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, email, username, password):
        # inherit from createuser function then just add admin privelages
        user = self.create_user(
            email = self.normalize_email(email),
            username = username,
            password = password,
            first_name = first_name,
            last_name = last_name,
        )
        user.is_admin =True
        user.is_active =True
        user.is_staff =True
        user.is_superadmin =True
        user.save(using=self._db)
        return user

#model for base user and fields
class Account(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, unique=True)
    email = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=50)
    
    #required for creating customer user model
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)

    #login with email not username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    objects = MyAccountManager()

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.email
    
    #required
    def has_perm(self, perm, obj=None):
        #if permission is admin, he has all permission to all changes
        return self.is_admin
   
    #required
    def has_module_perms(self, add_label):
        return True

class UserProfile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    address_line_1 = models.CharField(blank=True, max_length=100)
    address_line_2 = models.CharField(blank=True, max_length=100)
    city = models.CharField(blank=True, max_length=20)
    district = models.CharField(blank=True, max_length=20)
    province = models.CharField(blank=True, max_length=20)
    country = models.CharField(blank=True, max_length=20, default='Philippines')

    def __str__(self):
        return self.user.first_name

    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'


class RefundRequests(models.Model):
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    reason = models.CharField(max_length=200)
    order_number = models.CharField(max_length=20)
    amount_paid = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.first_name
    
    class Meta:
        verbose_name = 'Refund Request'
        verbose_name_plural = 'Refund Requests'

class Favorite(models.Model):
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.id


class FavoriteItem(models.Model):
    user =models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    favorite = models.ForeignKey(Favorite, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(to='store.Product', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
        
    def __str__(self):
        return self.user.first_name


class Preferences(models.Model):
    user =models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(to='store.Product', on_delete=models.CASCADE)
    rating = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.product.product_name
    
    class Meta:
        verbose_name = 'preference'
        verbose_name_plural = 'preferences'
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from .forms import UserRegistrationForm, ProductForm, DeliveryAreaForm, CustomPasswordResetForm, ShippingAddressForm
from .models import Product, Cart, CartItem, DeliveryArea, Order, OrderItem, Category, Review, Wishlist, ShippingAddress
from django.db.models import Sum, Q
from datetime import datetime, timedelta
import random
from django.contrib import messages
from django.db.models import Avg, Count
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


@csrf_protect
def custom_password_reset_view(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user:
                user_role = getattr(getattr(user, 'profile', None), 'role', 'buyer').capitalize()
                subject = 'Account Details Recovery'
                message = f"Hello {user.username},\n\nYour account details have been recovered. Your username is {user.username} and your role is {user_role}.\n\nThank you for using our store!"
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                except Exception:
                    pass
                messages.success(request, f"Your account details have been sent to {user.email}")
                return render(request, 'app/custom_password_reset.html', {'form': CustomPasswordResetForm(), 'success': True})
    else:
        form = CustomPasswordResetForm()
    return render(request, 'app/custom_password_reset.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            raw_password = form.cleaned_data.get('password1')
            user_role = form.cleaned_data.get('role', 'buyer').capitalize()
            user_email = user.email
            if user_email:
                subject = ' Welcome to Our Store – Your Account Details'
                message = f"""Hello {user.username},

Welcome to Our Store! 

Your account has been successfully created. Here are your login details:

     Username : {user.username}
     Password : {raw_password}
     Role     : {user_role}

You can log in at any time using these credentials. For security, we recommend changing your password after your first login.

Thank you for joining us. We hope you enjoy your shopping experience!
"""
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user_email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Welcome email failed to send: {e}")

            messages.success(request, f"Account created for {user.username}. A welcome email with your login details has been sent to {user_email}. Please log in.")
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'app/register.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'app/login.html'

    def form_valid(self, form):
        return super().form_valid(form)

    def get_initial(self):
        return {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        if form is not None:
            try:
                form.initial = {}
            except Exception:
                pass
        return context

    def get_success_url(self):
        redirect_to = self.request.GET.get('next') or self.request.POST.get('next')
        if redirect_to:
            return redirect_to
        from django.urls import reverse
        try:
            profile = getattr(self.request.user, 'profile', None)
            if profile and getattr(profile, 'role', None) == 'seller':
                return reverse('seller_dashboard')
        except Exception:
            pass
        return reverse('product_list')

@login_required
def user_dashboard_view(request):
    if request.user.is_superuser:
        return redirect('product_list')
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role == 'seller':
        return redirect('seller_dashboard')
    return render(request, 'app/user_dashboard.html')

@login_required
def seller_dashboard_view(request):
    profile = getattr(request.user, 'profile', None)
    is_seller = profile and profile.role == 'seller'
    if not request.user.is_superuser and not is_seller:
        return redirect('product_list')

    if request.user.is_superuser:
        products = Product.objects.all()
        seller_order_items = OrderItem.objects.all().select_related('order', 'product', 'order__user')
    else:
        products = Product.objects.filter(seller=request.user)
        seller_order_items = OrderItem.objects.filter(
            product__seller=request.user
        ).select_related('order', 'product', 'order__user')

    total_items = products.count()
    delivered_items = seller_order_items.filter(order__status='Delivered')
    total_revenue = sum(item.price * item.quantity for item in delivered_items)
    pending_items = seller_order_items.filter(order__status='Pending')
    pending_amount = sum(item.price * item.quantity for item in pending_items)

    seller_order_ids = seller_order_items.values_list('order_id', flat=True).distinct()
    orders = Order.objects.filter(id__in=seller_order_ids).order_by('-created_at')

    delivered_count = orders.filter(status='Delivered').count()
    pending_count = orders.filter(status='Pending').count()
    cancelled_count = orders.filter(status='Cancelled').count()

    return render(request, 'app/seller_dashboard.html', {
        'products': products,
        'total_items': total_items,
        'total_revenue': total_revenue,
        'pending_amount': pending_amount,
        'orders': orders,
        'delivered_count': delivered_count,
        'pending_count': pending_count,
        'cancelled_count': cancelled_count,
        'seller_order_items': seller_order_items,
    })

@login_required
def seller_edit_product_view(request, product_id):
    profile = getattr(request.user, 'profile', None)
    is_seller = profile and profile.role == 'seller'
    if not request.user.is_superuser and not is_seller:
        return redirect('product_list')

    if request.user.is_superuser:
        product = get_object_or_404(Product, id=product_id)
    else:
        product = get_object_or_404(Product, id=product_id, seller=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            updated = form.save(commit=False)
            new_cat = form.cleaned_data.get('new_category')
            if new_cat:
                cat, created = Category.objects.get_or_create(name=new_cat)
                updated.category = cat
            updated.save()
            messages.success(request, f"'{product.name}' updated successfully.")
            return redirect('seller_dashboard')
    else:
        form = ProductForm(instance=product)

    return render(request, 'app/seller_edit_product.html', {'form': form, 'product': product})

@login_required
def seller_delete_product_view(request, product_id):
    profile = getattr(request.user, 'profile', None)
    is_seller = profile and profile.role == 'seller'
    if not request.user.is_superuser and not is_seller:
        return redirect('product_list')

    if request.user.is_superuser:
        product = get_object_or_404(Product, id=product_id)
    else:
        product = get_object_or_404(Product, id=product_id, seller=request.user)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f"'{name}' has been deleted.")
    return redirect('seller_dashboard')

@login_required
def seller_update_order_status_view(request, order_id):
    profile = getattr(request.user, 'profile', None)
    is_seller = profile and profile.role == 'seller'
    if not request.user.is_superuser and not is_seller:
        return redirect('product_list')

    if not request.user.is_superuser:
        seller_order_items = OrderItem.objects.filter(
            order_id=order_id,
            product__seller=request.user
        )
        if not seller_order_items.exists():
            messages.error(request, "Order not found or not associated with your products.")
            return redirect('seller_dashboard')

    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        allowed = ['Pending', 'Shipped', 'Delivered', 'Cancelled']
        if new_status in allowed:
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.id} status updated to {new_status}.")
        else:
            messages.error(request, "Invalid status.")
    return redirect('seller_dashboard')

@login_required
def seller_create_product_view(request):
    profile = getattr(request.user, 'profile', None)
    is_seller = profile and profile.role == 'seller'
    if not request.user.is_superuser and not is_seller:
        return redirect('product_list')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            new_cat = form.cleaned_data.get('new_category')
            if new_cat:
                cat, created = Category.objects.get_or_create(name=new_cat)
                product.category = cat
            product.save()
            messages.success(request, 'Product created successfully.')
            return redirect('seller_dashboard')
    else:
        form = ProductForm()
    return render(request, 'app/seller_create_product.html', {'form': form})

def product_list_view(request):
    query      = request.GET.get('q', '').strip()
    gender     = request.GET.get('gender', '')
    category_id = request.GET.get('category', '')
    products = Product.objects.all().order_by('-created_at')

    if gender:
        if gender != 'All':
            products = products.filter(gender__in=[gender, 'All'])

    if category_id:
        if category_id.isdigit():
            products = products.filter(category_id=category_id)
        else:
            products = products.filter(category__name__icontains=category_id)

    if query:
        products = products.filter(name__icontains=query)

    if gender and gender != 'All':
        gender_products = Product.objects.filter(gender__in=[gender, 'All'])
        relevant_cat_ids = gender_products.exclude(category=None).values_list('category_id', flat=True).distinct()
        categories = Category.objects.filter(id__in=relevant_cat_ids)
    else:
        categories = Category.objects.all()

    try:
        current_category = int(category_id) if category_id and category_id.isdigit() else None
    except ValueError:
        current_category = None

    return render(request, 'app/product_list.html', {
        'products': products,
        'query': query,
        'categories': categories,
        'current_category': current_category,
        'current_gender': gender,
        'gender_choices': ['Men', 'Women', 'Kids', 'Baby'],
    })

@login_required
def add_to_cart_view(request, product_id):
    if request.user.is_superuser:
        messages.error(request, "Administrators cannot add items to cart.")
        return redirect('product_list')
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role == 'seller':
        messages.error(request, "Sellers cannot add items to cart. Please use a buyer account.")
        return redirect('seller_dashboard')

    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    selected_size = request.POST.get('selected_size') or request.GET.get('selected_size')

    if product.size and selected_size:
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, selected_size=selected_size)
    else:
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, selected_size=None)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success', 
            'message': f"{product.name} added to cart!",
            'cart_count': cart.cartitem_set.count()
        })

    messages.success(request, f"{product.name} added to cart!")
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))

@login_required
def buy_now_view(request, product_id):
    if request.user.is_superuser:
        messages.error(request, "Administrators cannot buy products.")
        return redirect('product_list')
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role == 'seller':
        messages.error(request, "Sellers cannot buy products. Please use a buyer account.")
        return redirect('seller_dashboard')

    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    selected_size = request.POST.get('selected_size') or request.GET.get('selected_size')

    if product.size and selected_size:
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, selected_size=selected_size)
    else:
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, selected_size=None)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('checkout')

@login_required
def remove_from_cart_view(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart_detail')

@login_required
def cart_detail_view(request):
    if request.user.is_superuser:
        return redirect('product_list')
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role == 'seller':
        return redirect('seller_dashboard')

    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'app/cart_detail.html', {'cart': cart})

@login_required
def checkout_view(request):
    if request.user.is_superuser:
        return redirect('product_list')
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role == 'seller':
        return redirect('seller_dashboard')

    cart, created = Cart.objects.get_or_create(user=request.user)
    if not cart.cartitem_set.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart_detail')

    addresses = ShippingAddress.objects.filter(user=request.user)
    address_form = ShippingAddressForm()

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'COD')
        address_id = request.POST.get('address_id')

        selected_address = None
        if address_id == 'new':
            address_form = ShippingAddressForm(request.POST)
            if address_form.is_valid():
                selected_address = address_form.save(commit=False)
                selected_address.user = request.user
                selected_address.save()
            else:
                return render(request, 'app/checkout.html', {
                    'cart': cart,
                    'addresses': addresses,
                    'address_form': address_form,
                    'payment_methods': Order.PAYMENT_METHOD_CHOICES
                })
        elif address_id:
            selected_address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
        else:
            messages.error(request, "Please select or add a shipping address.")
            return redirect('checkout')

        for item in cart.cartitem_set.all():
            if item.product.stock_count < item.quantity:
                messages.error(request, f"Insufficient stock for {item.product.name}. Only {item.product.stock_count} available.")
                return redirect('cart_detail')

        order = Order.objects.create(
            user=request.user,
            shipping_address=selected_address,
            total_price=cart.total_price,
            delivery_date=datetime.now().date() + timedelta(days=3),
            status='Pending',
            payment_method=payment_method
        )

        for item in cart.cartitem_set.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
                selected_size=item.selected_size
            )
            item.product.total_sales += item.quantity
            item.product.stock_count -= item.quantity
            item.product.save()

        cart.cartitem_set.all().delete()

        try:
            if request.user.email:
                item_lines = []
                for oi in order.items.all():
                    name = oi.product.name if oi.product else 'Product'
                    size_info = f' (Size: {oi.selected_size.upper()})' if oi.selected_size else ''
                    item_lines.append(
                        f"  • {name}{size_info}  x{oi.quantity}  — ₹{int(oi.price * oi.quantity):,}"
                    )

                items_text = "\n".join(item_lines)
                body = (
                    f"Hi {request.user.get_full_name() or request.user.username},\n\n"
                    f"🎉 Your order has been confirmed!\n\n"
                    f"Order ID  : #{order.id}\n"
                    f"Date      : {order.created_at.strftime('%d %b %Y, %I:%M %p')}\n"
                    f"Payment   : {order.get_payment_method_display()}\n"
                    f"Delivery  : {order.delivery_date.strftime('%d %b %Y')}\n\n"
                    f"--- Items Ordered ---\n"
                    f"{items_text}\n\n"
                    f"{'─'*36}\n"
                    f"Total Amount  :  ₹{int(order.total_price):,}\n"
                    f"{'─'*36}\n\n"
                    f"Thank you for shopping at findStyle! 🛍️\n"
                    f"We will notify you when your order ships.\n\n"
                    f"— The findStyle Team"
                )
                send_mail(
                    subject=f'Order Confirmed — #{order.id} | findStyle',
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[request.user.email],
                    fail_silently=True,
                )
        except Exception:
            pass

        messages.success(request, f"Order #{order.id} placed successfully with {order.get_payment_method_display()}! A confirmation email has been sent.")
        return render(request, 'app/checkout.html', {'success': True, 'order': order})

    return render(request, 'app/checkout.html', {
        'cart': cart, 
        'addresses': addresses,
        'address_form': address_form,
        'payment_methods': Order.PAYMENT_METHOD_CHOICES
    })

@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'app/orders.html', {'orders': orders})

@login_required
def cancel_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'Pending':
        order.status = 'Cancelled'
        order.save()
        for item in order.items.all():
            if item.product:
                item.product.stock_count += item.quantity
                item.product.total_sales -= item.quantity
                item.product.save()
        messages.success(request, f"Order #{order.id} has been cancelled.")
    else:
        messages.error(request, "Only pending orders can be cancelled.")
    return redirect('orders')

@login_required
def return_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'Delivered':
        order.status = 'Returned'
        order.save()
        messages.success(request, f"Order #{order.id} has been marked for return.")
    else:
        messages.error(request, "Only delivered orders can be returned.")
    return redirect('orders')

def logout_view(request):
    logout(request)
    return redirect('login')

def product_detail_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.filter(is_verified_purchase=True).order_by('-created_at')
    avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    available_sizes = []
    if product.size:
        available_sizes = [size.strip() for size in product.size.split(',')]
    delivery_date = (datetime.now() + timedelta(days=random.randint(2, 5))).strftime('%A, %b %d')
    pincode = request.GET.get('pincode')
    is_deliverable = None
    if pincode:
        is_deliverable = pincode[0] in '456' if len(pincode) >= 1 else False
    similar_products = Product.objects.filter(category=product.category).exclude(id=product_id).order_by('?')[:4]
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, products=product).exists()
    return render(request, 'app/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'reviews_count': reviews.count(),
        'delivery_date': delivery_date,
        'is_deliverable': is_deliverable,
        'pincode': pincode,
        'similar_products': similar_products,
        'in_wishlist': in_wishlist,
        'available_sizes': available_sizes
    })

@login_required
def toggle_wishlist_view(request, product_id):
    if request.user.is_superuser:
        return redirect('product_list')
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role == 'seller':
        return redirect('seller_dashboard')
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    if wishlist.products.filter(id=product_id).exists():
        wishlist.products.remove(product)
        messages.info(request, f"{product.name} removed from wishlist.")
    else:
        wishlist.products.add(product)
        messages.success(request, f"{product.name} added to wishlist.")
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))

@login_required
def wishlist_view(request):
    if request.user.is_superuser:
        return redirect('product_list')
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role == 'seller':
        return redirect('seller_dashboard')
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'app/wishlist.html', {'wishlist': wishlist})

@login_required
def update_cart_quantity_view(request, item_id, action):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if action == 'increment':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrement':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart_detail')

@login_required
def add_review_view(request, product_id):
    if request.user.is_superuser:
        return redirect('product_list')
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role == 'seller':
        return redirect('seller_dashboard')
    if request.method == 'POST':
        from .models import OrderItem
        product = get_object_or_404(Product, id=product_id)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        order_item_id = request.POST.get('order_item_id')
        if not rating or not comment:
            messages.error(request, "Rating and comment are required.")
            return redirect(request.META.get('HTTP_REFERER', 'product_list'))
        if order_item_id:
            try:
                order_item = OrderItem.objects.get(id=order_item_id, order__user=request.user)
                if hasattr(order_item, 'review'):
                    messages.warning(request, "You have already reviewed this item.")
                    return redirect('orders')
                Review.objects.create(
                    product=product,
                    user=request.user,
                    rating=rating,
                    comment=comment,
                    order_item=order_item,
                    is_verified_purchase=True
                )
                messages.success(request, "Review added successfully!")
            except OrderItem.DoesNotExist:
                messages.error(request, "Invalid order item.")
                return redirect('orders')
        else:
            Review.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment,
                is_verified_purchase=False
            )
            messages.success(request, "Review added successfully!")
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))

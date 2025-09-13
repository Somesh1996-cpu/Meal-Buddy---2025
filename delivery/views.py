from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.conf import settings
import razorpay

from .models import Customer, Restaurant, Item, Cart


def index(request):
    return render(request, 'delivery/index.html')


def open_signin(request):
    return render(request, 'delivery/signin.html')


def open_signup(request):
    return render(request, 'delivery/signup.html')


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')

        if Customer.objects.filter(username=username).exists():
            return HttpResponse("Duplicate username!")
        else:
            Customer.objects.create(
                username=username,
                password=password,
                email=email,
                mobile=mobile,
                address=address,
            )
            return render(request, 'delivery/signin.html')

    return render(request, 'delivery/signup.html')


def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            customer = Customer.objects.get(
                username=username, password=password)
            if username == 'admin':
                return render(request, 'delivery/admin_home.html')
            else:
                restaurantList = Restaurant.objects.all()
                return render(request, 'delivery/customer_home.html', {
                    "restaurantList": restaurantList,
                    "username": username
                })
        except Customer.DoesNotExist:
            return render(request, 'delivery/fail.html')

    return render(request, 'delivery/signin.html')


def open_add_restaurant(request):
    return render(request, 'delivery/add_restaurant.html')


def add_restaurant(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')

        if Restaurant.objects.filter(name=name).exists():
            return HttpResponse("Duplicate restaurant!")
        else:
            Restaurant.objects.create(
                name=name,
                picture=picture,
                cuisine=cuisine,
                rating=rating,
            )
            return render(request, 'delivery/admin_home.html')

    return render(request, 'delivery/add_restaurant.html')


def open_show_restaurant(request):
    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html', {"restaurantList": restaurantList})


def open_update_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    return render(request, 'delivery/update_restaurant.html', {"restaurant": restaurant})


def update_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    if request.method == 'POST':
        restaurant.name = request.POST.get('name')
        restaurant.picture = request.POST.get('picture')
        restaurant.cuisine = request.POST.get('cuisine')
        restaurant.rating = request.POST.get('rating')
        restaurant.save()

    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html', {"restaurantList": restaurantList})


def delete_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    restaurant.delete()
    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html', {"restaurantList": restaurantList})


def open_update_menu(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    itemList = restaurant.items.all()
    return render(request, 'delivery/update_menu.html', {"itemList": itemList, "restaurant": restaurant})


def update_menu(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = float(request.POST.get('price'))
        vegetarian = request.POST.get('vegetarian') == 'on'
        picture = request.POST.get('picture')

        if Item.objects.filter(name=name, restaurant=restaurant).exists():
            return HttpResponse('Item already exists!')
        else:
            Item.objects.create(
                restaurant=restaurant,
                name=name,
                description=description,
                price=price,
                vegetarian=vegetarian,
                picture=picture,
            )
            return HttpResponse('Item added successfully!')


def delete_menu_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    restaurant = item.restaurant
    item.delete()
    itemList = restaurant.items.all()
    return render(request, 'delivery/update_menu.html',
                  {"itemList": itemList, "restaurant": restaurant})


def view_menu(request, restaurant_id, username):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    itemList = restaurant.items.all()
    return render(request, 'delivery/customer_menu.html', {
        "itemList": itemList,
        "restaurant": restaurant,
        "username": username
    })


def add_to_cart(request, item_id, username):
    item = get_object_or_404(Item, id=item_id)
    customer = get_object_or_404(Customer, username=username)

    cart, created = Cart.objects.get_or_create(customer=customer)
    cart.items.add(item)
    return render(request, 'delivery/add_to_cart.html')


def show_cart(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    return render(request, 'delivery/cart.html', {
        "itemList": items,
        "total_price": total_price,
        "username": username
    })


def checkout(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    cart_items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    if total_price == 0:
        return render(request, 'delivery/checkout.html', {
            'error': 'Your cart is empty!',
        })

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    order_data = {
        'amount': int(total_price * 100),  # Amount in paisa
        'currency': 'INR',
        'payment_capture': '1',
    }
    order = client.order.create(data=order_data)

    return render(request, 'delivery/checkout.html', {
        'username': username,
        'cart_items': cart_items,
        'total_price': total_price,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'order_id': order['id'],
        'amount': total_price,
    })


def orders(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()

    cart_items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    if cart:
        cart.items.clear()

    return render(request, 'delivery/orders.html', {
        'username': username,
        'customer': customer,
        'cart_items': cart_items,
        'total_price': total_price,
    })

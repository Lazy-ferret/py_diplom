from django.contrib.auth import get_user_model, authenticate
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django.http import JsonResponse
from requests import get
from yaml import load as load_yaml, Loader
from django.contrib.auth.password_validation import validate_password

from backend.models import (
    ConfirmEmailToken,
    Shop,
    Category,
    ProductInfo,
    Product,
    Parameter,
    ProductParameter,
    Order,
    OrderItem,
    Contact,
    # User,
)
from backend.permissions import IsShop
from backend.serializers import (
    UserSerializer,
    ShopSerializer,
    CategorySerializer,
    ProductSerializer,
    OrderSerializer,
    ContactSerializer,
)
from backend.signals import new_user_registered
from django.core.mail import send_mail
from orders.settings import EMAIL_HOST_PASSWORD, EMAIL_HOST_USER

User = get_user_model()


class RegisterUserView(APIView):
    def post(self, request):
        data = request.data

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user_type = serializer.validated_data.get("type", "buyer")
            user = User.objects.create_user(
                email=serializer.validated_data["email"],
                username=serializer.validated_data["username"],
                password=serializer.validated_data["password"],
                type=user_type,
            )
            user.save()

            token = ConfirmEmailToken.objects.create(user=user)

            send_mail(
                "Подтверждение электронной почты",
                f"Ваш ключ подтверждения: {token.key}",
                EMAIL_HOST_USER,
                [user.email],
                auth_password=EMAIL_HOST_PASSWORD,
                fail_silently=False,
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConfirmEmailView(APIView):
    def post(self, request):
        key = request.data.get("key")
        token = ConfirmEmailToken.objects.get(key=key)
        if token:
            user = token.user
            user.is_active = True
            user.save()
            return Response({"message": "Email confirmed"}, status=status.HTTP_200_OK)
        return Response(
            {"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST
        )


class LoginUserView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(request, email=email, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid login data"}, status=status.HTTP_200_OK)


class UserDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContactView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        contacts = Contact.objects.filter(user=request.user)
        serializer = ContactSerializer(contacts, many=True)

    def post(self, request):
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopView(ListAPIView):
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer


class CreateShopView(APIView):
    permission_classes = [IsAuthenticated, IsShop]

    def post(self, request):
        user = request.user
        if user.type != "shop":
            return Response(
                {"error": "USer is not a shop"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ShopSerializer(data=request.data)
        if serializer.is_valid():
            shop = serializer.save(user=user)
            return Response(ShopSerializer(shop).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateShopView(APIView):
    permission_classes = [IsAuthenticated, IsShop]

    def put(self, request):
        shop_id = request.data.get("shop_id")
        shop = Shop.objects.filter(id=shop_id, user=request.user).first()
        if shop:
            serializer = ShopSerializer(shop, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Shop not found"}, status=status.HTTP_400_BAD_REQUEST)


class UpdateShopStatusView(APIView):
    permission_classes = [IsAuthenticated, IsShop]

    def put(self, request):
        user = request.user
        user.is_active = request.data.get("is_active")
        user.save()
        return Response({"message": "Status updated"})


class CategoryView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductsView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class SearchProductView(APIView):
    def get(self, request):
        query = request.query_params.get("query", "")
        products = Product.objects.filter(name__icontains=query)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class UpdatePriceView(APIView):
    permission_classes = [IsAuthenticated, IsShop]

    def put(self, request):
        shop_id = request.data.get("shop_id")
        product_infos = request.data.get("product_infos", [])
        shop = Shop.objects.filter(id=shop_id).first()
        if shop:
            for product_info_data in product_infos:
                product_info = ProductInfo.objects.filter(
                    id=product_info_data.get("id")
                ).first()
                if product_info:
                    serializer = ProductSerializer(product_info, data=product_info_data)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        return Response(
                            serializer.errors, status=status.HTTP_400_BAD_REQUEST
                        )

            return Response({"message": "Prices updated"})
        return Response({"error": "Shop not found"}, status=status.HTTP_400_BAD_REQUEST)


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        order = Order.objects.filter(user=request.user, state="cart").first()
        if order:
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        return Response({"massage": "Cart is empty"})

    def post(self, request):
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)
        product = Product.objects.filter(id=product_id).first()
        if product:
            order = Order.objects.filter(user=request.user, state="cart")
            if not order:
                order = Order.objects.create(user=request.user, state="cart")
            OrderItem.objects.create(order=order, product=product, quantity=quantity)
            return Response({"message": "Product added to cart"})
        return Response(
            {"error": "Product not found"}, status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request):
        product_id = request.data.get("product_id")
        order = Order.objects.filter(user=request.user, state="cart").first()
        if order:
            item = OrderItem.objects.filter(order=order, product_id=product_id).first()
            if item:
                item.delete()
                return Response({"message": "Product removed from cart"})
            return Response(
                {"error": "Product not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)


class ShopOrdersView(APIView):
    permission_classes = [IsAuthenticated, IsShop]

    def get(self, request):
        orders = Order.objects.filter(shop__user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class UserOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class PartnerUpdate(APIView):
# def post(self, request, *args, **kwargs):
#     if not request.user.is_authenticated:
#         return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
#
#     if request.user.type != 'shop':
#         return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
#
#     url = request.data.get('url')
#     if url:
#         validate_url = URLValidator()
#         try:
#             validate_url(url)
#         except ValidationError as e:
#             return JsonResponse({'Status': False, 'Error': str(e)})
#         else:
#             stream = get(url).content
#
#             data = load_yaml(stream, Loader=Loader)
#
#             shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
#             for category in data['categories']:
#                 category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
#                 category_object.shops.add(shop.id)
#                 category_object.save()
#             ProductInfo.objects.filter(shop_id=shop.id).delete()
#             for item in data['goods']:
#                 product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])
#
#                 product_info = ProductInfo.objects.create(product_id=product.id,
#                                                           external_id=item['id'],
#                                                           model=item['model'],
#                                                           price=item['price'],
#                                                           price_rcc=item['price_rcc'],
#                                                           quantity=item['quantity'],
#                                                           shop_id=shop.id)
#                 for name, value in item['paramaters'].items():
#                     parameter_object, _ = Parameter.objects.get_or_create(name=name)
#                     ProductParameter.objects.create(product_info_id=product_info.id,
#                                                     parameter_id=parameter_object.id,
#                                                     value=value)
#             return JsonResponse({'Status': True})
#
#     return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

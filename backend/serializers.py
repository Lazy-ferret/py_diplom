from rest_framework import serializers

from backend.models import (
    User,
    Shop,
    Product,
    Category,
    ProductInfo,
    Parameter,
    ProductParameter,
    Contact,
    Order,
    OrderItem,
)


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "user",
            "city",
            "street",
            "house",
            "structure",
            "building",
            "apartment",
            "phone",
        ]
        read_only_fields = ["user"]


class UserSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ["email", "username", "password", "type", "contacts"]


class ProductInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInfo
        fields = [
            "model",
            "external_id",
            "product",
            "shop",
            "quantity",
            "price",
            "price_rrc",
        ]


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    product_infos = ProductInfoSerializer(read_only=True, many=True)

    class Meta:
        model = Product
        fields = ["id", "name", "category", "product_infos"]


class CategorySerializer(serializers.ModelSerializer):
    products = ProductSerializer(read_only=True, many=True)

    class Meta:
        model = Category
        fields = ["id", "name", "products"]
        read_only_fields = ["id"]


class ShopSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(read_only=True, many=True)

    class Meta:
        model = Shop
        fields = ["id", "name", "state", "url", "categories"]
        read_only_fields = ["id"]


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = ["name"]


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ["product_info", "parameter", "value"]


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["user", "dt", "state", "contact"]


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["order", "product_info", "quantity"]

from time import sleep
import json
from rest_framework.test import APITestCase, URLPatternsTestCase
from django.urls import include, path, reverse
from rest_framework import status
from model_bakery import baker
from backend.models import User, Shop, ConfirmEmailToken


class OrdersApiTestCase(APITestCase, URLPatternsTestCase):
    urlpatterns = [path("api/v1/", include("backend.urls"))]

    def make_request(self, method, path, data=None, format="json", **extra):
        if format == "json":
            data = json.dumps(data)
            content_type = "application/json"

        response = self.client.generic(
            method, path, data, content_type=content_type, **extra
        )

        if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            sleep(1)
            response = self.client.generic(
                method, path, data, content_type=content_type, **extra
            )
        return response

    def test_register_user(self):
        url = reverse("user-register")
        count = User.objects.count()
        data = {
            "email": "test@test.com",
            "username": "test_user",
            "password": "123456AV",
        }
        response = self.make_request("POST", url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), count + 1)
        self.assertEqual(User.objects.all().last().type, "buyer")

    def test_register_shop(self):
        url = reverse("user-register")
        data = {
            "email": "test@test.com",
            "username": "test_shop_user",
            "password": "123456AV",
            "type": "shop",
        }
        response = self.make_request("POST", url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.all().last().type, "shop")

    def test_register_user_without_required(self):
        url = reverse("user-register")
        data = {"email": "test@test.com", "username": "test_user"}
        response = self.make_request("POST", url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["password"][0], "Обязательное поле.")

    def test_register_user_not_valid_password(self):
        url = reverse("user-register")
        data = {
            "email": "test@test.com",
            "username": "test_user",
            "password": "1234",
        }
        response = self.make_request("POST", url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertTrue(len(response.data["error"]) > 0)

    def test_register_not_unique_user(self):
        user = baker.make(User, email="test@test.com")
        user.save()
        url = reverse("user-register")
        count = User.objects.count()
        data = {
            "email": "test@test.com",
            "username": "test_user_copy",
            "password": "123456AV",
        }
        response = self.make_request("POST", url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), count)

    # def test_user_confirmation(self):
    #     user = baker.make(User, email="test@test.com")
    #     token = ConfirmEmailToken.objects.create(user=user)
    #     url = reverse("user-confirm")
    #     data = {"key": token.key}
    #     response = self.make_request('POST', url, data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.data['message'], 'Адрес электронной почты подтвержден')

from celery import shared_task
from django.core.mail import send_mail
from orders.settings import EMAIL_HOST_PASSWORD, EMAIL_HOST_USER
from django.core.files.base import ContentFile
import requests


@shared_task()
def new_user_registered(email, token):
    send_mail(
        "Подтверждение электронной почты",
        f"Ваш ключ подтверждения: {token}",
        EMAIL_HOST_USER,
        [email],
        auth_password=EMAIL_HOST_PASSWORD,
        fail_silently=False,
    )


@shared_task()
def user_email_confirmed(username, email):
    send_mail(
        "Подтверждение электронной почты",
        f"{username} адрес Вашей электронной почты: {email} подтвержден",
        EMAIL_HOST_USER,
        [email],
        auth_password=EMAIL_HOST_PASSWORD,
        fail_silently=False,
    )


@shared_task()
def new_order(email):
    send_mail(
        "Обновление статуса заказа",
        "Заказ сформирован",
        EMAIL_HOST_USER,
        [email],
        auth_password=EMAIL_HOST_PASSWORD,
        fail_silently=False,
    )


@shared_task
def process_user_avatar(user):
    response = requests.get(user.avatar_url)
    if response.status_code == 200:
        image_data = response.content
        user.avatar_thumbnail.save(
            f"{user.username}_thumbnail.jpg", ContentFile(image_data), save=False
        )
        user.save()

from celery import shared_task
from django.core.mail import send_mail
from orders.settings import EMAIL_HOST_PASSWORD, EMAIL_HOST_USER


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

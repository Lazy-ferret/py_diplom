from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django_rest_passwordreset.tokens import get_token_generator


STATE_CHOICES = (
    ("basket", "Статус корзины"),
    ("new", "Новый"),
    ("confirmed", "Подтвержден"),
    ("assembled", "Собран"),
    ("sent", "Отправлен"),
    ("delivered", "Доставлен"),
    ("canceled", "Отменен"),
)

USER_TYPE_CHOICES = (
    ("shop", "Магазин"),
    ("buyer", "Покупатель"),
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    REQUIRED_FIELDS = []
    objects = UserManager()
    USERNAME_FIELD = "email"
    email = models.EmailField(_("email address"), unique=True)
    company = models.CharField(max_length=50, verbose_name="Компания", blank=True)
    position = models.CharField(max_length=50, verbose_name="Должность", blank=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        _("username"),
        max_length=150,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    is_active = models.BooleanField(
        _("active"),
        default=False,
        help_text=_(
            "Designates whether this user should be treated as active."
            "Unselect this instead of deleting accounts."
        ),
    )
    type = models.CharField(
        max_length=5,
        verbose_name="Тип пользователя",
        choices=USER_TYPE_CHOICES,
        default="buyer",
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("email",)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Shop(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название магазина")
    url = models.URLField(verbose_name="Ссылка", null=True, blank=True)
    filename = models.CharField(max_length=50, null=True, blank=True)

    user = models.OneToOneField(
        User,
        verbose_name="Пользователь",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    state = models.BooleanField(verbose_name="Статус получения заказов", default=True)

    class Meta:
        verbose_name = "Магазин"
        verbose_name_plural = "Магазины"
        ordering = ("-name",)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название категории")
    shops = models.ManyToManyField(
        Shop, verbose_name="Магазины", related_name="categories", blank=True
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ("-name",)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        max_length=100, verbose_name="Название продукта", blank=True
    )
    category = models.ForeignKey(
        Category,
        verbose_name="Категория",
        related_name="products",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        ordering = ("-name",)

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name="Продукт",
        related_name="product_infos",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    shop = models.ForeignKey(
        Shop,
        verbose_name="Магазин",
        related_name="product_infos",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    model = models.CharField(max_length=80, verbose_name="Модель", blank=True)
    external_id = models.PositiveIntegerField(verbose_name="Внешний ИД")
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    price = models.PositiveIntegerField(verbose_name="Цена")
    price_rrc = models.PositiveIntegerField(verbose_name="Рекомендуемая розничная цена")

    class Meta:
        verbose_name = "Информация о продукте"
        verbose_name_plural = "Информация о продуктах"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "shop", "external_id"], name="unique_product_info"
            )
        ]


class Parameter(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название параметра")

    class Meta:
        verbose_name = "Параметр"
        verbose_name_plural = "Параметры"
        ordering = ("-name",)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(
        ProductInfo,
        verbose_name="Информация о продукте",
        related_name="product_paremeters",
        blank=True,
        on_delete=models.CASCADE,
    )
    parameter = models.ForeignKey(
        Parameter,
        verbose_name="Параметр",
        related_name="product_paremeters",
        blank=True,
        on_delete=models.CASCADE,
    )
    value = models.CharField(max_length=100, verbose_name="Значение")

    class Meta:
        verbose_name = "Параметр"
        verbose_name_plural = "Параметры"
        constraints = [
            models.UniqueConstraint(
                fields=["product_info", "parameter"], name="unique_product_parameter"
            )
        ]


class Contact(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        related_name="contacts",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    city = models.CharField(max_length=50, verbose_name="Город")
    street = models.CharField(max_length=80, verbose_name="Улица")
    house = models.CharField(max_length=10, verbose_name="Дом", blank=True)
    structure = models.CharField(max_length=10, verbose_name="Корпус", blank=True)
    building = models.CharField(max_length=10, verbose_name="Строение", blank=True)
    apartment = models.CharField(max_length=10, verbose_name="Квартира", blank=True)
    phone = models.CharField(max_length=20, verbose_name="Телефон")

    class Meta:
        verbose_name = "Контакты пользователя"
        verbose_name_plural = "Список контактов пользователя"

    def __str__(self):
        return f"{self.city} {self.street} {self.house}"


class Order(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        related_name="orders",
        blank=True,
        on_delete=models.CASCADE,
    )
    dt = models.DateTimeField(auto_now_add=True)
    state = models.CharField(
        max_length=20, verbose_name="Статус", choices=STATE_CHOICES
    )
    contact = models.ForeignKey(
        Contact, verbose_name="Контакт", blank=True, null=True, on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ("-dt",)

    def __str__(self):
        return str(self.dt)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name="Заказ",
        related_name="ordered_items",
        blank=True,
        on_delete=models.CASCADE,
    )
    product_info = models.ForeignKey(
        ProductInfo,
        verbose_name="Информация о продукте",
        related_name="ordered_items",
        blank=True,
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField(verbose_name="Количество")

    class Meta:
        verbose_name = "Заказанная позиция"
        verbose_name_plural = "Список заказанных позиций"
        constraints = [
            models.UniqueConstraint(
                fields=["order_id", "product_info"], name="unique_order_item"
            )
        ]


@staticmethod
class ConfirmEmailToken(models.Model):
    class Meta:
        verbose_name = "Токен подтверждение Email"
        verbose_name_plural = "Токены подтверждение Email"

    def generate_key(self):
        return get_token_generator().generate_token()

    user = models.ForeignKey(
        User,
        related_name="confirm_email_tokens",
        on_delete=models.CASCADE,
        verbose_name=_("The User which is associated to this password reset token"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("When was this token generated")
    )

    key = models.CharField(_("Key"), max_length=64, db_index=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)

    def __str__(self):
        return "Password reset token for user {user}".format(user=self.user)

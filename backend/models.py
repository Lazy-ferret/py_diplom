from django.db import models
from django.contrib.auth.models import AbstractUser

STATE_CHOICES = ()


# class User(AbstractUser):
#     pass


class Shop(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название магазина")
    url = models.URLField(verbose_name="Ссылка", null=True, blank=True)
    filename = models.CharField(max_length=50, null=True, blank=True)

    # user = models.OneToOneField(User, verbose_name='Пользователь',
    #                             blank=True, null=True,
    #                             on_delete=models.CASCADE)

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
        Shop, verbose_name="Магазины", related_name="categories", null=True, blank=True
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
    # user = models.ForeignKey(
    #     User,
    #     verbose_name="Пользователь",
    #     related_name="contacts",
    #     blank=True,
    #     on_delete=models.CASCADE,
    # )
    city = models.CharField(max_length=50, verbose_name="Город")
    street = models.CharField(max_length=80, verbose_name="Улица")
    house = models.CharField(max_length=10, verbose_name="Дом", blank=True)
    structure = models.CharField(max_length=10, verbose_name="Корпус", blank=True)
    building = models.CharField(max_length=10, verbose_name="Строение", blank=True)
    apartment = models.CharField(max_length=10, verbose_name="Квартира", blank=True)
    structure = models.CharField(max_length=20, verbose_name="Телефон")

    class Meta:
        verbose_name = "Контакты пользователя"
        verbose_name_plural = "Список контактов пользователя"

    def __str__(self):
        return f"{self.city} {self.street} {self.house}"


class Order(models.Model):
    # user = models.ForeignKey(
    #     User,
    #     verbose_name="Пользователь",
    #     related_name="orders",
    #     blank=True,
    #     on_delete=models.CASCADE,
    # )
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

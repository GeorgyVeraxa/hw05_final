from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls.base import reverse

from posts.models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса group/test-slug/
        cls.user = User.objects.create(username="username")
        cls.wrong_user = User.objects.create(username='GeorgeVeraksa')
        cls.group = Group.objects.create(
            title="Тест тайтл",
            description="Тестовое описание",
            slug="test-slug")
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=cls.user,
            group=cls.group)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        self.authorized_wrong_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        self.authorized_wrong_client.force_login(self.wrong_user)

    # Проверяем доступность страниц для незарегистрированных пользователей
    def test_address_correct(self):
        """Доступность страниц для незарегистрированного
        и зарегистрированного пользователей"""
        pages = {
            reverse("index"): 200,
            reverse("group_posts", args=["test-slug"]): 200,
            reverse("profile",
                    args=[f"{self.user.username}"]): 200,
            reverse("post",
                    args=[f"{self.user.username}",
                          f"{self.post.id}"]): 200,
            "dex/": 404,
        }
        for value, expected in pages.items():
            with self.subTest(value=value):
                response = self.guest_client.get(value)
                self.assertEqual(
                    response.status_code, expected)
                response = self.guest_client.get(value)
                self.assertEqual(
                    response.status_code, expected)

    def test_address_correct_redirect(self):
        """Доступность страниц для незарегистрированного пользователя"""
        pages = {
            reverse("new_post"): 302,
            reverse("post_edit",
                    args=[f"{self.user.username}",
                          f"{self.post.id}"]): 302,
        }
        for value, expected in pages.items():
            with self.subTest(value=value):
                response = self.guest_client.get(value)
                self.assertEqual(
                    response.status_code, expected)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            reverse("index"): "index.html",
            reverse("group_posts", args=["test-slug"]): "group.html",
            reverse("new_post"): "new.html",
            reverse("post_edit",
                    args=[f"{self.user.username}",
                          f"{self.post.id}"]): "new.html",
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_edit_pages_by_auth_user_who_is_not_author(self):
        """Проверяем возможность внести изменения другим авторизированным
        пользователем"""
        test_url = f"/{self.user.username}/{self.post.id}/edit/"
        response = self.authorized_wrong_client.get(test_url)
        self.assertEqual(response.status_code, 302)

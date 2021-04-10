# deals/tests/test_views.py
from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, Comment, Follow

User = get_user_model()


class TaskViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса group/test-slug/
        cls.user = User.objects.create(username="username")
        cls.following = User.objects.create(username="GeorgeVeraksa")
        cls.group = Group.objects.create(
            title="Тест тайтл",
            description="Тестовое описание",
            slug="test-slug")
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=cls.user,
            group=cls.group)
        cls.wrong_group = Group.objects.create(
            title="Не верная группа",
            description="ошибочный пост",
            slug="test-wrong")
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text="Текст комментария")

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(self.following)

    # Проверяем используемые шаблоны
    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: name"
        templates_pages_names = {
            "index.html": reverse("index"),
            "group.html": reverse("group_posts",
                                  kwargs={"slug": "test-slug"}),
            "new.html": reverse("new_post"),
        }
        # Проверяем, что при обращении к name вызывается
        # соответствующий HTML-шаблон
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверка словаря контекста страницы нового поста (в нём передаётся форма)
    def test_context(self):
        """Шаблон new сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("new_post"))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            # При создании формы поля модели типа TextField
            # преобразуются в CharField с виджетом forms.Textarea
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }

        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("index"))
        self.assertEqual(response.context["page"][0], self.post)

    def test_group_pages_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("group_posts", kwargs={"slug": self.group.slug})
        )
        self.assertEqual(response.context["group"], self.group)

    def test_index_shows_new_post(self):
        """Проверяем, что новый пост появится на странице index."""
        response = self.authorized_client.get(reverse("index"))
        self.assertEqual(len(response.context["page"]), 1)

    def test_group_shows_new_post(self):
        """Проверяем, что новый пост появится в соответствующей группе."""
        response = self.authorized_client.get(
            reverse("group_posts", kwargs={"slug": self.group.slug})
        )
        self.assertEqual(len(response.context["page"]), 1)

    def test_wrong_group_does_not_show_new_post(self):
        """Проверяем, что новый пост не появится в несоответствующей группе."""
        response = self.authorized_client.get(
            reverse("group_posts", kwargs={"slug": self.wrong_group.slug})
        )
        self.assertEqual(len(response.context["page"]), 0)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("post_edit", kwargs={
            "username": self.user.username,
            "post_id": self.post.id
        }))
        self.assertEqual(response.context["post"], self.post)

    def test_post_page_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("post", kwargs={
            "username": self.user.username,
            "post_id": self.post.id}))
        post_context = {
            "user": self.user,
            "post": self.post,
            "count": self.user.posts.all().count(), }
        for key, value in post_context.items():
            with self.subTest(key=value, value=value):
                context = response.context[key]
                self.assertEqual(context, value)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("profile", kwargs={"username": self.user.username})
        )
        self.assertEqual(response.context["user"], self.user)
        self.assertEqual(response.context["page"][0], self.post)

    def test_index_page_cache(self):
        """Проверяем корректнось кэширования шаблона index."""
        response = self.authorized_client.get(reverse("index"))
        previous_content = response.content
        Post.objects.create(text="Новый пост", author=self.user, )
        response = self.authorized_client.get(reverse("index"))
        next_content = response.content
        self.assertEqual(previous_content, next_content)
        cache.clear()

        response = self.authorized_client.get(reverse('index'))
        cleared_cache_content = response.content
        self.assertNotEqual(cleared_cache_content, next_content)

    def test_auth_user_can_follow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей."""
        author = self.following
        user = self.user
        Follow.objects.create(author=author, user=user)
        follower = user.follower.filter(author=author)[0]
        following = author.following.filter(user=user)[0]
        self.assertEqual(follower, following)
        count = Follow.objects.filter(author=author, user=user).count()
        self.assertEqual(count, 1)

    def test_auth_user_can_unfollow(self):
        """Авторизованный пользователь может отписываться от других
        пользователей."""
        author = self.following
        user = self.user
        Follow.objects.create(author=author, user=user)
        Follow.objects.filter(author=author, user=user).delete()
        count = Follow.objects.filter(author=author, user=user).count()
        self.assertEqual(count, 0)

    def test_follow_page_shows_new_post(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан на него."""
        author = self.following
        user = self.user
        new_post = Post.objects.create(text="Новый пост", author=author, )
        Follow.objects.create(author=author, user=user)
        response = self.authorized_client.get(reverse("follow_index"))
        self.assertEqual(len(response.context["page"]), 1)
        self.assertEqual(response.context["page"][0], new_post)
        response = self.another_authorized_client.get(reverse("follow_index"))
        self.assertEqual(len(response.context["page"]), 0)

    def test_only_authorized_client_can_comment(self):
        """Только авторизированный пользователь может комментировать посты."""
        kwargs = {"username": self.user.username, "post_id": self.post.id}
        response = self.authorized_client.get(reverse("post", kwargs=kwargs))
        comments_count = response.context["comments"].count()
        self.assertEqual(comments_count, 1)
        Comment.objects.create(post=self.post, author=self.user,
                               text="Новый комментарий")
        response = self.authorized_client.get(reverse("post", kwargs=kwargs))
        comments_count = response.context["comments"].count()
        self.assertEqual(comments_count, 2)


class PaginatorViewsTest(TestCase):
    @ classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="test_user")
        cls.client = Client()
        cls.client.force_login(cls.user)
        objs = [
            Post(
                text="Тестовый пост",
                author=cls.user,
            )
            for i in range(13)
        ]
        Post.objects.bulk_create(objs)

    def test_first_page_containse_ten_records(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(len(response.context.get("page").object_list), 10)

    def test_second_page_containse_three_records(self):
        response = self.client.get(reverse("index") + "?page=2")
        self.assertEqual(len(response.context.get("page").object_list), 3)

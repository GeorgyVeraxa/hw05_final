# deals/tests/tests_models.py
from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаём тестовую запись в БД
        # и сохраняем ее в качестве переменной класса
        cls.group = Group.objects.create(
            title="Тест тайтл",
            description="Тестовое описание",
            slug="Test_slug")
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=User.objects.create(username="User"),
            group=cls.group)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            "group": "Группа",
            "text": "Текст"
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            "group": "Выберите группу",
            "text": "Введите текст поста"
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_post_text_str(self):

        self.assertEqual(str(self.post), self.post.text[:15])

    def test_group_title_str(self):

        self.assertEqual(str(self.group), self.group.title)

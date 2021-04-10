from django.test import Client, TestCase
from django.urls.base import reverse


class AboutURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_public_url_exists_at_desired_location(self):
        """Cтраница 'url' доступна любому пользователю."""
        url_names = [
            reverse("about:author"),
            reverse("about:tech"),
        ]
        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

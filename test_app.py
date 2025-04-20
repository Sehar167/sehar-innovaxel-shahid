import unittest
from app import app, db, URL

class URLShortenerTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_create_short_url(self):
        response = self.app.post('/shorten', json={'url': 'https://www.example.com'})
        self.assertEqual(response.status_code, 201)
        self.assertIn('shortCode', response.json)

    def test_retrieve_original_url(self):
        # First, create a short URL
        response = self.app.post('/shorten', json={'url': 'https://www.example.com'})
        short_code = response.json['shortCode']
        # Now, retrieve it
        response = self.app.get(f'/shorten/{short_code}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['url'], 'https://www.example.com')

if __name__ == '__main__':
    unittest.main()

import unittest
import json
import sys
from app import app


class TestImageService(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        # populate database with imagecreator.py from create_test_db

    def test_get_wrong_endpoint(self):

        response = self.app.get('/wrong_end_point')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data["code"], 404)
        self.assertEqual(data["name"], "Not Found")
        self.assertEqual(data["description"],
                         "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.",
                         )
        
    def test_put_wrong_endpoint(self):

        response = self.app.put('/wrong_end_point')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data["code"], 404)
        self.assertEqual(data["name"], "Not Found")
        self.assertEqual(data["description"],
                         "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.",
                         )
        
    def test_wrong_method_correct_endpoint1(self):

        response = self.app.put('/groups')
        self.assertEqual(response.status_code, 405)
        data = response.get_json()
        self.assertEqual(data["code"], 405)
        self.assertEqual(data["name"], "Method Not Allowed")
        self.assertEqual(data["description"],
                         "The method is not allowed for the requested URL.",
                         )

    def test_wrong_method_correct_endpoint2(self):

        response = self.app.delete('/groups')
        self.assertEqual(response.status_code, 405)
        data = response.get_json()
        self.assertEqual(data["code"], 405)
        self.assertEqual(data["name"], "Method Not Allowed")
        self.assertEqual(data["description"],
                         "The method is not allowed for the requested URL.",
                         )
        
    def test_wrong_method_correct_endpoint3(self):

        response = self.app.post('/groups')
        self.assertEqual(response.status_code, 405)
        data = response.get_json()
        self.assertEqual(data["code"], 405)
        self.assertEqual(data["name"], "Method Not Allowed")
        self.assertEqual(data["description"],
                         "The method is not allowed for the requested URL.",
                         )
        
    def test_get_groups_with_images(self):
        response = self.app.get('/groups')
        self.assertEqual(response.status_code, 200)

    def test_update_image_status(self):
        image_id = '65071d4d96b52de451f914f8'
        data = {'status': 'accepted'}
        response = self.app.put(f'/images/{image_id}', 
                                data=json.dumps(data), 
                                content_type='application/json',
                                )
        self.assertEqual(response.status_code, 200)

    def test_get_statistics(self):
        response = self.app.get('/statistics')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
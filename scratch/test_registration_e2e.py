import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
import re
from app import app
import database

class TestRegistrationE2E(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_full_registration_and_validation(self):
        # 1. Clean up test record if exists
        test_email = "student999@culkomail.in"
        conn = database.get_db_connection()
        conn.execute("DELETE FROM students WHERE email = ?", (test_email,))
        conn.commit()
        conn.close()

        # 2. Get register page and extract CSRF token
        response = self.app.get('/register')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        self.assertTrue(csrf_match is not None, "CSRF token should be present in form")
        csrf_token = csrf_match.group(1)

        # 3. Post invalid email (not @culkomail.in)
        bad_response = self.app.post('/register', data={
            'csrf_token': csrf_token,
            'name': 'Test Student',
            'email': 'student999@gmail.com',
            'password': 'password123'
        }, follow_redirects=True)
        bad_html = bad_response.get_data(as_text=True)
        self.assertIn("Chandigarh University email", bad_html)

        # 4. Post valid registration
        reg_response = self.app.post('/register', data={
            'csrf_token': csrf_token,
            'name': 'Test Student',
            'email': test_email,
            'password': 'password123'
        }, follow_redirects=True)
        reg_html = reg_response.get_data(as_text=True)
        self.assertIn("Registration successful", reg_html)

        # 5. Verify record exists in DB
        conn = database.get_db_connection()
        student = conn.execute("SELECT * FROM students WHERE email = ?", (test_email,)).fetchone()
        conn.close()
        self.assertIsNotNone(student)
        self.assertEqual(student['name'], 'Test Student')

        # 6. Cleanup
        conn = database.get_db_connection()
        conn.execute("DELETE FROM students WHERE email = ?", (test_email,))
        conn.commit()
        conn.close()

if __name__ == '__main__':
    unittest.main()

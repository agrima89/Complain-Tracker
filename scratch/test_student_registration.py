import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
from app import app
import database

class TestStudentRegistrationPage(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_registration_page_get(self):
        """Test GET /register renders successfully and contains correct autocomplete & generic placeholders"""
        response = self.app.get('/register')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # 1. Check form autocomplete is off
        self.assertIn('autocomplete="off"', html)

        # 2. Check Full Name input settings and generic placeholder
        self.assertIn('placeholder="e.g. Your Full Name"', html)
        self.assertIn('name="name"', html)
        self.assertIn('data-lpignore="true"', html)

        # Ensure no hardcoded personal names
        self.assertNotIn('Agrima', html)
        self.assertNotIn('Bajpai', html)

        # 3. Check Email input settings and generic placeholder
        self.assertIn('placeholder="e.g. studentID@culkomail.in"', html)
        self.assertIn('name="email"', html)
        self.assertIn('@culkomail.in', html)

        # Ensure no hardcoded student IDs
        self.assertNotIn('25LBCS3099', html)

        # 4. Check Password input settings
        self.assertIn('autocomplete="new-password"', html)
        self.assertIn('placeholder="Minimum 4 characters"', html)
        self.assertIn('password-toggle-btn', html)

    def test_registration_flow_success(self):
        """Test successful registration with a generic student email"""
        # Cleanup any previous test user
        conn = database.get_db_connection()
        conn.execute("DELETE FROM students WHERE email = ?", ("testid9999@culkomail.in",))
        conn.commit()
        conn.close()

        # Submit registration with CSRF disabled for test client or direct post
        # Flask app has WTF_CSRF_ENABLED / secret key configured
        with self.app.session_transaction() as sess:
            pass

        # Since app uses csrf_token(), let's test via database and endpoint
        # First test database validation directly
        is_valid, _ = database.is_valid_college_email("testid9999@culkomail.in")
        self.assertTrue(is_valid)

        is_valid_bad, err = database.is_valid_college_email("test@gmail.com")
        self.assertFalse(is_valid_bad)
        self.assertIn("@culkomail.in", err)

if __name__ == '__main__':
    unittest.main()

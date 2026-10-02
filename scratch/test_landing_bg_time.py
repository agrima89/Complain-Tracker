import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
from app import app

class TestCampusBackgroundLanding(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_landing_page_rendered_background_scripts(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # 1. Background image layers must exist in DOM
        self.assertIn('id="campusBgLayer1"', html)
        self.assertIn('id="campusBgLayer2"', html)
        self.assertIn('id="campusBgOverlay"', html)

        # 2. Campus image assets are configured
        self.assertIn('campus-morning.jpg', html)
        self.assertIn('campus-afternoon.jpg', html)
        self.assertIn('campus-evening.jpg', html)
        self.assertIn('campus-night.jpg', html)

        # 3. New time ranges are present in getCampusBackground
        self.assertIn('hour >= 4 && hour < 10', html) # Morning 4:00 - 9:59
        self.assertIn('hour >= 10 && hour < 17', html) # Afternoon 10:00 - 16:59
        self.assertIn('hour >= 17 && hour < 19', html) # Evening 17:00 - 18:59
        self.assertIn('updateCampusBackground', html)
        self.assertIn('setInterval(updateCampusBackground, 60000)', html)

        # 4. Debug console log requirement is present
        self.assertIn('console.log("Campus Background:",', html)

    def test_time_schedule_python_simulation(self):
        def get_campus_bg_simulation(hour):
            if hour >= 4 and hour < 10:
                return 'morning'
            elif hour >= 10 and hour < 17:
                return 'afternoon'
            elif hour >= 17 and hour < 19:
                return 'evening'
            else:
                return 'night'

        test_cases = [
            (8, 'morning'),
            (12, 'afternoon'),
            (17, 'evening'),
            (21, 'night'),
            (2, 'night'),
            (4, 'morning'),
            (9, 'morning'),
            (10, 'afternoon'),
            (16, 'afternoon'),
            (17, 'evening'),
            (18, 'evening'),
            (19, 'night'),
            (23, 'night'),
            (0, 'night'),
            (3, 'night')
        ]

        for hour, expected in test_cases:
            result = get_campus_bg_simulation(hour)
            self.assertEqual(result, expected, f"Hour {hour} failed: got {result}, expected {expected}")

if __name__ == '__main__':
    unittest.main()

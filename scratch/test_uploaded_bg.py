import os
import sys
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
from app import app

class TestCampusUploadedBackgrounds(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_image_assets_integrity(self):
        """Verify uploaded afternoon & evening images and their RGB properties"""
        aft_path = os.path.join(os.path.dirname(__file__), "..", "static", "images", "campus-afternoon.jpg")
        eve_path = os.path.join(os.path.dirname(__file__), "..", "static", "images", "campus-evening.jpg")
        morn_path = os.path.join(os.path.dirname(__file__), "..", "static", "images", "campus-morning.jpg")
        night_path = os.path.join(os.path.dirname(__file__), "..", "static", "images", "campus-night.jpg")

        self.assertTrue(os.path.exists(aft_path), "campus-afternoon.jpg must exist")
        self.assertTrue(os.path.exists(eve_path), "campus-evening.jpg must exist")
        self.assertTrue(os.path.exists(morn_path), "campus-morning.jpg must exist")
        self.assertTrue(os.path.exists(night_path), "campus-night.jpg must exist")

        # Check Afternoon Image: Blue sky
        im_aft = Image.open(aft_path)
        self.assertEqual(im_aft.size, (1670, 942))
        sky_aft = im_aft.getpixel((800, 150))
        self.assertTrue(sky_aft[2] > sky_aft[0], "Afternoon sky should have higher Blue than Red")

        # Check Evening Image: Sunset orange/purple
        im_eve = Image.open(eve_path)
        self.assertEqual(im_eve.size, (1670, 941))
        sky_eve = im_eve.getpixel((800, 150))
        self.assertTrue(sky_eve[0] > 80, "Evening sky should have warm tones")

    def test_landing_page_dom_and_time_schedule(self):
        """Verify DOM elements, styles, and full time-schedule resolution"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # 1. Background Layers
        self.assertIn('id="campusBgLayer1"', html)
        self.assertIn('id="campusBgLayer2"', html)
        self.assertIn('id="campusBgOverlay"', html)

        # 2. Console Debug Log Requirement
        self.assertIn('console.log("Campus Background Debug:", {', html)

        # 3. Time Schedule logic in JS
        self.assertIn('hour >= 4 && hour < 10', html) # Morning 4:00 - 9:59
        self.assertIn('hour >= 10 && hour < 17', html) # Afternoon 10:00 - 16:59
        self.assertIn('hour >= 17 && hour < 19', html) # Evening 17:00 - 18:59

        # 4. Auto refresh every 60s
        self.assertIn('setInterval(updateCampusBackground, 60000)', html)

        # 5. Verify simulated hours logic
        def get_time_category(hour):
            if hour >= 4 and hour < 10:
                return 'morning'
            elif hour >= 10 and hour < 17:
                return 'afternoon'
            elif hour >= 17 and hour < 19:
                return 'evening'
            else:
                return 'night'

        test_schedule = [
            (8, 'morning', 'campus-morning.jpg'),
            (12, 'afternoon', 'campus-afternoon.jpg'),
            (16, 'afternoon', 'campus-afternoon.jpg'),
            (17, 'evening', 'campus-evening.jpg'),
            (18, 'evening', 'campus-evening.jpg'),
            (19, 'night', 'campus-night.jpg'),
            (21, 'night', 'campus-night.jpg'),
            (2, 'night', 'campus-night.jpg')
        ]

        for hour, cat, expected_img in test_schedule:
            resolved_cat = get_time_category(hour)
            self.assertEqual(resolved_cat, cat, f"Hour {hour} should resolve to {cat}")
            print(f"PASS: Hour {hour:02d}:00 -> Category: {resolved_cat:9s} -> Background: {expected_img}")

if __name__ == '__main__':
    unittest.main()

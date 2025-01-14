import unittest
import requests
import json

class TestHuggingFaceModelIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test parameters"""
        self.base_url = "http://huggingface-distilbert.default.139.59.55.131.sslip.io"
        self.predict_endpoint = f"{self.base_url}/v1/models/distilbert:predict"
        self.headers = {"content-type": "application/json"}

    def test_positive_sentiment_prediction(self):
        """Test model prediction with positive sentiments"""
        payload = {
            "instances": ["Hello, my dog is cute", "I am feeling happy"]
        }

        response = requests.post(
            self.predict_endpoint,
            headers=self.headers,
            data=json.dumps(payload)
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('predictions', response_data)
        
        # For positive sentiments, we expect 1
        for pred in response_data['predictions']:
            self.assertEqual(pred, 1)

    def test_negative_sentiment_prediction(self):
        """Test model prediction with negative sentiment"""
        payload = {
            "instances": ["I am very sad"]
        }

        response = requests.post(
            self.predict_endpoint,
            headers=self.headers,
            data=json.dumps(payload)
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('predictions', response_data)
        
        # For negative sentiment, we expect 0
        self.assertEqual(response_data['predictions'][0], 0)

    def test_invalid_input_format(self):
        """Test model prediction with invalid input format"""
        payload = {
            "invalid_key": ["This should fail"]
        }

        response = requests.post(
            self.predict_endpoint,
            headers=self.headers,
            data=json.dumps(payload)
        )

        # Assert response status code indicates error
        self.assertNotEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
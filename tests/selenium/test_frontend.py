from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import unittest

class FrontendTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up the WebDriver (e.g., ChromeDriver)
        cls.driver = webdriver.Chrome()  # Ensure chromedriver is in PATH
        cls.driver.implicitly_wait(10)  # Implicit wait for elements to load
        #cls.base_url = "http://localhost:3000"  # Replace with your app's URL
        cls.base_url = "https://ece-30861-phase2-24.vercel.app/"

    @classmethod
    def tearDownClass(cls):
        # Quit the WebDriver
        cls.driver.quit()

    def test_navigation_to_dashboard(self):
        """Test navigation to the Dashboard page."""
        self.driver.get(self.base_url)
        self.assertIn("Dashboard", self.driver.title)

        # Verify the presence of the header
        header = self.driver.find_element(By.TAG_NAME, "header")
        self.assertIsNotNone(header)

    def test_register_artifact(self):
        """Test registering a new artifact."""
        self.driver.get(self.base_url)

        # Navigate to the artifact registration form
        register_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Register Artifact')]")
        self.assertIsNotNone(register_button)

        # Fill in the artifact URL
        artifact_url_input = self.driver.find_element(By.ID, "artifact-url")
        artifact_url_input.send_keys("https://huggingface.co/gpt2")

        # Submit the form
        register_button.click()

        # Wait for success toast
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Artifact registered successfully')]")
        ))

    def test_view_model_details(self):
        """Test viewing model details."""
        self.driver.get(self.base_url)

        # Click on a model's "View" button
        view_button = self.driver.find_element(By.XPATH, "//button[@aria-label='View artifact details']")
        view_button.click()

        # Verify navigation to the Model Details page
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Model Details')]")
        ))

if __name__ == "__main__":
    unittest.main()
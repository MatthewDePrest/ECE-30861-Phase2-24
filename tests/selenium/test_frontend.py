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
        print("Current page title:", self.driver.title)  # Debugging log
        self.assertIn("Dashboard", self.driver.title, "Dashboard title not found in page title.")

        # Verify the presence of the header
        header = self.driver.find_element(By.TAG_NAME, "header")
        self.assertIsNotNone(header, "Header element not found.")

    def test_register_artifact(self):
        """Test registering a new artifact."""
        self.driver.get(self.base_url)
        print("Navigated to Dashboard for artifact registration.")

        # Navigate to the artifact registration form
        try:
            register_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Register Artifact')]")
            self.assertIsNotNone(register_button, "Register Artifact button not found.")
        except Exception as e:
            print("Error locating Register Artifact button:", e)
            raise

        # Fill in the artifact URL
        artifact_url_input = self.driver.find_element(By.ID, "artifact-url")
        artifact_url_input.send_keys("https://huggingface.co/gpt2")

        # Submit the form
        register_button.click()

        # Wait for success toast
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Artifact registered successfully')]")
            ))
        except Exception as e:
            print("Error waiting for success toast:", e)
            raise

    def test_view_model_details(self):
        """Test viewing model details."""
        self.driver.get(self.base_url)
        print("Navigated to Dashboard for viewing model details.")

        # Click on a model's "View" button
        try:
            view_button = self.driver.find_element(By.XPATH, "//button[@aria-label='View artifact details']")
            view_button.click()
        except Exception as e:
            print("Error locating View button:", e)
            raise

        # Verify navigation to the Model Details page
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Model Details')]")
            ))
        except Exception as e:
            print("Error waiting for Model Details page:", e)
            raise

    def test_system_health_page(self):
        """Test navigation to the System Health page."""
        self.driver.get(self.base_url + "/system-health")

        # Verify the presence of the System Health header
        header = self.driver.find_element(By.XPATH, "//h1[contains(text(), 'System Health')]")
        self.assertIsNotNone(header)

    def test_model_details_content(self):
        """Test content on the Model Details page."""
        self.driver.get(self.base_url + "/model-details")

        # Verify the presence of the Model Details header
        header = self.driver.find_element(By.XPATH, "//h1[contains(text(), 'Model Details')]")
        self.assertIsNotNone(header)

        # Verify the presence of a specific detail (e.g., model name)
        model_name = self.driver.find_element(By.XPATH, "//p[contains(text(), 'Model Name')]")
        self.assertIsNotNone(model_name)

    def test_header_navigation(self):
        """Test navigation links in the header."""
        self.driver.get(self.base_url)

        # Click on the "System Health" link in the header
        system_health_link = self.driver.find_element(By.LINK_TEXT, "System Health")
        system_health_link.click()

        # Verify navigation to the System Health page
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'System Health')]")
        ))

        # Navigate back to the home page
        self.driver.get(self.base_url)

        # Click on the "Model Details" link in the header
        model_details_link = self.driver.find_element(By.LINK_TEXT, "Model Details")
        model_details_link.click()

        # Verify navigation to the Model Details page
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Model Details')]")
        ))

    def test_artifact_filtering(self):
        """Test filtering artifacts on the Dashboard page."""
        self.driver.get(self.base_url)
        print("Navigated to Dashboard for artifact filtering.")

        # Locate the filter input box
        try:
            filter_input = self.driver.find_element(By.ID, "artifact-filter")
            self.assertIsNotNone(filter_input, "Filter input box not found.")
        except Exception as e:
            print("Error locating filter input box:", e)
            raise

        # Enter a filter term
        filter_input.send_keys("example")

        # Verify that the filtered results are displayed
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Filtered Result')]")
            ))
        except Exception as e:
            print("Error waiting for filtered results:", e)
            raise
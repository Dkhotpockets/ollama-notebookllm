"""
Simple Playwright Tests for NotebookLlama UI
Tests against a running Streamlit instance on port 8502
"""

import pytest
from playwright.sync_api import Page, expect, sync_playwright
import time


BASE_URL = "http://localhost:8502"


@pytest.fixture(scope="function")
def page():
    """Page fixture for each test"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True for headless
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        page.set_default_timeout(15000)  # 15 second timeout
        yield page
        context.close()
        browser.close()


class TestHomePage:
    """Tests for the Home page"""

    def test_home_page_loads(self, page: Page):
        """Test that the home page loads successfully"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)  # Wait for Streamlit to fully render

        # Check for key elements
        expect(page.locator("text=NotebookLlaMa")).to_be_visible(timeout=10000)

    def test_document_title_visible(self, page: Page):
        """Test document title field is visible"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Check for document title label
        expect(page.locator("text=Document Title")).to_be_visible(timeout=10000)

    def test_file_upload_visible(self, page: Page):
        """Test file upload is visible"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Check for file uploader
        expect(page.locator("text=Upload your source PDF file")).to_be_visible(timeout=10000)

    def test_sidebar_visible(self, page: Page):
        """Test sidebar is visible"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Check sidebar content - use more specific selector
        expect(page.locator("h2:has-text('Home')").first).to_be_visible(timeout=10000)


class TestNavigation:
    """Test navigation between pages"""

    def test_navigate_to_document_management(self, page: Page):
        """Test navigation to Document Management page"""
        page.goto(f"{BASE_URL}/Document_Management_UI")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Should not show 404
        assert "Page not found" not in page.content()

    def test_navigate_to_document_chat(self, page: Page):
        """Test navigation to Document Chat page"""
        page.goto(f"{BASE_URL}/Document_Chat")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Should not show 404
        assert "Page not found" not in page.content()

    def test_navigate_to_enhanced_rag(self, page: Page):
        """Test navigation to Enhanced RAG Chat page"""
        page.goto(f"{BASE_URL}/Enhanced_RAG_Chat")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Should not show 404
        assert "Page not found" not in page.content()

    def test_navigate_to_topic_discovery(self, page: Page):
        """Test navigation to Topic Discovery page"""
        page.goto(f"{BASE_URL}/Topic_Discovery")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Should not show 404
        assert "Page not found" not in page.content()

    def test_navigate_to_observability(self, page: Page):
        """Test navigation to Observability Dashboard page"""
        page.goto(f"{BASE_URL}/Observability_Dashboard")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Should not show 404
        assert "Page not found" not in page.content()


class TestDocumentManagementPage:
    """Tests for Document Management page"""

    def test_load_documents_button(self, page: Page):
        """Test Load Documents button exists"""
        page.goto(f"{BASE_URL}/Document_Management_UI")
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        # Look for Load Documents button
        load_btn = page.locator("button:has-text('Load Documents')")
        expect(load_btn).to_be_visible(timeout=10000)


class TestResponsiveness:
    """Test responsive design"""

    def test_mobile_viewport(self, page: Page):
        """Test in mobile viewport"""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Page should still load
        expect(page.locator("text=NotebookLlaMa")).to_be_visible(timeout=10000)

    def test_tablet_viewport(self, page: Page):
        """Test in tablet viewport"""
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Page should still load
        expect(page.locator("text=NotebookLlaMa")).to_be_visible(timeout=10000)


class TestAccessibility:
    """Basic accessibility tests"""

    def test_page_title(self, page: Page):
        """Test page has proper title"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        title = page.title()
        assert "NotebookLlaMa" in title or "Home" in title

    def test_headings_present(self, page: Page):
        """Test page has headings"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        headings = page.locator("h1, h2, h3")
        assert headings.count() > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from bs4 import BeautifulSoup
from your_module import format_and_extract_data, update_url_status, fetch, get_new_links, add_urls_to_queue, batch_insert_articles
from nltk.tokenize import sent_tokenize

class TestFormatAndExtractData(unittest.TestCase):

    @patch('your_module.fetch')
    @patch('your_module.update_url_status')
    @patch('your_module.get_new_links')
    @patch('your_module.add_urls_to_queue')
    @patch('your_module.batch_insert_articles')
    async def test_format_and_extract_data_success(self, mock_batch_insert_articles, mock_add_urls_to_queue, mock_get_new_links, mock_update_url_status, mock_fetch):
        # Mock data
        pool = MagicMock()
        queue_pool = MagicMock()
        url_id = 1
        url = 'https://www.example.com'
        depth = 1
        search_string = 'test'
        include_list = ['example.com']
        session = MagicMock()
        semaphore = MagicMock()
        article_data_batch = []
        batch_size = 10

        # Mock responses
        mock_fetch.return_value = """
        <html>
            <div class="caas-body">
                <h1>Test Headline</h1>
                <p>This is a test article with the word 'test' in it. <a href="https://www.example.com/link1">Link 1</a> </p>
                <p>Another sentence with 'test' and a link: <a href="https://www.example.com/link2">Link 2</a></p>
            </div>
        </html>
        """
        mock_get_new_links.return_value = ['https://www.example.com/link3']

        # Run the function
        await format_and_extract_data(pool, queue_pool, url_id, url, depth, search_string, include_list, session, semaphore, article_data_batch, batch_size)

        # Assertions
        mock_fetch.assert_called_once_with(session, url)
        mock_update_url_status.assert_called_once_with(queue_pool, url_id, 'crawled')
        mock_get_new_links.assert_called_once_with(url, include_list, session)
        mock_add_urls_to_queue.assert_called_once_with(queue_pool, ['https://www.example.com/link3'])
        mock_batch_insert_articles.assert_called_once_with(pool, article_data_batch)
        self.assertEqual(len(article_data_batch), 0)  # Batch should be cleared

        # Check article data
        expected_article_data = [
            (url, 2, 0, 2)  # 2 occurrences of 'test', 0 sentences without links, 2 sentences with links
        ]
        self.assertEqual(expected_article_data, article_data_batch)

    @patch('your_module.fetch')
    @patch('your_module.update_url_status')
    async def test_format_and_extract_data_no_caas_body(self, mock_update_url_status, mock_fetch):
        # Mock data
        pool = MagicMock()
        queue_pool = MagicMock()
        url_id = 1
        url = 'https://www.example.com'
        depth = 1
        search_string = 'test'
        include_list = ['example.com']
        session = MagicMock()
        semaphore = MagicMock()
        article_data_batch = []
        batch_size = 10

        # Mock responses
        mock_fetch.return_value = """
        <html>
            <div class="not-caas-body">
                <p>This is a test article without a caas-body div.</p>
            </div>
        </html>
        """

        # Run the function
        await format_and_extract_data(pool, queue_pool, url_id, url, depth, search_string, include_list, session, semaphore, article_data_batch, batch_size)

        # Assertions
        mock_fetch.assert_called_once_with(session, url)
        mock_update_url_status.assert_called_once_with(queue_pool, url_id, 'crawled')
        self.assertEqual(len(article_data_batch), 0)  # No article data should be added

    @patch('your_module.fetch')
    @patch('your_module.update_url_status')
    async def test_format_and_extract_data_fetch_error(self, mock_update_url_status, mock_fetch):
        # Mock data
        pool = MagicMock()
        queue_pool = MagicMock()
        url_id = 1
        url = 'https://www.example.com'
        depth = 1
        search_string = 'test'
        include_list = ['example.com']
        session = MagicMock()
        semaphore = MagicMock()
        article_data_batch = []
        batch_size = 10

        # Mock responses
        mock_fetch.return_value = None

        # Run the function
        await format_and_extract_data(pool, queue_pool, url_id, url, depth, search_string, include_list, session, semaphore, article_data_batch, batch_size)

        # Assertions
        mock_fetch.assert_called_once_with(session, url)
        mock_update_url_status.assert_called_once_with(queue_pool, url_id, 'crawled')
        self.assertEqual(len(article_data_batch), 0)  # No article data should be added

    @patch('your_module.fetch')
    @patch('your_module.update_url_status')
    async def test_format_and_extract_data_invalid_url(self, mock_update_url_status, mock_fetch):
        # Mock data
        pool = MagicMock()
        queue_pool = MagicMock()
        url_id = 1
        url = 'https://www.example.com#'
        depth = 1
        search_string = 'test'
        include_list = ['example.com']
        session = MagicMock()
        semaphore = MagicMock()
        article_data_batch = []
        batch_size = 10

        # Mock responses
        mock_fetch.return_value = None

        # Run the function
        await format_and_extract_data(pool, queue_pool, url_id, url, depth, search_string, include_list, session, semaphore, article_data_batch, batch_size)

        # Assertions
        mock_fetch.assert_not_called()
        mock_update_url_status.assert_called_once_with(queue_pool, url_id, 'crawled')
        self.assertEqual(len(article_data_batch), 0)  # No article data should be added

    @patch('your_module.fetch')
    @patch('your_module.update_url_status')
    @patch('your_module.get_new_links')
    @patch('your_module.add_urls_to_queue')
    @patch('your_module.batch_insert_articles')
    async def test_format_and_extract_data_batch_insert(self, mock_batch_insert_articles, mock_add_urls_to_queue, mock_get_new_links, mock_update_url_status, mock_fetch):
        # Mock data
        pool = MagicMock()
        queue_pool = MagicMock()
        url_id = 1
        url = 'https://www.example.com'
        depth = 1
        search_string = 'test'
        include_list = ['example.com']
        session = MagicMock()
        semaphore = MagicMock()
        article_data_batch = []
        batch_size = 2

        # Mock responses
        mock_fetch.return_value = """
        <html>
            <div class="caas-body">
                <h1>Test Headline</h1>
                <p>This is a test article with the word 'test' in it. <a href="https://www.example.com/link1">Link 1</a> </p>
                <p>Another sentence with 'test' and a link
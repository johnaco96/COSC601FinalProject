from typing import Union, Dict, List, Callable
import marqo
import requests
from bs4 import BeautifulSoup

def default_chunker(document: str) -> List[Dict[str, str]]:
    """Default chunker that returns the whole document as a single chunk."""
    return [{"text": document}]

class WebScraper:
    """Class to handle web scraping for course and advising webpages."""

    def __init__(self, urls: List[str]):
        self.urls = urls

    def scrape_courses(self, url: str) -> List[Dict[str, str]]:
        """Scrape course titles and descriptions from a course catalog."""
        scraped_courses = []
        try:
            print(f"Scraping course catalog: {url}")
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")


            titles = soup.find_all(class_="courseblocktitle")
            descriptions = soup.find_all(class_="courseblockdesc")

            for title, desc in zip(titles, descriptions):
                scraped_courses.append({
                    "title": title.get_text(strip=True),
                    "description": desc.get_text(strip=True)
                })

            if not scraped_courses:
                print(f"No course data found on {url}. Check selectors.")
        except Exception as e:
            print(f"Error scraping courses from {url}: {e}")
        return scraped_courses

    def scrape_general_content(self, url: str) -> List[str]:
        """Scrape general content from advising or program pages."""
        scraped_content = []
        try:
            print(f"Scraping general advising page: {url}")
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

   
            content_blocks = soup.find_all(["p", "h2", "h3", "li"])
            for block in content_blocks:
                text = block.get_text(strip=True)
                if text:  
                    scraped_content.append(text)

            if not scraped_content:
                print(f"No content found on {url}. Check structure.")
        except Exception as e:
            print(f"Error scraping general content from {url}: {e}")
        return scraped_content

    def scrape_data(self):
        """Scrape course titles, descriptions, and other advising content."""
        scraped_data = []
        for url in self.urls:
            try:
                print(f"Scraping {url}...")
                response = requests.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")


                course_blocks = soup.select(".courseblock")
                for block in course_blocks:
                    title = block.select_one(".courseblocktitle")
                    description = block.select_one(".courseblockdesc")
                    if title and description:
                        scraped_data.append({
                            "title": title.get_text(strip=True),
                            "description": description.get_text(strip=True)
                        })


                content_blocks = soup.select("p, h2, h3, li")
                for block in content_blocks:
                    text = block.get_text(strip=True)
                    if text:
                        scraped_data.append({
                            "title": "General Content",
                            "description": text
                        })
            except Exception as e:
                print(f"Error scraping {url}: {e}")
        return scraped_data
    

class MarqoKnowledgeStore:
    def __init__(
        self,
        client: marqo.Client,
        index_name: str,
        document_chunker: Callable[[str], List[Dict[str, str]]] = default_chunker,
        document_cleaner: Union[Callable[[str], str], None] = None,
    ) -> None:
        self._client = client
        self._index_name = index_name
        self._document_chunker = document_chunker
        self._document_cleaner = document_cleaner
        self._index_settings = {
            "model": "hf/all_datasets_v4_MiniLM-L6",
            "text_preprocessing": {
                "split_length": 3,
                "split_overlap": 1,
                "split_method": "sentence"
            }
        }
        self.reset_index()

    def query_for_content(self, query: str, content_var: str, limit: int = 5) -> List[str]:
        try:
            response = self._client.index(self._index_name).search(q=query, limit=limit)
            print("Query:", query)
            print("Marqo response:", response)
            return [res[content_var] for res in response["hits"] if res["_score"] > 0.3]
        except Exception as e:
            print(f"Error querying Marqo: {e}")
            return []


    def add_document(self, document: str) -> None:
        try:
            print(f"Adding document: {document[:100]}...")
            chunks = self._document_chunker(document)
            print(f"Document chunks: {chunks}") 
            self._client.index(self._index_name).add_documents(chunks, tensor_fields=['text'])
        except Exception as e:
            print(f"Error adding document: {e}")


    def reset_index(self) -> None:
        """Reset the index."""
        try:
            self._client.index(self._index_name).delete()
        except marqo.errors.MarqoWebError:
            print(f"Index '{self._index_name}' not found. Creating a new one.")
        except Exception as e:
            print(f"Error deleting index: {e}")
        try:
            self._client.create_index(index_name=self._index_name, **self._index_settings)
        except Exception as e:
            print(f"Error creating index: {e}")

    def fetch_and_add_towson_data(self, urls: List[str]) -> None:
        """Fetch data from Towson course and advising pages."""
        scraper = WebScraper(urls)
        scraped_data = scraper.scrape_data()

        for entry in scraped_data:
            print(f"Adding content: {entry[:100]}...")
            self.add_document(entry)


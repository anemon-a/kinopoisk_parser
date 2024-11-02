from dataclasses import dataclass, asdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup, PageElement
from time import sleep
import logging
import json
import re


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class Movie:
    name: str
    year: int
    country: str
    director: str
    rating: float | None
    is_on_kinopoisk: bool

    def __init__(
        self,
        name: PageElement,
        year: PageElement,
        country_and_director: PageElement,
        rating: PageElement,
        is_on_kinopoisk: PageElement,
    ):

        year = year.text.split(",")
        country = country_and_director.text.split(' • ')[0]
        director = country_and_director.text.split('Режиссёр: ')[1]

        self.name = name.text
        self.year = int(year[1][1:]) if not year[0] else int(year[0])
        self.country = country
        self.director = director
        self.rating = float(rating.text) if rating else None
        self.is_on_kinopoisk = True if is_on_kinopoisk else False


def get_movie_information(element: PageElement) -> Movie:
    name = element.find(
        "span",
        class_="styles_mainTitle__IFQyZ styles_activeMovieTittle__kJdJj",
    )
    year = element.find(
        "span", class_="desktop-list-main-info_secondaryText__M_aus"
    )
    country_and_director = element.find(
        "span", class_="desktop-list-main-info_truncatedText__IMQRP"
    )
    rating = element.find(
        "span", class_=re.compile("styles_kinopoiskValue__nkZEC")
    )
    is_on_kinopoisk = element.find(
        "element", class_="styles_onlineButton__ER9Vt styles_inlineItem___co22"
    )

    movie = Movie(name, year, country_and_director,
                  rating, is_on_kinopoisk)
    return movie


def parse_kinopoisk() -> None:
    data = []

    driver = webdriver.Chrome()
    url = "https://www.kinopoisk.ru/lists/movies/top_1000/"
    try:
        for page in range(1, 21):
            driver.get(url + f"?page={page}")
            sleep(3)
            soup = BeautifulSoup(driver.page_source, "lxml")
            element = soup.find_all("div", attrs={"data-tid": "679d3e26"})
            if not element:
                raise RuntimeError(
                    f"Can't find necessary elements on page {page}")

            for e in element:
                data.append(asdict(get_movie_information(element=e)))

            logger.info("Processed page %s", page)

    except Exception:
        logger.exception("Failed")
    finally:

        with open("movies.json", "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            if len(data) != 1000:
                logger.info(
                    "instead of 1000 movies, %s were recorded in the file", len(data))
            logger.info("Writed to file %s", "movies.json")


if __name__ == "__main__":
    parse_kinopoisk()

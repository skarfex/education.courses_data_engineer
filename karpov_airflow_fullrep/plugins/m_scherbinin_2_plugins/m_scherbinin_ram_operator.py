# """
# Practice HW for creating my own plugins
# """
#
# import logging
# import requests
# from airflow.models import BaseOperator
# from airflow import AirflowException
#
# class MarselRamSpeciesCountOperator(BaseOperator):
#     """
#        Count number of dead concrete species
#        """
#
#     template_fields = ('species_type',)
#     ui_color = "#e0ffff"
#
#     def __init__(self, species_type: str = 'Human', **kwargs) -> None:
#         super().__init__(**kwargs)
#         self.species_type = species_type
#
#     def get_page_count(self, api_url: str) -> int:
#         """
#         Get count of page in API
#         :param api_url
#         :return: page count
#         """
#         r = requests.get(api_url)
#         if r.status_code == 200:
#             logging.info("SUCCESS")
#             page_count = r.json().get('info').get('pages')
#             logging.info(f'page_count = {page_count}')
#             return int(page_count)
#         else:
#             logging.warning("HTTP STATUS {}".format(r.status_code))
#             raise AirflowException('Error in load page count')
#
#     def get_species_count_on_page(self, result_json: list) -> int:
#         """
#         Get count of concrete species_type in one page of character
#         :param result_json:
#         :return: species_count
#         """
#         species_count_on_page = 0
#         for one_char in result_json:
#             if one_char.get('species') == self.species_type:
#                 species_count_on_page += 1
#         logging.info(f'     {self.species_type} count_on_page = {species_count_on_page}')
#         return species_count_on_page
#
#     def execute(self, context):
#         """
#         Logging count of concrete species in Rick&Morty
#         """
#         species_count = 0
#         ram_char_url = 'https://rickandmortyapi.com/api/character?page={pg}'
#         for page in range(self.get_page_count(ram_char_url.format(pg='1'))):
#             r = requests.get(ram_char_url.format(pg=str(page + 1)))
#             if r.status_code == 200:
#                 logging.info(f'PAGE {page + 1}')
#                 species_count += self.get_species_count_on_page(r.json().get('results'))
#             else:
#                 logging.warning("HTTP STATUS {}".format(r.status_code))
#                 raise AirflowException('Error in load from Rick&Morty API')
#
#         logging.info(f'{self.species_type} in Rick&Morty: {species_count}')



import requests
import logging
import json

from airflow.models import BaseOperator
from airflow.exceptions import AirflowException


class MarselRamSpeciesCountOperator(BaseOperator):
    """
    Select top 3 locations with largest number of residents
    """

    template_fields = ('top_count',)
    ui_color = "#e0ffff"

    def __init__(self, top_count: int = 3, **kwargs) -> None:
        super().__init__(**kwargs)
        self.top_count = top_count

    def get_page_count(self, api_url: str) -> int:
        """Load page count
        Args:
            api_url (str): Url to API
        Raises:
            AirflowException: Error in load page count
        Returns:
            int: Page count
        """
        r = requests.get(api_url)
        if r.status_code == 200:
            logging.info("GET PAGE COUNT SUCCESS")
            page_count = r.json().get('info').get('pages')
            logging.info(f'page_count = {page_count}')
            return int(page_count)
        else:
            logging.warning("HTTP STATUS {}".format(r.status_code))
            raise AirflowException('Error in load page count')

    def execute(self, context):
        """Operator execution
        Args:
            context (_type_):
        Raises:
            AirflowException: Error in load from Rick&Morty API
        Returns:
            list: Top locations
        """
        result = []
        ram_char_url = 'https://rickandmortyapi.com/api/location?page={pg}'
        for page in range(self.get_page_count(ram_char_url.format(pg='1'))):
            r = requests.get(ram_char_url.format(pg=str(page + 1)))
            if r.status_code == 200:
                logging.info(f'PAGE {page + 1}')
                data = json.loads(r.text)
                for value in data['results']:
                    result.append([
                        value['id'],
                        value['name'],
                        value['type'],
                        value['dimension'],
                        len(value['residents']),
                    ])
            else:
                logging.warning("HTTP STATUS {}".format(r.status_code))
                raise AirflowException('Error in load from Rick&Morty API')
        return sorted(result, key=lambda x: x[-1], reverse=True)[:self.top_count]


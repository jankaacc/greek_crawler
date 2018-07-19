import json
import logging


import argparse
import requests
from lxml import html


module_logger = logging.getLogger('greek_alphabet_scraper') #intialize logger
handler = logging.StreamHandler() #default stream output, logs to be printed
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s') # the logs format
handler.setFormatter(formatter) #setting up logs format
module_logger.addHandler(handler) #add handler to module_logger
module_logger.setLevel(logging.INFO) #setting lowest log priority

class GreekLetter():
    """
    This is a class representing single Greek letter, in its constructor is accepting
    a row from greek letters table from link given in GreekLetterFactory constructor.
    Then in its methods is extracting proper information and wrap them with property decorator.
    staticmethod update_image is used to update information about each letter with url to its image,
    to_dict method is converting latter information in to dictionary.
    """
    BASE_URL = 'https://en.wikipedia.org{detail_path}'

    def __init__(self, item):
        """
        :param (html.HtmlElement) item: Contains greek letter data (row from table)
        """
        self.item = item

    @property
    def __name(self):
        return self.item.xpath('string(td[2]/a)')

    @property
    def __symbol(self):
        return self.item.xpath('string(td[1]//span[@lang="el"])')

    @property
    def __url(self):
        try:
            detail_path = self.item.xpath('td[2]/a')[0].attrib['href']
            return self.BASE_URL.format(detail_path=detail_path)
        except IndexError:
            module_logger.error('url not found')
            return None

    @property
    def __description(self):
        url = self.__url
        if not url:
            return ''
        module_logger.info('started crawling details for {}'.format(url))
        detail_page = requests.get(url)
        detail_page_html = html.fromstring(detail_page.content)
        first_paragraph = detail_page_html.xpath('string(//p[1])')
        return first_paragraph

    @staticmethod
    def update_image(data):
        """
        :param http response data: dictionary representing GreekLLetter in format
        given in GreekLetterFactory doc.
        method is updating given dictionary with new entry of letter image url.
        """
        detail_page = requests.get(data['url'])
        detail_page_html = html.fromstring(detail_page.content)
        image = detail_page_html.xpath('//a[@class = "image"]/img')
        image_index = 0
        # Need of catch an except is caused by that some of image xpath nodes
        # are different and don't have 'srcset' attribute.
        # If the node has 'srcset' attribute we need to check if it's a right
        # url for letter image because some of the letter detail pages have
        # different layout and have book image before letter image
        try:
            if 'book' in image[image_index].attrib['srcset']:
                image_index = 1
            image_url = image[image_index].attrib['srcset'].split(' ')[0]
        except IndexError:
            module_logger.error('image_url not found')
        else:
            if not image_url.startswith('http'): #just in case if url didn't contain https
                image_url = 'https:' + image_url
            data['image_url'] = image_url

    def to_dict(self):
        """
        :return: dictionary representing single greek letter object
        """
        return {'name': self.__name, 'letter': self.__symbol, 'url': self.__url,'description': self.__description}



class GreekLetterFactory():
    """
    This class accepts in constructor url for Greek alphabet from en.wikipedia.org and is
    extracting table of greek letters from the page in its constructor.
    Its __call__ function when is called is crating a list of GreekLetter objects and
    if the object is valid(some of the rows in greek letters table may be empty) saves each one
    as a dictionary in format:
    greek_alphabet = [{
		‘name’: ‘alpha’,
		‘letter’: ‘Αα’,
		‘url’: ‘https://en.wikipedia.org/wiki/Alpha'},
		‘description’: 'Alpha (uppercase Α, lowercase α; Ancient Greek: ἄλφα...
    }]
    """

    def __init__(self, base_url):
        """
        :param string base_url Contains url for Wikipedia site where you can find
         table of greek letters:
        """
        page = requests.get(base_url)
        page_html = html.fromstring(page.content)
        self.table = page_html.xpath('//*[@id="mw-content-text"]/div/table[2]//tr')

    def __call__(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return: list of valid greek letter dictionaries
        """
        filtered_letters = filter(
            lambda greek_letter: greek_letter['description'],
            [GreekLetter(greek_letter_html_element).to_dict() for greek_letter_html_element in self.table]
        )
        return list(filtered_letters)

def to_json_file(file_name, data):
    """
    Serialize letter list of dictionaries to json file
    :param string file_name: name of .json file to be saved
    :param unicode data: list of dictionaries
    :return:
    """
    with open(file_name, 'w') as json_file:
        json.dump(data, json_file)


def crawl_greek_letter(file_name=None):
    """
    :param string file_name: name of file to be saved
    :return: list of greek letters dictionaries
    if file_name is not None all data will be saved in .json format
    """
    greek_letter_factory = GreekLetterFactory('https://en.wikipedia.org/wiki/Greek_alphabet')
    greek_letters = greek_letter_factory()
    if file_name:
        to_json_file(file_name, greek_letters)
        module_logger.info('Greek letters saved to {}'.format(file_name))
    else:
        for letter_info in greek_letters:
            module_logger.info(letter_info)
    return greek_letters


def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-fn", "--file_name", help="name of json file to be saved eg. 'json_file.json'", type=str, default=None)
    # Print version
    parser.add_argument("--version", action="version", version='%(prog)s - Version 1.0')
    # Parse arguments
    args = parser.parse_args()
    return args




if __name__ == '__main__':
    # Parse the arguments
    args = parseArguments()
    greek_letters = crawl_greek_letter(args.file_name)
    for letter in greek_letters:
        GreekLetter.update_image(letter)
        module_logger.info(letter)

import scrapy
from urllib import parse
import json


class YelpSpider(scrapy.Spider):
    name = 'yelp_spider_two'
    custom_settings = {'FEED_URI': "yelps_%(time)s.json",
                       'FEED_FORMAT': 'json',
                       'ROBOTSTXT_OBEY': False,
                       'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'}

    def __init__(self, url):
        self.allowed_domains = ['yelp.com']
        self.start_urls = [url]

    def parse(self, responce):
        biz_title = responce.css('h1::text').extract_first()
        biz_img = responce.xpath('//meta[@property="og:image"]/@content').extract_first()
        biz_phone = responce.xpath('//p[starts-with(text(), "Phone number")]/following-sibling::p[1]/text()').extract_first()
        biz_id = responce.xpath('//meta[@name="yelp-biz-id"]/@content').extract_first()
        address_lines = responce.xpath('//address[contains(@class, "lemon--address")]/p/span/text()').extract()
        if len(address_lines) < 3:
            for x in range(3 - len(address_lines)):
                address_lines = [''] + address_lines
        if any(char.isdigit() for char in address_lines[2]):
            address_country = 'United States'
            if ',' in address_lines[2]:
                state_zip = address_lines[2].split(',')
                address_city = state_zip.pop(0)
                address_place = ', '.join(address_lines[0:2])
                state_zip = state_zip[0].strip().split(' ')
            else:
                state_zip = address_lines[2].split(' ')
                address_place = address_lines[0]
                address_city = address_lines[1]
            address_state = state_zip[0]
            address_zip = state_zip[1] if len(state_zip) == 2 else ' '.join(state_zip[1:])
        else:
            address_country = address_lines[2]
            state_zip = address_lines[1].split(',')
            address_city = state_zip.pop(0)
            address_place = ', '.join(address_lines[0:2])
            state_zip = state_zip[0].strip().split(' ')
            address_state = state_zip[0]
            address_zip = state_zip[1] if len(state_zip) == 2 else ' '.join(state_zip[1:])
        biz_address = {
            'country': address_country,
            'state': address_state,
            'city': address_city,
            'street': address_place,
            'zipcode': address_zip
        }
        rating = responce.xpath('//div[contains(@class, "i-stars--large")]/@aria-label').extract_first()
        biz_rating = rating.split(' ')[0]
        rating_num = responce.xpath('//p[contains(text(), "reviews")]/text()').extract_first()
        biz_rating_num = rating_num.split(' ')[0]
        biz_categories = responce.xpath('//a[starts-with(@href, "/c/")]/text()').extract()
        biz_work_hours = list()
        work_days = responce.xpath('//table[contains(@class, "hours-table")]/tbody/tr/th/p/text()').extract()
        work_hours = responce.xpath('//table[contains(@class, "hours-table")]/tbody/tr/td/ul/li/p/text()').extract()
        for i in zip(work_days, work_hours):
            biz_work_hours.append({'day': i[0], 'hours': i[1]})
        json_script = responce.xpath('//script[contains(@data-hypernova-key,"__yelp_main__BizDetailsApp__dynamic")]/text()').extract_first()
        json_data = json.loads(json_script.replace('<!--', '').replace('-->', ''))
        biz_about = list()
        if json_data['bizDetailsPageProps']['fromTheBusinessProps']:
            text_block = json_data['bizDetailsPageProps']['fromTheBusinessProps']['fromTheBusinessContentProps']
            biz_general_description = text_block['specialtiesText']
            biz_history = text_block['historyText']
            biz_established = text_block['yearEstablished']
            biz_person = text_block['businessOwner']['markupDisplayName'] if text_block['businessOwner'] else None
            biz_person_role = text_block['businessOwner']['localizedRole'] if text_block['businessOwner'] else None
            biz_person_bio = text_block['businessOwnerBio']
            biz_about.append({'specialties': biz_general_description,
                              'history': {'established': biz_established, 'history_text': biz_history},
                              'owner': {'name': biz_person, 'role': biz_person_role, 'about': biz_person_bio}})
        biz_highlights = list()
        if json_data['bizDetailsPageProps']['sponsoredBusinessHighlightsProps']:
            for i in json_data['bizDetailsPageProps']['sponsoredBusinessHighlightsProps']['businessHighlights']:
                biz_highlights.append(i['title'])
        biz_website = None
        if json_data['bizDetailsPageProps']['bizContactInfoProps']['businessWebsite']:
            encoded_reflink = parse.unquote(json_data['bizDetailsPageProps']['bizContactInfoProps']['businessWebsite']['href'])
            biz_website = encoded_reflink.split('=')[1].split('&')[0]
        scraped_data = {
            'title': biz_title,
            'url_yelp': responce.url,
            'business_id': biz_id,
            'img_main': biz_img,
            'phone': biz_phone,
            'address': biz_address,
            'rating': biz_rating,
            'reviews_count': biz_rating_num,
            'categories': biz_categories,
            'website': biz_website,
            'work_hours': biz_work_hours,
            'about': biz_about,
            'amenities_more': biz_highlights
        }

        yield scraped_data



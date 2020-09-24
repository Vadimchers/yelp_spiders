import scrapy
import json
from urllib import parse


class YelpSpider(scrapy.Spider):
    name = 'yelp_spider'
    custom_settings = {'FEED_URI': "yelps_%(time)s.json",
                       'FEED_FORMAT': 'json',
                       'ROBOTSTXT_OBEY': False}

    def __init__(self, url):
        self.allowed_domains = ['yelp.com']
        self.start_urls = [url]

    def parse(self, responce):
        print('Processing:', responce.url)
        # название
        biz_title = responce.css('h1::text').extract_first()
        # JSON объект со всеми данными на странице
        json_script = responce.xpath('//script[contains(@data-hypernova-key,"__yelp_main__BizDetailsApp__dynamic")]/text()').extract_first()
        json_data = json.loads(json_script.replace('<!--', '').replace('-->', ''))
        # ссылку на главное изображение
        biz_img = None
        if json_data['bizDetailsPageProps']['photoHeaderProps']:
            biz_img = json_data['bizDetailsPageProps']['photoHeaderProps']['photoHeaderMedias'][0]['srcUrl']
        # телефон (если есть)
        biz_phone = json_data['bizDetailsPageProps']['bizContactInfoProps']['phoneNumber']
        # внешний id бизнеса (id в системе yelp)
        biz_id = json_data['bizDetailsPageProps']['claimStatusGQLProps']['businessId']
        address_lines = json_data['bizDetailsPageProps']['mapBoxProps']['addressProps']['addressLines']
        if len(address_lines) < 3:
            for x in range(3 - len(address_lines)):
                address_lines = [''] + address_lines
        # адрес (разбитый на составляющие)
        # проверяю если ли запятая в последней строке списка, если есть, значит в строку добавили город, помимо штата и зипкода
        if any(char.isdigit() for char in address_lines[2]):
            address_country = json_data['gaConfig']['dimensions']['www']['content_country'][1]
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
        # средний рейтинг
        biz_rating = json_data['gaConfig']['dimensions']['www']['rating'][1]
        # количество отзывов
        biz_rating_num = json_data['bizDetailsPageProps']['ratingDetailsProps']['numReviews']
        # список категорий включая родительские категории
        biz_categories = json_data['gaConfig']['dimensions']['www']['category_paths_to_root'][1]
        # расписание работы
        biz_work_hours = list()
        for i in json_data['bizDetailsPageProps']['bizHoursProps']['hoursInfoRows']:
            biz_work_hours.append({'day': i['hoursInfo']['day'], 'hours': i['hoursInfo']['hours']})
        # описание (About the business)
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
        # удобства и прочее (Amenities and More)
        biz_highlights = list()
        if json_data['bizDetailsPageProps']['sponsoredBusinessHighlightsProps']:
            for i in json_data['bizDetailsPageProps']['sponsoredBusinessHighlightsProps']['businessHighlights']:
                biz_highlights.append(i['title'])
        # адрес веб-сайта
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



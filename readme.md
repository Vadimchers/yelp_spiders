yelp_spider - парсит JSON со страницы
\
yelp_spider_two - парсит часть данных через Xpath.

В обоих случаях отличается только способ получения данных. Для запуска оба паука нужно добавить в каталог проекта.

На входе принимает параметр url в котором нужно указать полную ссылку на страницу бизнеса yelp.
\
`scrapy crawl yelp_spider -a url=ссылка_на_страницу` \
`scrapy crawl yelp_spider_two -a url=ссылка_на_страницу`

Данные сохраняются в JSON файл `yelps_%(time)s.json` где `%(time)s` дата и время запуска
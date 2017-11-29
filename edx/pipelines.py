# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
from scrapy.exporters import CsvItemExporter


class HtmlFilePipeline(object):
    def process_item(self, item, spider):
        if spider.name == "edx_spider" and 'html' in item:
            file_name = item['title']
            directory = item['folder']
            if not os.path.exists('courses/' + directory):
                os.makedirs('courses/' + directory)

            with open('%s/%s.html' % ('courses/' + directory, file_name), 'w') as f:
                f.write(item['html'])

            del item['html']
        return item

#
# class CsvPipeline(object):
#     def __init__(self):
#         self.file = open("usa_cities_data.csv", 'w')
#         self.exporter = CsvItemExporter(self.file, unicode)
#         self.exporter.start_exporting()
#
#     def close_spider(self, spider):
#         self.exporter.finish_exporting()
#         self.file.close()
#
#     def process_item(self, item, spider):
#         print(item)
#         self.exporter.export_item(item)
#         return item

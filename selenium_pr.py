from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait as WDW
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import redis
import json
from lxml import etree

class JD_item(object):
	#初始化登陆账号：account和密码password，已经要搜索的关键字keywords
	def __init__(self,account,password,keywords,website = 'https://www.jd.com'):
		self.account = account
		self.password = password
		self.keywords = keywords
		self.browser = webdriver.Chrome()

	def login(self):
		#初始化登陆，由于未添加滑块验证功能，这里需要进行手动滑块验证
		self.browser.get('https://www.jd.com')
		wait = WDW(self.browser,10)
		self.browser.find_element_by_xpath('//*[@id="ttbar-login"]/a[1]').click()
		time.sleep(2)
		self.browser.find_element_by_xpath('//*[@id="content"]/div[2]/div[1]/div/div[3]').click()
		input = wait.until(EC.presence_of_element_located((By.ID,'loginname')))
		input.send_keys(self.account)
		input = wait.until(EC.presence_of_element_located((By.ID,'nloginpwd')))
		input.send_keys(self.password)
		button = self.browser.find_element_by_id('loginsubmit')
		button.click()

	def close(self):
		#关闭网页
		self.browser.close()

	def save_to_redis(self,name,item_dic):
		#将数据存储在redis数据库中（多维度数据大量爬取时建议使用sql或者mongodb数据库）
		try:
			db2 = redis.StrictRedis(host = 'localhost',port=6379,db = 5,password = 'lvmingfu123')
			db2.hset('JD:{}'.format(self.keywords),name,item_dic)
			print('存储完成一个')
		except:
			print('数据存储出现错误')

	def find_item(self):
		#模拟在京东主页面搜索框进行搜索
		try:
			wait = WDW(self.browser,10)
			input = wait.until(EC.presence_of_element_located((By.ID,'key')))
			input.clear()
			input.send_keys(self.keywords)
			self.browser.find_element_by_xpath('//*[@id="search"]/div/div[2]/button').click()
			self.parse_item()
		except:
			print('搜索框出现错误')

	def response(self):
		#将目前浏览的网页源代码转换成html
		return etree.HTML(self.browser.page_source)
	
	def parse_item(self):
		#爬取的物品的名称，价格，物品的主页面网址
		res = self.response()
		try:
			items = res.xpath('//*[@id="J_goodsList"]/ul/li')
			item_dic = {}
			for i in range(1,len(items)+1):
				name = ''.join(res.xpath('//*[@id="J_goodsList"]/ul/li[{}]/div/div[contains(@class,"-name")]//em/text()'.format(i))).replace(' ','')
				price = ''.join(res.xpath('//*[@id="J_goodsList"]/ul/li[{}]/div/div[contains(@class,"-price")]/strong//text()'.format(i)))
				item_url = res.xpath('//*[@id="J_goodsList"]/ul/li[{}]/div/div[contains(@class,"-name")]/a/@href'.format(i))[0]
				if 'https:' not in item_url:
					item_url = 'https:'+item_url
				item_dic = {
				'item_url':item_url,
				'price':price
				}
				self.save_to_redis(name,json.dumps(item_dic))
		except:
			print('物品爬取错误!')

def main():
	jd_account = '----' #----填入京东账号
	jd_pwd = '----'   #----填入京东密码
	item_word = '----' #----填入你要搜索的物品名称
	JD = JD_item(jd_account,jd_pwd,item_word) 
	JD.login()
	JD.find_item()
	time.sleep(5)
	JD.parse_item()
	JD.close()

if __name__=='__main__':
	main()
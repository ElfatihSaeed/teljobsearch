import os
import sys
import telebot
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from flask import Flask, request


load_dotenv()


API_KEY = os.getenv('API_KEY')
bot = telebot.TeleBot(API_KEY)
server = Flask(__name__)



@bot.message_handler(commands=['hello'])
def hello(message):
  bot.send_message(message.chat.id, "Hello!")

wlcm_msg = "!\nWelcome to @sudanjobsearch_bot.\nPlease send the job you are looking for"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,wlcm_msg)
    


def scra_sites(message,sites):

  if 'sudancareers' in sites:    
    jobs_list = ''
    keyword = message.text
    site_url  = f'https://www.sudancareers.com/job-vacancies-search-sudan/{keyword}?'
    print(f'Searching sudancareers at {site_url}')
    html_text = requests.get(site_url).text
    soup = BeautifulSoup(html_text,'lxml')
    jobs = soup.find_all('div',class_='job-description-wrapper',limit=1)
    for job in jobs:
      job_title = job.find('h5').text.strip()
      job_comp_date = job.find('p',class_='job-recruiter').text.split('|')
      job_post_date = job_comp_date[0]
      company_name = job_comp_date[1]      
      location = job.find('div',class_='col-lg-5 col-md-5 col-sm-5 col-xs-12 job-title').text.split('\n')[4].replace('Region of : ','').strip()
      job_details = 'https://www.sudancareers.com' + job.find('h5').a['href']
      jobs_list +=  f'Job Title   : {job_title}\n' + \
                    f'Company  : {company_name}\n' +  \
                    f'Location    : {location}\n' + \
                    f'<a href="{job_details}">More Details</a> \n'
    print(jobs_list)
    print(f'Done searching sudancareers\n')
    if jobs_list != '':
      try:
        bot.send_message(message.chat.id,jobs_list,parse_mode = "html",disable_web_page_preview=True)
      except :
        print("Unexpected error:", sys.exc_info()[0],'\n')
    
  if 'orooma' in sites:
    jobs_list = ''
    site_url = f'https://orooma.com/jobs/all/?q={keyword}' 
    print(f'Searching orooma at {site_url}')
    html_text = requests.get(site_url).text
    soup = BeautifulSoup(html_text,'lxml')
    jobs = soup.find_all('div',class_='card_group_item job_group_item',limit=1)
    for job in jobs:
      company_name = job.find('div',class_='m_0 p_0').text.strip()
      job_details = 'https://orooma.com' + job.find('a',class_='p_light overflow_auto d_block')['href']
      job_title = job.find('h4',class_='text_primary m_0').text.strip()
      jobs_list +=  f'Job Title   : {job_title}\n' + \
                    f'Company  : {company_name}\n' +  \
                    f'<a href="{job_details}">More Details</a> \n'
    print(jobs_list)
    print(f'Done searching orooma\n')
    if jobs_list != '':
      try:
        bot.send_message(message.chat.id,jobs_list,parse_mode = "html",disable_web_page_preview=True)
      except :
        print("Unexpected error:", sys.exc_info()[0],'\n')


@bot.message_handler()
def send_jobs(message):  
  sites = ['sudancareers','orooma']
  scra_sites(message,sites)


@server.route('/' + API_KEY, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://boiling-anchorage-39680.herokuapp.com/' + API_KEY)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

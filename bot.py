import os
import sys
import telebot
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from flask import Flask, request
import sqlite3
import psycopg2
import schedule
from datetime import datetime

load_dotenv()


API_KEY = os.getenv('API_KEY')
bot = telebot.TeleBot(API_KEY)
DATABASE_URL = os.getenv('DATABASE_URL')
server = Flask(__name__)
dtime = datetime.now()

wlcm_msg = "Welcome to @sudanjobsearch_bot.\nPlease send jobs names seperated by commas.\nIf you would you like to subscribe for a weekly report please send\n/Subscribe\n/help - Print help message"

def manage_sub(message,stmnt):
  # conn = sqlite3.connect('sudanjobsearch.db')
  conn = psycopg2.connect(DATABASE_URL, sslmode='require')
  cur = conn.cursor()
  cur.execute(stmnt)        
  conn.commit()
  cur.close()
  conn.close()


def chat_log(message):
  log_stmnt=f'insert into tbl_chat_log(chat_id,chat_text,dtime) values({message.chat.id},"{message.text}","{dtime}")' 
  print(log_stmnt)   
  manage_sub(message,log_stmnt)

@bot.message_handler(commands=['start'])
def start(message):
  print(message.text)
  chat_log(message)
  bot.send_message(message.chat.id,wlcm_msg)

    
@bot.message_handler(commands=['Unsubscribe'])
def unsubscribe(message):
  print(message.text)
  chat_log(message)
  mng_sub = f"delete from tbl_subscribers where sub_chat_id = '{message.chat.id}'"
  manage_sub(message,mng_sub) 
  bot.send_message(message.chat.id,'Unsubscribed succsesfully\nto subscribe again please send \n/Subscribe')

    
@bot.message_handler(commands=['Change'])
@bot.message_handler(commands=['Subscribe'])
def subscribe(message):
  print(message.text)
  chat_log(message)
  msg = bot.send_message(message.chat.id, "Ok, Please write jobs seperated by commas")
  bot.register_next_step_handler(msg, ck1)

def ck1(message):
  if not message.text.startswith("/"):
    print(message.text)
    chat_log(message)
    # mng_sub = f'replace into tbl_subscribers(sub_chat_id,jobs) values({message.chat.id},"{message.text}")'
    mng_sub = f"INSERT INTO tbl_subscribers (sub_chat_id,jobs) VALUES ({message.chat.id},'{message.text}') ON CONFLICT (sub_chat_id) DO UPDATE SET jobs = excluded.jobs;"
    manage_sub(message,mng_sub)
  bot.send_message(message.chat.id,f'"{message.text}"\nis your watch list now,\nto change please send /Change\nto unsubscribe please \nsend /Unsubscribe')



def search_send_jobs(user_id,keywords,sites):
  for keyword in keywords:
    if 'sudancareers' in sites:
      jobs_list = ''
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
          bot.send_message(user_id,jobs_list,parse_mode = "html",disable_web_page_preview=True)
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
          bot.send_message(user_id,jobs_list,parse_mode = "html",disable_web_page_preview=True)
        except :
          print("Unexpected error:", sys.exc_info()[0],'\n')
  bot.send_message(user_id,'To subscribe for a weekly report\n send /Subscribe')      


@bot.message_handler()
def send_jobs(message):  
  sites = ['sudancareers','orooma']
  chat_id = message.chat.id
  chat_jobs = message.text.split(',')
  print(chat_id,chat_jobs)
  chat_log(message)
  search_send_jobs(chat_id,chat_jobs,sites)



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


# bot.remove_webhook()
# bot.polling()

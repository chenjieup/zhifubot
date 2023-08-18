
from telegram.ext import Updater
from telegram.ext import CommandHandler, CallbackQueryHandler
import requests
import hashlib
import json
import re
import time
import datetime
import random
import os
header3 = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'}

proxies = {'https': '127.0.0.1:7890'}
# 这是开源版本
#https://lempay.org/submit.php
#商户ID：1110
#密钥：dwmD92It3PWPc7M3pW2WyQ6fjW9cf77Y

# 易支付API地址, 末尾需要包含/
API = 'https://api.lempay.org/'
# 商户ID
ID = 1110
# 商户密钥
KEY = 'dwmD92It3PWPc7M3pW2WyQ6fjW9cf77Y'
NOTIFY_URL = 'https://ilay1678.github.io/pages/pay/notify.html'

# 支付成功跳转地址
JUMP_URL = "https://ilay1678.github.io/pages/pay/notify.html"
# 支付超时时间(秒)
PAY_TIMEOUT = 300


def start(update, context):
    url = submit(money = "2.00",name="sss",trade_id= get_trade_id())
    context.bot.send_message(chat_id=update.effective_chat.id, text=url)

def main():
    PORT = int(os.environ.get('PORT', '8443'))
    APP_NAME='https://zhifubot.onrender.com/'
    TOKEN = "6282116592:AAF0g-K_VhaX-mDgYMLI940wHPs4vnUfYg0"
    #update = Updater(token = TOKEN,use_context=True,  request_kwargs={'proxy_url': 'socks5h://127.0.0.1:7890/'})
    update = Updater(token = TOKEN,use_context=True)
    #http://127.0.0.1:7890
    #https=127.0.0.1:7890;socks=127.0.0.1:7890
    #update = Updater(token = TOKEN,use_context=True)
    dispatcher = update.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    update.start_webhook(listen="0.0.0.0",port=PORT,url_path=TOKEN,webhook_url=APP_NAME + TOKEN)
    #update.start_polling(timeout=600)
    update.idle()


def get_trade_id():
    now_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = random.randint(0, 99)
    if random_num <= 10:
        random_num = str(0) + str(random_num)
    unique_num = str(now_time) + str(random_num)
    return unique_num

def make_data_dict(money, name, trade_id):
    #data = {'notify_url': NOTIFY_URL, 'pid': ID, 'return_url': JUMP_URL, 'sitename': '发卡机器人'}
    data = {'pid': ID}
    data.update(notify_url=JUMP_URL, return_url=JUMP_URL, money=money, name=name, out_trade_no=trade_id)
    return data


def submit(money, name, trade_id):
    data = {'notify_url': NOTIFY_URL, 'pid': ID, 'return_url': JUMP_URL}
    data.update(money=money, name=name, out_trade_no=trade_id)
    items = data.items()
    items = sorted(items)
    wait_sign_str = ''
    for i in items:
        wait_sign_str += str(i[0]) + '=' + str(i[1]) + '&'
    wait_for_sign_str = wait_sign_str[:-1] + KEY
    # print("输出待加密字符串" + '\n' + wait_sign_str)
    sign = hashlib.md5(wait_for_sign_str.encode('utf-8')).hexdigest()
    # print("输出订单签名：" + sign)
    data.update(sign=sign, sign_type='MD5')
    print(data)
    print(API + 'submit.php')
    try:
        #req = requests.post(API + 'submit.php', data=data,headers = header3,proxies = proxies)
        req = requests.post(API + 'submit.php', data=data)
        print(req.status_code)
        print(req.text)
        content = re.search(r"<script>(.*)</script>", req.text).group(1)
        print(content)
        if 'http' in content:
            pay_url = re.search(r"href=\'(.*)\'", content).group(1)
            return_data = {
                'status': 'Success',
                'type': 'url',
                'data': pay_url
            }
            return return_data
        else:
            pay_url = API + re.search(r"\.\/(.*)\'", content).group(1)
            print(pay_url)
            return_data = {
                'status': 'Success',
                'type': 'url',  # qrcode
                'data': pay_url
            }
            return return_data
    except Exception as e:
        print('submit | API请求失败')
        print(e)
        return_data = {
            'status': 'Failed',
            'data': 'API请求失败'
        }
        return return_data

def check_status(out_trade_no):
    try:
        req = requests.get(API + 'api.php?act=order&pid={}&key={}&out_trade_no={}'.format(ID, KEY, out_trade_no), timeout=5)
        # print(req.text)
        rst = re.search(r"(\{.*?\})", req.text).group(1)
        # print(rst)
        rst_dict = json.loads(rst)
        # print(rst_dict)
        code = str(rst_dict['code'])
        if int(code) == 1:
            # trade_no = str(rst_dict['trade_no'])
            # msg = str(rst_dict['msg'])
            pay_status = str(rst_dict['status'])
            if pay_status == '1':
                print('支付成功')

                return '支付成功'
            else:
                print('支付失败')
                return '支付失败'
        else:
            print('查询失败，订单号不存在')
            return '查询失败，订单号不存在'
    except Exception as e:
        print('check_status | 请求失败')
        print(e)
        return 'API请求失败'


if __name__ == '__main__':
    #data = make_data_dict(money = "2.00",name="sss",trade_id= get_trade_id())
    #url = submit(money = "2.00",name="VIP会员",trade_id= get_trade_id())
    # print(url)
    main()

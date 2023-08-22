
from telegram.ext import Updater
from telegram.ext import CommandHandler, CallbackQueryHandler
import telegram
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
import requests
import hashlib
import json
import re
import time
import datetime
import random
import os
import threading
from config import *
import done_postgres_database as dpd

header3 = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'}
proxies = {'https': '127.0.0.1:7890'}
# 易支付API地址, 末尾需要包含/
API = 'https://api.lempay.org/'
# 商户ID
ID = 1110
# 商户密钥
KEY = 'dwmD92It3PWPc7M3pW2WyQ6fjW9cf77Y'
NOTIFY_URL = "https://zhifubot.onrender.com"
# 支付成功跳转地址
JUMP_URL = "https://zhifubot.onrender.com"
# 支付超时时间(秒)
PAY_TIMEOUT = 300
GOODS_PRICE = '30.00'
ROUTE, CATEGORY, PRICE, SUBMIT, RESULT,RETURN,TRADE = range(7)
TOKEN = "6544328429:AAF4YnMWCWXGsuOON-A6L1pxbRpUi0vdyeY"
bot = telegram.Bot(token=TOKEN)

def start(update, context):
    print('进入start函数')
    keyboard = [
        [InlineKeyboardButton("解锁频道", callback_data=str('解锁频道')),
         InlineKeyboardButton("查询订单", callback_data=str('查询订单'))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        '选择您的操作：',
        reply_markup=reply_markup
    )
    return ROUTE

def category_filter(update, context):
    query = update.callback_query
    query.answer()
    keyboard = []
    #conn = sqlite3.connect('faka.sqlite3')
    #cursor = conn.cursor()
    #cursor.execute("select * from category ORDER BY priority")
    #categorys = cursor.fetchall()
    #conn.close()
    for key, value in pindao_dict.items():
        category_list = [InlineKeyboardButton(key, callback_data=key+'+'+str(value))]
        keyboard.append(category_list)
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="选择要解锁的频道：",
        reply_markup=reply_markup
    )
    return CATEGORY

def cancel(update, context):
    update.message.reply_text('期待再次见到你～')
    return ConversationHandler.END

def buy(update, context):
    query = update.callback_query
    query.answer()
    goods = update.callback_query.data.split('+')
    goods_name = goods[0]
    goods_id = int(goods[1])
    print(goods_name)
    print(goods_id)
    context.user_data['goods_name'] = goods_name
    context.user_data['goods_id'] = goods_id
    keyboard = [
            [InlineKeyboardButton("提交订单", callback_data=str('提交订单')),
             InlineKeyboardButton("下次一定", callback_data=str('下次一定'))]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="频道名：*{}*\n"
             "价格：*{}*\n"
             "介绍：*{}*\n".format(goods_name, GOODS_PRICE+'元', '本私有频道包含所有该地区的资源，且稳定更新中！进入频道后，可免费加入地区群组，资源互换！'),
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return SUBMIT

def submit_trade(update, context):
    query = update.callback_query
    query.answer()
    user = update.callback_query.message.chat
    user_id = str(user.id)
    user_name = user.username
    #try:
    #     conn = sqlite3.connect('faka.sqlite3')
    #     cursor = conn.cursor()
    #     cursor.execute("select * from trade where user_id=? and status=?", (user_id, 'unpaid'))
    trade_list = dpd.get_trade_list_from_sqlite(user_id,"unpaid")
    print(trade_list)
    if not trade_list:
        goods_name = context.user_data['goods_name']
        goods_id = context.user_data['goods_id']
        trade_id = get_trade_id()
        context.user_data['trade_id'] = trade_id
        #print('商品名：{}，价格：{}，交易ID：{}'.format(goods_name, "30元", trade_id))
        now_time = int(time.time())
        trade_data = make_data_dict(GOODS_PRICE, goods_name, trade_id)
        pay_url = submit(trade_data)
        print(pay_url)
        if pay_url != 'API请求失败':
            print('API请求成功，已成功返回支付链接')
            context.user_data['pay_url'] = pay_url
            result = dpd.insert_trade_in_sqlite(trade_id,goods_id,goods_name,user_id,user_name,now_time,'unpaid')
            if result:
                keyboard = [[InlineKeyboardButton("点击跳转支付", callback_data=str('点击跳转支付'),url=pay_url)],
                            [InlineKeyboardButton("完成支付", callback_data=str('完成支付'))]
                            ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text(
                    text="请在{}s内完成支付，超时支付会导致订单失败！\n"
                         "[点击这里]({})跳转支付，或者点击下方跳转按钮!\n"
                         "支付链接无法支付，可关掉VPN重试！\n"
                         "支付完成后，会自动发出频道链接；也可点击下方支付完成按钮获取！".format(str(PAY_TIMEOUT), pay_url),
                    parse_mode='Markdown',
                    reply_markup=reply_markup)
                return RESULT
            else:
                query.edit_message_text('系统出问题啦，可直接联系 @niwaiyou2 处理哦！')
                return ConversationHandler.END
        else:
            query.edit_message_text('系统出问题啦，可直接联系 @niwaiyou2 处理哦！')
            return ConversationHandler.END
    else:
        query.edit_message_text('您存在未支付订单，请支付或等待订单过期后重试！')
        return ConversationHandler.END
    # except Exception as e:
    #     print(e)

def trade_result(update, context):
    try:
        query = update.callback_query
        query.answer()
        trade_id = context.user_data['trade_id']
        pay_url = context.user_data['pay_url']
        keyboard = [
            [InlineKeyboardButton("点击跳转支付", callback_data=str('点击跳转支付'),url=pay_url)],
            [InlineKeyboardButton("完成支付", callback_data=str('完成支付'))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="您的订单正在处理中！\n"
                 "支付成功后会自动发出频道链接！\n"
                 "支付成功后也可点击完成支付按钮，主动获取频道链接！",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    except:
        pass
    rst = check_status(trade_id)
    if rst == "支付成功":
        dpd.update_paid_status_to_sqlite(trade_id)
        goods_name = context.user_data['goods_name']
        goods_id = context.user_data['goods_id']
        pindao_url = pindao_url_dict.get(int(goods_id))
        query.edit_message_text(
                text = "订单支付成功!\n"
                       "订单号：{}\n"
                       "商品：{}\n"
                       "频道链接：`{}`，请保存好！\n"
                       "使用方法：[点击这里]({})即可进入频道！\n".format(trade_id,goods_name, pindao_url,pindao_url),
                parse_mode='Markdown'
        )
        return ConversationHandler.END
    else:
        return RETURN

def cancel_trade(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="记得哦～下次一定")
    return ConversationHandler.END
def trade_filter(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="暂未开放！有问题直接联系 @niwaiyou2")
    return ConversationHandler.END

def get_trade_id():
    #trade_id类型为字符串
    now_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
    random_num = random.randint(0, 99)
    if random_num <= 10:
        random_num = str(0) + str(random_num)
    unique_num = str(now_time) + str(random_num)
    return unique_num


def make_data_dict(money, name, trade_id):
    #data = {'notify_url': NOTIFY_URL, 'pid': ID, 'return_url': JUMP_URL, 'sitename': '发卡机器人'}
    data = {'pid': ID,'sitename': '解锁资源'}
    data.update(notify_url=JUMP_URL, return_url=JUMP_URL, money=money, name=name, out_trade_no=trade_id)
    return data


def submit(data):
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
    try:
        req = requests.post(API + 'submit.php', data=data,headers = header3)
        content = re.search(r"<script>(.*)</script>", req.text).group(1)
        if 'http' in content:
            pay_url = re.search(r"href=\'(.*)\'", content).group(1)
            return pay_url
        else:
            pay_url = API + re.search(r"\.\/(.*)\'", content).group(1)
            return pay_url
    except Exception as e:
        print('submit | API请求失败')
        print(e)
        return 'API请求失败'

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

def check_trade():
    while True:
        print('---------------订单轮询开始---------------')
        # conn = sqlite3.connect('faka.sqlite3')
        # cursor = conn.cursor()
        # cursor.execute("select * from trade where status=?", ('unpaid',))
        # unpaid_list = cursor.fetchall()
        # conn.close()
        unpaid_list = dpd.get_unpaid_list_from_sqlite()
        print(unpaid_list)
        for i in unpaid_list:
            now_time = int(time.time())
            trade_id = i[0]
            user_id = i[3]
            create_time = i[5]
            goods_name = i[2]
            goods_id = i[1]
            sub_time = now_time - int(create_time)
            if sub_time >= PAY_TIMEOUT:
                # conn = sqlite3.connect('faka.sqlite3')
                # cursor = conn.cursor()
                # cursor.execute("update trade set status=? where trade_id=?", ('locking', trade_id,))
                # cursor.execute("update cards set status=? where id=?", ('active', card_id,))
                # conn.commit()
                # conn.close()
                dpd.delete_unpaid_status_in_sqlite(trade_id)
                #print("订单关闭")
                bot.send_message(
                    chat_id=int(user_id),
                    text='很遗憾，订单已关闭\n'
                         '订单号：`{}`\n'
                         '原因：逾期未付\n'.format(str(trade_id)),
                    parse_mode='Markdown',
                )
            else:
                try:
                    rst = check_status(trade_id)
                    if rst == '支付成功':
                        # conn = sqlite3.connect('faka.sqlite3')
                        # cursor = conn.cursor()
                        # cursor.execute("update trade set status=? where trade_id=?", ('paid', trade_id,))
                        # cursor.execute("DELETE FROM cards WHERE id=?", (card_id,))
                        # conn.commit()
                        # conn.close()
                        dpd.update_paid_status_to_sqlite(trade_id)
                        pindao_url = pindao_url_dict.get(int(goods_id))
                        #print('订单成功')
                        bot.send_message(
                            chat_id=(user_id),
                            text='恭喜！订单支付成功!\n'
                                 '订单号：`{}`\n'
                                 '商品：*{}*\n'
                                 '频道链接：`{}`\n'
                                 '使用方法：[点击这里]({})即可进入频道！\n'.format(str(trade_id),goods_name, pindao_url,pindao_url),
                            parse_mode='Markdown',
                        )
                except Exception as e:
                    print(e)
            time.sleep(3)
        print('---------------订单轮询结束---------------')
        time.sleep(10)

def main():
    PORT = int(os.environ.get('PORT', '8443'))
    APP_NAME='https://zhifubot.onrender.com/'
    #update = Updater(token = TOKEN,use_context=True,  request_kwargs={'proxy_url': 'socks5h://127.0.0.1:7890/'})
    update = Updater(token = TOKEN,use_context=True)
    dispatcher = update.dispatcher
    #dispatcher.add_handler(CommandHandler("start", start))
    start_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ROUTE: [
                CallbackQueryHandler(category_filter, pattern='^' + str('解锁频道') + '$'),
                CallbackQueryHandler(trade_filter, pattern='^' + str('查询订单') + '$'),
            ],
            CATEGORY: [
                CallbackQueryHandler(buy, pattern='.*?'),
            ],
            SUBMIT: [
                CallbackQueryHandler(submit_trade, pattern='^' + str('提交订单') + '$'),
                CallbackQueryHandler(cancel_trade, pattern='^' + str('下次一定') + '$')
            ],
            RESULT: [
                CallbackQueryHandler(trade_result, pattern='^' + str('完成支付') + '$'),
            ],
            RETURN:[
                CallbackQueryHandler(trade_result, pattern='^' + str('完成支付') + '$'),
            ]
        # TRADE: [
        #     MessageHandler(Filters.text, trade_query)
        # ],
        },
        conversation_timeout=60,
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(start_handler)
    update.start_webhook(listen="0.0.0.0",port=PORT,url_path=TOKEN,webhook_url=APP_NAME + TOKEN)
    #update.start_polling(timeout=600)
    update.idle()

if __name__ == '__main__':
    # trade_id = get_trade_id()
    # trade_data = make_data_dict("30.00", "深圳停车场", trade_id)
    # pay_url = submit(trade_data)
    # print(pay_url)
    thread = threading.Thread(target=check_trade)
    thread.start()
    main()

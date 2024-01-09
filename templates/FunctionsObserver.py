# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 16/06/2023  at 12:03 p.m. $'

import json
import os
import re
import threading
import time
from datetime import datetime, timezone
from typing import List, Any

import customtkinter as ctk
import openai
import requests
from bardapi import Bard
from bardapi.constants import SESSION_HEADERS
from dotenv import dotenv_values

from static.extensions import ventanasApp
from templates.FunctionsSQL import get_isAlive, update_isAlive, get_only_context, set_finish_chat

secrets = dotenv_values(".env")
openai.api_key = secrets["OPENAI_API_KEY_1"]
session = requests.Session()
session.headers = SESSION_HEADERS
session.cookies.set("__Secure-1PSID", secrets["PSID"])
session.cookies.set("__Secure-1PSIDTS", secrets["PSIDTS"])
session.cookies.set("__Secure-1PSIDCC", secrets["PSIDCC"])
bard = Bard(token=secrets["PSID"], session=session)


def get_response_bard(prompt: str) -> str:
    """
    Get the response from bard api
    :param prompt: prompt to send to bard
    :return: response from bard
    """
    try:
        response = bard.get_answer(prompt)["content"]
    except Exception as e:
        print(e)
        response = "Error in Bard API:  " + str(e)
    return response


def normalize_command(s: str):
    replacements = (
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "o"),
        ("ú", "u"),
    )
    for a, b in replacements:
        s = s.replace(a, b).replace(a.upper(), b.upper())
    s = s.lower()
    return s


def clean_command(command: str) -> str:
    """

    :param command: command for sql bot
    :return: cleaned command without special characters
    """
    message = normalize_command(command)
    message = message.replace("'''", "")
    numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    ignore = ["a", "ante", "bajo", "con", "contra", "de", "desde", "durante", "en", "entre", "hacia", "hasta",
              "mediante", "para", "por", "según", "sin", "sobre", "tras", "y", "e", "ni", "que", "o", "u", "pero",
              "aunque", "sino"]
    for item in ignore:
        message = message.replace(f" {item} ", " ")
    for number in numbers:
        match = re.search(f"{number}", message)
        if match is not None:
            index = match.regs[0][0]
            message = message[:index] + "" + message[index + 1:]
    message = message.replace("''", "'%'")
    message = message.replace("/", "")
    message = message.replace("  ", " ")
    message = message.replace("=", " like ")
    msg_list = message.split(",")
    message = " AND ".join(msg_list)
    matches = re.findall(r"'(.*?)'", message)
    if matches.__len__() != 0:
        for item in matches:
            message = message.replace(item, item.replace(" ", " OR "))
    return message


def clean_name(name: str) -> List:
    """

    :param name: name to be cleaned and make iterable
    :return: cleaned message list without special characters
    """
    message = normalize_command(name)
    ignore = ["a", "ante", "bajo", "con", "contra", "de", "desde", "durante", "en", "entre", "hacia", "hasta",
              "mediante", "para", "por", "según", "sin", "sobre", "tras", "y", "e", "ni", "que", "o", "u", "pero",
              "aunque", "sino"]
    for item in ignore:
        message = message.replace(f" {item} ", " ")
    message = message.replace("''", "'%'")
    message = message.replace("'generic'", "'%'")
    message = message.replace("  ", " ")
    msg_list = message.split(" ")
    return msg_list


def get_response(messages: list, temperature: float = 0.0) -> str:
    """
    Receives context and conversation with the bot and return a
    message from the bot.

    :param messages: chain of messages or context as a List[json].
    :param temperature:
    :return: answer (string)
    """
    # while 1:
    try:
        out = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            # model="gpt-4-0613",
            messages=messages,
            temperature=temperature,
        )
        # break
    except Exception as e:
        print("Error at openAI: ", e)
        return "Error at openAI"
    # print(str(response.choices[0].message["content"]))
    return out.choices[0].message["content"]


def list_and_data_generator():
    pass


def observer_chats_msg(chat_id, sender_id, time_start):
    """
    :param chat_id: chat id to observe.
    :param sender_id: sender id to observe.
    :param time_start: time to start the observation.
    :return:
    """
    counter = 0
    is_alive = 1
    flag_checker = True
    while counter <= 20:
        time_end = datetime.now(timezone.utc)
        time_diff = time_end - time_start
        print("time_diff: ", time_diff)
        if time_diff.seconds >= 60 + counter * 60:
            counter += 1
            print("Chat is still alive")
            result = get_isAlive(chat_id, sender_id)
            if result is None:
                print("Chat not found")
                break
            else:
                is_alive = result[0]
                if is_alive == 0:
                    print("Chat is dead")
                    flag_checker = False
                    break
        else:
            diff_counter = (60 + counter * 60) - time_diff.seconds
            time.sleep(diff_counter)
            continue
    if flag_checker:
        update_isAlive(chat_id, sender_id, is_alive)
    print("Observer finished")
    # run list and data generator
    t1 = threading.Thread(target=list_and_data_generator)
    t1.start()


def process_request(raw_request: str) -> tuple[str, list | None]:
    """
    :param raw_request: string  with the request to process.
    :return: tuple with the command and the data sent.
    """
    # Split the request
    datalist = raw_request.split(",")
    if len(datalist) <= 1:
        return "empty", None
    else:
        return datalist[0], datalist[1:]


def follow_conversation(data: list) -> str:
    """
    :param data: list with the data to follow the conversation.
    :return: string with the response to the request.
    """
    chat_id = data[0]
    sender_id = data[1]
    time_start = datetime.strptime(data[2], '%Y-%m-%d %H:%M:%S.%f')
    result = get_isAlive(chat_id, sender_id)
    if result is None:
        print("Chat not found")
        return "Chat not found"
    else:
        is_alive = result[0]
        print("chat is alive: ", is_alive)
        t1 = threading.Thread(target=observer_chats_msg, args=(chat_id, sender_id, time_start))
        t1.start()
        return "Observer initiated"


def update_log_file(filename: str, content: list, type_update: int = 1, thread=None):
    """
    This method is used to update the log file with the timestamp of the last message and the id of the chat.
    :param content:
    :param type_update: type of update
    :param filename: name of the file to modify
    :param thread
    """

    match type_update:
        case 1:
            timestamp, chats_id = content
            print("update_log_file: ", timestamp, chats_id)
            with open(filename, "a") as file:
                file.write(timestamp + ",;" + chats_id + "\n")
        case 2:
            timestamp, chat_id, products = content
            with open(filename, "a") as file:
                file.write(timestamp + ",;" + str(chat_id) + ",;" + str(products) + "\n")


def retrieve_content_chat_id(chat_id: str) -> tuple:
    """
    Retrieves the context of a conversation.
    :param chat_id: <string> id of the conversation
    :return: <list> list of dictionaries with the context of the conversation
    """
    result = get_only_context(chat_id)
    if result is not None:
        context = json.loads(result[0])
    else:
        context = None
    return context


def finish_chat(chat_id: str):
    """
    This method is used to finish a conversation.
    :param chat_id: string with the id of the conversation
    """
    set_finish_chat(chat_id)
    print("Chat finished:  ", chat_id)


def is_role_match(item, role):
    return item["role"] == role


def search_keyword_end_chat(chat):
    """
    This method is used to search a keyword in a conversation.
    :param chat: list with the context of the conversation
    """
    ending_terms = {
        "bot": {"Gracias por elegir Telintec": 0.7, "Te enviaremos": 0.8,
                "ha sido confirmado": 0.9},
        "user": {"/end": 1.0, "seria todo": 0.7, "adios": 0.9}
    }
    if len(chat) >= 2:
        for index, item in enumerate(chat[2:]):
            for role, patterns in ending_terms.items():
                if not is_role_match(item, role):
                    continue
                regex = re.compile("|".join(patterns.keys()))
                match = regex.search(item["content"])
                if match:
                    print("match found in " + str(index))
                    print(item["content"])


def check_conversation(chat_id: str, ia_tool="BARD") -> tuple[bool, list]:
    """
    This method is used to check the status of a conversation.
    :rtype: tuple that contains the is_finish flag and the list of products.
    :param chat_id: string with the id of the conversation
    :param ia_tool: string with the id of the tool for getting the list of products
    """
    conversation = retrieve_content_chat_id(chat_id)
    print("getting products from: ", chat_id)
    list_items_res = []
    if ia_tool == "BARD" and len(conversation) > 4:
        context = json.loads(open('files/context_list_generator.json', encoding='utf-8').read())["context"]
        message = context["content"]
        try:
            out = bard.get_answer(message + "\n" + str(conversation))['content']
            print("out: ", out)
        except Exception as e:
            print("Error bard: ", e)
            out = "no content"
        # noinspection RegExpRedundantEscape
        list_items_res = re.findall(r"\[(.*?)\]", out)
    elif ia_tool == "CHATGPT" and len(conversation) > 4:
        context_list = [json.loads(open('files/context_list_generator.json', encoding='utf-8').read())["context"], {
            'role': 'user',
            'content': f"{str(conversation[1:])}"}]
        out = get_response(context_list)
        # noinspection RegExpRedundantEscape
        list_items_res = re.findall(r'\[(.*?)\]', out)
    if len(list_items_res) > 0:
        list_items_res = list_items_res[0].split(",")
        is_finish = True
    else:
        list_items_res = []
        is_finish = False
    return is_finish, list_items_res


def handle_if_products(thread, products: list, chat_id: str, is_finish: bool, timestamp, time_window):
    """
    This method is used to handle the status of the chats in the database.
    :param time_window:
    :param timestamp:
    :param is_finish:
    :param chat_id:
    :param products:
    :param thread
    """
    if len(products) > 0 and is_finish:
        print("Products: ", products)
        filename = "Pedidos_{}.txt".format(datetime.now().strftime("%Y-%m-%d"))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_log_file(filename,
                        [timestamp,
                         chat_id, products], 2, thread)
        # put here code to notify the user
        message = "Hay pedidos del chat: {} y se guardo en el archivo.".format(chat_id)
        notifier = NotificationsUpdater(thread,
                                        [chat_id, message, 0, products, timestamp],
                                        0)
        notifier.start()
        print("Chat {} is not alive", chat_id)
        finish_chat(chat_id)
    else:
        # check if enough time has passed
        if (datetime.now(timezone.utc) -
            datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc)).seconds / 60 > time_window:
            print("Chat {} is not alive", chat_id)
            finish_chat(chat_id)


def handle_chat_status(thread, result: str, last_timestamp: str, time_wait):
    """
    This method is used to handle the status of the chats in the database.
    :param last_timestamp: timestamp for checking status
    :param time_wait: time window for a chat to be alive
    :param result: string with the result of the query
    :param thread
    """
    print("handle_chat_status: ", result)
    if len(result) > 0:
        message = f"Hay {len(result)} chats por revisar."
        notifier = NotificationsUpdater(thread,
                                        [0, message, 0, [], datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                                        delay=0.5)
        notifier.start()
        for chat in result:
            # check for products
            print("Chat is alive", chat[1])
            is_finish, products = check_conversation(chat[1])
            handle_if_products(thread, products, chat[1], is_finish, last_timestamp, time_wait)


def read_last_line_file(filename: str) -> str:
    """
    This method is used to read the last line of a file.
    :param filename: name of the file
    :return: string with the last line of the file
    """
    with open(filename, "rb") as file:
        try:
            file.seek(-2, os.SEEK_END)
            while file.read(1) != b'\n':
                file.seek(-2, os.SEEK_CUR)
        except OSError:
            file.seek(0)
        return file.readline().decode()


def read_last_timestamp(filename: str) -> str | None:
    """
    This method is used to read the last timestamp of a file.
    :param filename: name of the file
    :return: string with the last timestamp of the file
    """
    if os.path.exists(filename):
        last_line = read_last_line_file(filename)
        return last_line.split(",;")[0]
    else:
        return None


def get_timestamp_difference(timestamp_last: str, is_utc=True, scale="MINUTES") -> float:
    """
    This method is used to calculate the difference between two timestamps.
    :param scale: scale of the difference
    :param timestamp_last: timestamp for the last message
    :param is_utc: flag for utc timezone
    :return: int with the difference in minutes
    """
    if is_utc:
        timestamp_last = datetime.strptime(
            timestamp_last, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        timestamp_now = datetime.now(timezone.utc)
    else:
        timestamp_last = datetime.strptime(
            timestamp_last, "%Y-%m-%d %H:%M:%S")
        timestamp_now = datetime.now()
    match scale:
        case "MINUTES":
            factor = 60
        case "SECONDS":
            factor = 1
        case _:  # default
            factor = 1
    return (timestamp_now - timestamp_last).seconds / factor


def create_button_side_menu(master, row, column, text, image=None, command=None):
    """
    This method is used to create a button in the side menu.
    :param image: image for the button
    :param command: command for the button
    :param master: master for the button
    :param row: row for the button
    :param column: column for the button
    :param text: text for the button
    """
    button = ctk.CTkButton(master, corner_radius=0, height=40, border_spacing=10,
                           text=text, fg_color="transparent",
                           text_color=("#fff", "#fff"),
                           hover_color=("gray70", "gray30"),
                           image=image, anchor="w", command=command)
    button.grid(row=row, column=column, sticky="nsew", pady=5, padx=30)
    return button


def compare_permissions_windows(user_permissions: list) -> tuple[bool, Any] | tuple[bool, None]:
    """
    This method is used to compare the permissions of a user.
    :param user_permissions: list of permissions of the user
    :return: bool with the result of the comparison
    """
    for permission in user_permissions:
        if permission in ventanasApp.keys():
            return True, ventanasApp[permission]
    return False, None


class NotificationsUpdater(threading.Thread):
    def __init__(self, master, data, delay):
        super().__init__()
        self.master = master
        self.data = data
        self.delay = delay

    def run(self):
        time.sleep(self.delay)
        self.master.send_notification(self.data)

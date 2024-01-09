# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 26/dic./2023  at 14:35 $'

import pickle

import openai

from static.extensions import secrets
from openai import OpenAI

import time

client = OpenAI(api_key=secrets.get("OPENAI_API_KEY_1"))
openai.api_key = secrets["OPENAI_API_KEY_1"]


def upload_file_openai(file_path):
    e = None
    try:
        file = client.files.create(
            file=open(file_path, "rb"),
            purpose="assistants"
        )
    except Exception as e:
        print(e)
        file = None
    return file, e


def create_assistant_openai(model="gpt-4-1106-preview", files=None, instructions=None):
    e = None
    file_IDS = [item["file_openai"].id for item in files] if files is not None else []
    try:
        assistant = client.beta.assistants.create(
            name="Assistant",
            instructions=instructions,
            model=model,
            tools=[{"type": "code_interpreter"}, {"type": "retrieval"}],
            file_ids=file_IDS
        )
    except Exception as e:
        print(e)
        assistant = None
    return assistant, e


def create_thread_openai():
    e = None
    try:
        thread = client.beta.threads.create()
    except Exception as e:
        print(e)
        thread = None
    return thread, e


def create_message_openai(thread_id, msg, role):
    e = None
    try:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role=role,
            content=msg
        )
    except Exception as e:
        print(e)
        message = None
    return message, e


def run_thread_openai(thread_id, assistant_id):
    e = None
    try:
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id)
    except Exception as e:
        print(e)
        run = None
    return run, e


def retrieve_runs_openai(thread_id, run_id):
    e = None
    try:
        while True:
            runs = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            if runs.status == "completed":
                break
            time.sleep(0.5)
    except Exception as e:
        print(e)
        runs = None
    return runs, e


def retrieve_messages_openai(thread_id):
    e = None
    try:
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )
    except Exception as e:
        print(e)
        messages = None
    return messages, e


def get_response_chat_completion(messages: list) -> str:
    """
    Receives context and conversation with the bot and return a
    message from the bot.

    :param messages: chain of messages or context as a List[json].
    :return: answer (string)
    """
    # while 1:
    client_1 = OpenAI(api_key=secrets.get("OPENAI_API_KEY_1"))
    try:
        print(messages)
        out = client_1.chat.completions.create(
            # model="gpt-3.5-turbo",
            model="gpt-4-0613",
            messages=messages,
        )
        # break
    except Exception as e:
        print("Error at openAI: ", e)
        return "Error at openAI"
    return out.choices[0].message.content


def get_response_assistant(message: str, files: list = None, instructions: str = None, department=None) -> tuple[list | None, str]:
    """
    Receives context and conversation with the bot and return a
    message from the bot.

    :param department:
    :param instructions:
    :param files: list of files to upload
    :param message:message
    :return: answer (string)
    """
    e = None
    answer = ""
    try:
        if len(files) > 0:
            print(files)
            for i, item in enumerate(files):
                if files[i]["status"] == "upload":
                    continue
                files[i]["file_openai"], error = upload_file_openai(item["path"])
                files[i]["file_id"] = files[i]["file_openai"].id
                files[i]["status"] = "upload"
            with open(f'files/files_{department}_openAI_cache.pkl', 'wb') as file:
                pickle.dump(files, file)
    except Exception as e:
        print("Error at uploading files on openAI: ", e)
        return files, "Error at uploading files on openAI"
    try:
        assistant, error = create_assistant_openai(files=files, instructions=instructions)
    except Exception as e:
        print("Error at creating assistant on openAI: ", e)
        return files, "Error at creating assistant on openAI"
    try:
        thread, error = create_thread_openai()
        message_obj, error = create_message_openai(thread.id, message, "user")
        run, error = run_thread_openai(thread.id, assistant.id)
        run, error = retrieve_runs_openai(thread.id, run.id)
        msgs, error = retrieve_messages_openai(thread.id)
        print(msgs)
        for msg in reversed(msgs.data):
            answer += msg.content[0].text.value + "\n" if msg.role == "assistant" else ""
    except Exception as e:
        print("Error at getting response on openAI: ", e)
        return files, "Error at creating getting response on openAI"
    return files, answer


def get_files_list_openai(department):
    files = []
    e = None
    try:
        files_openai = client.files.list(purpose="assistants")
        files = files_openai.data
        if len(files) == 0:
            files = []
    except Exception as e:
        print("Error at getting files list on openAI: ", e)
    return files, e


def delete_file_openai(file_id):
    e = None
    try:
        res = client.files.delete(file_id=file_id)
        flag = res.deleted
    except Exception as e:
        flag = False
        print("Error at deleting file on openAI: ", e)
    return flag, e

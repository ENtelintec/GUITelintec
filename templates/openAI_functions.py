# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 26/dic./2023  at 14:35 $'

from static.extensions import secrets
from openai import OpenAI

client = OpenAI(api_key=secrets.get("OPENAI_API_KEY_1"))


def upload_file_openai(file_path, purpose="Assistant"):
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


def create_assistant_openai(file_id, model="gpt-4-1106-preview", files=None):
    e = None
    file_IDS = []
    if files is not None:
        for file in files:
            file_IDS.append(file.id)
    try:
        assistant = client.beta.assistants.create(
            name="Assistant",
            instructions="Create a conversation between the user and the assistant.",
            model=model,
            tools=[{"type": "code_interpreter"}, {"type": "retrieval"}],
            file_ids=file_IDS
        )
    except Exception as e:
        print(e)
        assistant = None
    return assistant, e


def create_thread_openai(file_id, model="gpt-4-1106-preview", files=None):
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
        runs = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
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

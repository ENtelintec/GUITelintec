# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 19/jul./2024  at 9:49 $'

import os
import tempfile

from office365.graph_client import GraphClient
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.system_object_type import FileSystemObjectType
from office365.sharepoint.sharing.links.kind import SharingLinkKind

from static.extensions import secrets
from templates.controllers.employees.employees_controller import get_emp_mail


def connect_sharepoint(url_shrpt):
    try:
        cert_credentials = {
            "tenant": secrets["TENANT_SHRPT"],
            "client_id": secrets["CLIENT_ID_SHRPT"],
            "thumbprint": secrets["CERT_THUMBPRINT_SHRPT"],
            "cert_path": secrets["FILE_CERT_PATH_SHRPT"],
            # "passphrase": "api_telintec"
        }
        ctx = ClientContext(url_shrpt).with_client_certificate(**cert_credentials)
        return ctx, 200
    except Exception as e:
        print(e)
        return None, 400


def connect_graph_client():
    client = GraphClient.with_client_secret(secrets["TENANT_GRAPH"], secrets["CLIENT_ID_GRAPH"], secrets["SECRET_GRAPH"])
    return client, 200


def get_files_site(site_url, folder_patter: str):
    ctx, code = connect_sharepoint(site_url)
    if code == 400:
        return None, 400
    doc_lib = ctx.web.default_document_library()
    items = (
        doc_lib.items.select(["FileSystemObjectType"])
        .expand(["File", "Folder"])
        .get_all()
        .execute_query()
    )
    files_paths_out = []
    for idx, item in enumerate(items):
        if item.file_system_object_type != FileSystemObjectType.Folder:
            if folder_patter in item.file.serverRelativeUrl:
                files_paths_out.append(item.file.serverRelativeUrl)
    return files_paths_out, 200


def download_files_site(site_url, file_url):
    ctx, code = connect_sharepoint(site_url)
    if code == 400:
        return None, 400
    download_path = os.path.join(tempfile.mkdtemp(), os.path.basename(file_url))
    with open(download_path, "wb") as local_file:
        file = (
            ctx.web.get_file_by_server_relative_path(file_url)
            .download(local_file)
            .execute_query()
        )
        print("[Ok] file has been downloaded into: {0}".format(download_path))
    return download_path, 200


def upload_files_site(site_url, file_path, file_path_shrpt=None):
    ctx, code = connect_sharepoint(site_url)
    if code == 400:
        return None, 400
    file_name = file_path_shrpt if file_path_shrpt is not None else os.path.basename(file_path)
    files_uploaded = []
    with open(file_path, "rb") as local_file:
        file = (
            ctx.web.default_document_library()
            .root_folder.files.add(file_name, local_file, True)
            .execute_query()
        )
        print("[Ok] file has been uploaded: {0}".format(file.serverRelativeUrl))
        files_uploaded.append(file.serverRelativeUrl)
    return files_uploaded, 200


def create_draft_mail(emp_id, from_mail, subject, body, to_recipients=None):
    graph_client, code = connect_graph_client()
    if code == 400:
        return None, 400
    flag, error, result = get_emp_mail(emp_id)
    if not flag:
        return None, 400
    to_recipients = to_recipients if to_recipients is not None else []
    mails = result[0].split(",")
    for mail in mails:
        to_recipients.append(mail)
    # Send an email
    email_subject = subject if subject is not None else f"Automatic Subject for {emp_id}"
    email_body = body
    response = (graph_client.users[from_mail].messages.add(
        email_subject,
        email_body,
        to_recipients
    ).execute_query())
    return response, 200


def share_file_nomina_emp(emp_id, url_shrpt, file_url, email_sender):
    ctx, code = connect_sharepoint(url_shrpt)
    if code == 400:
        return None, 400
    print("Creating a sharing link for a file...")
    file = ctx.web.get_file_by_server_relative_url(file_url)
    result = file.share_link(SharingLinkKind.OrganizationView).execute_query()
    print(f"Sharing link created successfully: {result.value.sharingLinkInfo}")
    # send email
    response, code = create_draft_mail(
        emp_id, email_sender, "Sharing Link",
        f"Shared link file nomina: {result.value.sharingLinkInfo}")
    return result.value.sharingLinkInfo, response, 200

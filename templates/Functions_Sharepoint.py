# -*- coding: utf-8 -*-
__author__ = 'Edisson Naula'
__date__ = '$ 19/jul./2024  at 9:49 $'

import os
import tempfile

from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.system_object_type import FileSystemObjectType

from static.extensions import secrets


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


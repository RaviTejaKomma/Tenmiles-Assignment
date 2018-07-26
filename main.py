
from __future__ import print_function

import base64
import email

import httplib2
import os

from apiclient import discovery,errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
# import MySQLdb
import time
import json
from pprint import pprint

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json

SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'

def get_connection():
    conn = MySQLdb.connect(host="localhost", user="root", passwd="raviprince57", db="tenmiles")
    return conn

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def ListMessagesMatchingQuery(service, user_id, query=''):
  """List all Messages of the user's mailbox matching the query.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    query: String used to filter messages returned.
    Eg.- 'from:user@some_domain.com' for Messages from a particular sender.

  Returns:
    List of Messages that match the criteria of the query. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate ID to get the details of a Message.
  """
  try:
    response = service.users().messages().list(userId=user_id,
                                               q=query).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id, q=query,
                                         pageToken=page_token).execute()
      messages.extend(response['messages'])

    return messages
  except errors.HttpError as error:
    print('An error occurred: %s' % error)

def ListMessagesWithLabels(service, user_id, label_ids=[]):
  """List all Messages of the user's mailbox with label_ids applied.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    label_ids: Only return Messages with these labelIds applied.

  Returns:
    List of Messages that have all required Labels applied. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate id to get the details of a Message.
  """
  try:
    response = service.users().messages().list(userId=user_id,
                                               labelIds=label_ids).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id,
                                                 labelIds=label_ids,
                                                 pageToken=page_token).execute()
      messages.extend(response['messages'])

    return messages
  except errors.HttpError as error:
    print('An error occurred: %s' % error)

def get_mpart(mail):
    maintype = mail.get_content_maintype()
    if maintype == 'multipart':
        for part in mail.get_payload():
            # This includes mail body AND text file attachments.
            if part.get_content_maintype() == 'text':
                return part.get_payload()
        # No text at all. This is also happens
        return ""
    elif maintype == 'text':
        return mail.get_payload()

def get_mail_body(mail):
    """
    There is no 'body' tag in mail, so separate function.
    :param mail: Message object
    :return: Body content
    """
    body = ""
    if mail.is_multipart():
        # This does not work.
        # for part in mail.get_payload():
        #    body += part.get_payload()
        body = get_mpart(mail)
    else:
        body = mail.get_payload()
    return body

def GetMessage(service, user_id, msg_id):
  """Get a Message with given ID.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id,format='raw').execute()
    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
    mime_msg = email.message_from_string(msg_str)
    data = {}
    data['to'] = mime_msg['To']
    data['from'] = mime_msg['From']
    data['date'] = mime_msg['Date']
    data['subject'] = mime_msg['Subject']
    data['message'] = ""
    return data
  except errors.HttpError as error:
    print('An error occurred: %s' % error)

def print_all_labels(service,user_id):
    results = service.users().labels().list(userId=user_id).execute()
    labels = results.get('labels', [])

    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(label['name'])

"""
Labels:
CATEGORY_PERSONAL
CATEGORY_SOCIAL
IMPORTANT
CATEGORY_UPDATES
CATEGORY_FORUMS
CHAT
SENT
INBOX
TRASH
CATEGORY_PROMOTIONS
DRAFT
SPAM
STARRED
UNREAD
"""

def fetch_and_store(service,user_id):
    conn = get_connection()
    cur = conn.cursor()
    messages = ListMessagesWithLabels(service, user_id, ['INBOX'])
    for msg in messages:
        result = GetMessage(service, user_id, msg['id'])
        result['date'] = " ".join(result['date'].split()[:5])
        conv = time.strptime(result['date'], "%a, %d %b %Y %H:%M:%S")
        result['date'] = time.strftime("%Y-%m-%d %H:%M:%S", conv)
        result['msg_id'] = msg['id']
        cur.execute(
            "INSERT INTO mail_data(email_from,email_to,email_subject,email_message,email_received,message_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (result['from'], result['to'], result['subject'], result['message'], result['date'],str(result['msg_id'])))
        conn.commit()
        print('logged successfully')
    conn.close()

def apply_rules():
    conn = get_connection()
    cur = conn.cursor()
    rules = json.load(open('rules.json'))
    for rule in rules["1"]["criteria"]:
        print(rule['name'],rule['value'])
        query = "SELECT message_id FROM mail_data WHERE " + "email_" + rule["name"] + " LIKE '"+rule["value"][1]+"'"
        cur.execute(query)
        print(cur.fetchall())


def main():
    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    user_id = 'me'

    ## get_labels ##
    #print_all_labels(service,user_id)
    #fetch_and_store(service,user_id)
    #apply_rules()


if __name__ == '__main__':
    main()
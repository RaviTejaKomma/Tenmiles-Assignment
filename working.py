from __future__ import print_function
from apiclient import discovery, errors
from httplib2 import Http
from oauth2client import file, client, tools
import base64
import email
import json


SCOPES = 'https://www.googleapis.com/auth/gmail.modify'

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


def read_all_labels(service, user_id):
    results = service.users().labels().list(userId = user_id).execute()
    labels = results.get('labels', [])
    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(label['name'])


def setup():
    # Setup the Gmail API

    store = file.Storage('token.json')
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets('../credentials.json', SCOPES)
        credentials = tools.run_flow(flow, store)
    service = discovery.build('gmail', 'v1', http=credentials.authorize(Http()))
    return service


if __name__ == "__main__":
    user_id = "me"
    service = setup()
    read_all_labels(service, user_id)
    messages = ListMessagesWithLabels(service, user_id, ['INBOX'])

    message = service.users().messages().get(userId=user_id, id = messages[1]['id'], format='raw').execute()
    msg_str = base64.urlsafe_b64decode(message['raw'])
    mime_msg = email.message_from_bytes(msg_str)
    data = dict()
    data['to'] = mime_msg['To']
    data['from'] = mime_msg['From']
    data['date'] = mime_msg['Date']
    data['subject'] = mime_msg['Subject']
    data['message'] = ""
    MessageBody = ""

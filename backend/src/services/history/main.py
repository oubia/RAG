# import boto3
# from botocore.exceptions import ClientError
# import boto3
# import logging
# from botocore.exceptions import ClientError

# def get_session_data(session_token):
#     dynamodb = boto3.resource('dynamodb')
#     table = dynamodb.Table('chiedimi_sessions')
#     try:
#         response = table.get_item(Key={'SessionToken': session_token})
#         item = response.get('Item')
#         if item is None:
#             table.put_item(Item={
#                 'SessionToken': session_token,
#                 'ChatHistory': []
#             })
#             print(f"Session ID {session_token} not found. Created new session with empty chat history.")
#             return []
#         else:
#             return item.get('ChatHistory', [])
#     except ClientError as e:
#         print(f"Error retrieving session data: {e}")
#         return []

# def update_session_data(session_token, chat_history):
#     dynamodb = boto3.resource('dynamodb')
#     table = dynamodb.Table('chiedimi_sessions')

#     try:
#         table.put_item(Item={
#             'SessionToken': session_token,
#             'ChatHistory': chat_history
#         })
#     except ClientError as e:
#         print(f"Error updating session data: {e}")

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from sqlalchemy import or_
from flask_session import Session
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from collections import defaultdict


import cloudinary
import cloudinary.api
import cloudinary.uploader


from config import ApplicationConfig

from models import db, User, Messages

import random
import re


cloudinary.config( 
  cloud_name = "drwk04rlc", 
  api_key = "517959355832483", 
  api_secret = "C5xq4hOXp2qPQL8ivf3K74igN8E",
  secure=True
)

def upload_picture_cloudinary(filename, type, folder):
  response = cloudinary.uploader.upload(file=filename, resource_type=type, folder=folder)
  return response['secure_url']

def delete_folder(folder_name):
  if not folder_name:
    return False

  try:
    assets = cloudinary.api.resources(
      type='upload',
      prefix=folder_name,
      max_results=500
    )
    if not assets['resources']:
      return True

    for asset in assets['resources']:
      public_id = asset['public_id']
      cloudinary.uploader.destroy(public_id)

    return True
  except Exception:
    return False


app = Flask(__name__)
app.config.from_object(ApplicationConfig)

mail = Mail(app=app)

CORS(app=app, supports_credentials=True, origins=app.config['FRONTEND_URL'], methods=['POST'], allow_headers=['Content-Type'])
server_session = Session(app)
socketio = SocketIO(app, manage_session=False, cors_allowed_origins=app.config['FRONTEND_URL'])

bcrypt = Bcrypt(app=app)

db.init_app(app=app)

migrate = Migrate(app=app, db=db)


with app.app_context():
  db.create_all()

rooms = defaultdict(dict)

def validate_email(email):
  email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
  return bool(email_pattern.match(email))

def validate_password(password):
  if not re.search(r'[A-Z]', password):
    return 'Password must contain at least one uppercase letter.'
    
  if not re.search(r'[a-z]', password):
    return 'Password must contain at least one lowercase letter.'
    
  if not re.search(r'\d', password):
    return 'Password must contain at least one digit.'
    
  if not re.search(r'[!@#$%^&*()_+{}|:"<>?]', password):
    return 'Password must contain at least one symbol.'
  
  if len(password) < 8:
    return 'Password must be at least 8 characters.'

  return False

def generate_random_code(length):
  return ''.join(random.choices('0123456789', k=length))

def send_email(receiver_email_address, head, body):
  try:
    message = Message(head, recipients=[receiver_email_address,])
    message.body = body
    mail.send(message=message)
    return True
  except Exception as e:
    return False

def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.after_request
def add_cors_headers(response):
  response.headers['Access-Control-Allow-Origin'] = app.config['FRONTEND_URL']
  response.headers['Access-Control-Allow-Credentials'] = 'true'
  response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
  response.headers['Access-Control-Allow-Methods'] = 'GET, POST'
  return response 



@app.route('/api/get_static_element/<filename>', methods=['GET'])
def get_static_element(filename):
  return send_from_directory(app.config['STATIC_FOLDER'], filename)


@app.route('/api/get_user_data', methods=['GET', 'POST'])
def get_user_data():

  if 'user_id' not in session:
    return jsonify({
      'error': 'user is not authorized'
    }), 400
  
  user = User.query.filter_by(id=session['user_id']).first()

  if not user:
    return jsonify({
      'error': 'user is not registered'
    }), 400

  return jsonify({
    'message': 'user data collected successfully',
    'user_data': {
      'id': user.id,
      'email': user.email,
      'username': user.username,
      'picture': user.profile_picture
    }
  })


@app.route('/api/fetch_users', methods=['GET'])
def fetch_users():
  user_id = session.get('user_id')
  if not user_id:
    return jsonify({
      'error': 'User is not authorized'
    }), 400
  
  users = User.query.filter(User.id != user_id).all()
  user_data = []
  for user in users:
    user_info = {
      'id': user.id,
      'username': user.username,
      'email': user.email,
      'picture': user.profile_picture
    }
    user_data.append(user_info)
  return jsonify(user_data), 200


@app.route('/api/send_code', methods=['POST'])
def send_code():
  email = request.json.get('email')

  if not email:
    return jsonify({'error': 'No email provided'}), 400
  
  is_email_registered = User.query.filter_by(email=email).first()
  if is_email_registered:
    return jsonify({'error': 'Email already registered'}), 400
  
  if not validate_email(email=email):
    return jsonify({'error': 'Invalid email format'}), 400
  
  random_code = generate_random_code(length=6)
  
  message_head = 'Welcome to Together'
  message_body = f'This is your verification code: {random_code}' 
  sent_email = send_email(receiver_email_address=email, head=message_head, body=message_body)
  
  if not sent_email:
    return jsonify({'error': 'Failed to send email'}), 400
  
  session['server_code'] = random_code
  
  return jsonify({'message': 'Mail sent successfully'}), 200


@app.route('/api/send_forgot_password_code', methods=['POST', 'GET'])
def send_forgot_password_code():
  email = request.json['email']

  if not email:
    return jsonify({
      'error': 'no email provided'
    }), 400
  
  
  if not validate_email(email=email):
    return jsonify({
      'error': 'invalid email'
    }), 400
  
  user = User.query.filter_by(email=email).first()
  if not user:
    return jsonify({
      'error': 'email is not registered'
    }), 400

  random_code = generate_random_code(length=6)
  message_head = 'Verification code | Together'
  message_body = f'This is your verification code: {random_code}' 

  sent_email = send_email(receiver_email_address=email, head=message_head, body=message_body)
  if not sent_email:
    return jsonify({
      'error': 'error while sending message'
    }), 400
  
  session['server_code'] = random_code

  return jsonify({
    'message': 'mail sent successfully'
  }), 200


@app.route('/api/check_code', methods=['POST', 'GET'])
def check_code():
  user_code = request.json['code']
  server_code = session['server_code']

  if not (user_code or server_code):
    return jsonify({
      'error': 'no code provided'
    }), 400

  if user_code == server_code:
    session.pop('server_code', None)
    return jsonify({
      'message': 'verified'
    }), 200

  return jsonify({
    'error': 'incorrect code'
  }), 400


@app.route('/api/register', methods=['POST', 'GET'])
def register():
  email = request.json['email']
  username = request.json['username']
  password = request.json['password']

  if not email:
    return jsonify({
      'error': 'No email provided'
    }), 400
  
  if not password:
    return jsonify({
      'error': 'No password provided'
    }), 400
  
  if not username:
    return jsonify({
      'error': 'No username provided'
    }), 400
  
  if validate_password(password=password):
    validate_password_error = validate_password(password=password)
    return jsonify({
      'error': validate_password_error
    }), 400    
  
  if User.query.filter_by(email=email).first():
    return jsonify({
      'error': 'This email is already registered'
    }), 400
    
  hashed_password = bcrypt.generate_password_hash(password=password)
  new_user = User(email=email.lower(), username=username, password=hashed_password, profile_picture=app.config['DEFAULT_PICTURE_URL'])

  db.session.add(new_user)
  db.session.commit()
  
  user = User.query.filter_by(email=email).first()
  session['user_id'] = user.id
  
  return jsonify({
    'message': 'User registered successfully. Please log in'
  }), 200


@app.route('/api/login', methods=['POST', 'GET'])
def login():
  email = request.json['email']
  password = request.json['password']

  if not email:
    return jsonify({
      'error': 'no email provided'
    }), 400
  
  if not password:
    return jsonify({
      'error': 'no password provided'
    }), 400
  
  user = User.query.filter_by(email=email.lower()).first()

  if not user:
    return jsonify({
      'error': 'this email isn\'t registered'
    }), 400
  
  if not bcrypt.check_password_hash(user.password, password):
    return jsonify({
      'error': 'incorrect password'
    }), 400
  
  session['user_id'] = user.id

  return jsonify({
    'message': 'user signed in successfully'
  }), 200


@app.route('/api/login_with_code', methods=['POST', 'GET'])
def login_with_code():
  server_code = session.get('server_code')
  if not server_code:
        return jsonify({
            'error': 'Verification code session expired. Please request a new code.'
        }), 400
  
  user_email = request.json['email']
  user_code = request.json['code']

  if not user_email:
    return jsonify({
      'error': 'no email provided'
    }), 400
  
  if not (server_code or user_code):
    return jsonify({
      'error': 'no code provided'
    }), 400
  
  user = User.query.filter_by(email=user_email).first()
  if not user:
    return jsonify({
      'error': 'email not registered'
    }) ,400
  
  if server_code != user_code:
    return jsonify({
      'error': 'incorrect code'
    }), 400
  
  session['user_id'] = user.id
  session.pop('server_code')
  return jsonify({
    'message': 'user signed in successfully'
  }), 200


@app.route('/api/logout', methods=['POST', 'GET'])
def logout():
  if 'user_id' not in session:
    return jsonify({
      'error': 'user is not authorized'
    }), 400
  
  session.pop('user_id', None)
  return jsonify({
    'message': 'signed out successfully'
  }), 200


@app.route('/api/search_users', methods=['POST', 'GET'])
def search_users():
    if 'user_id' not in session:
      return jsonify({
        'error': 'user is not authorized'
      }), 400

    search_word = request.json.get('search_word')
    if not search_word:
        return jsonify({'error': 'no search word provided'}), 400

    search_pattern = f'%{search_word}%'
    filter_condition = or_(User.email.ilike(search_pattern), User.username.ilike(search_pattern))
    searched_users = User.query.filter(filter_condition).filter(User.id != session['user_id']).all()

    if not searched_users:
        return jsonify({'error': 'no users found'}), 400

    users_data = [{'id': user.id, 'username': user.username, 'email': user.email} for user in searched_users]

    return jsonify(users_data), 200


@app.route('/api/update_email', methods=['POST'])
def update_email():
  user_id = session.get('user_id')
  if not user_id:
    return jsonify({
      'error': 'user is not authorized'
    }), 400
  
  new_email = request.json['newEmail']
  if not new_email:
    return jsonify({
      'error': 'no email provided'
    })
  
  user = User.query.filter_by(id=user_id).first()
  user.email = new_email
  db.session.commit()
  return jsonify({
    'message': 'email updated successfully'
  }), 200


@app.route('/api/update_username', methods=['POST'])
def update_username():
  user_id = session.get('user_id')
  if not user_id:
    return jsonify({
      'error': 'user is not authorized'
    }), 400
  
  new_username = request.json['newUsername']
  if not new_username:
    return jsonify({
      'error': 'no email provided'
    })
  
  user = User.query.filter_by(id=user_id).first()
  user.username = new_username
  db.session.commit()
  return jsonify({
    'message': 'username updated successfully'
  }), 200


@app.route('/api/upload_picture', methods=['POST'])
def upload_picture():
  if 'user_id' not in session:
    return jsonify({'error': 'User is not authorized'}), 400

  if 'newPicture' not in request.files:
    return jsonify({'error': 'No picture provided'}), 400

  file = request.files['newPicture']
  filename = secure_filename(file.filename)

  if not allowed_file(filename):
    return jsonify({'error': 'File type not allowed'}), 400

  user_id = session['user_id']
  user = User.query.filter_by(id=user_id).first()

  user_folder = f'user_{user.id}'
  type = 'image'
  folder_name = f'users_folder/{user_folder}'

  folder_deleted = delete_folder(folder_name=folder_name)
  if not folder_deleted:
    return jsonify({'error': 'Cannot manage folders'}), 400

  try:
    image_url = upload_picture_cloudinary(type=type, filename=file, folder=folder_name)
    if not image_url:
      return jsonify({'error': 'Cannot upload image to server'}), 400

    user.profile_picture = image_url
    db.session.commit()
    
    return jsonify({
      'message': 'Profile picture updated successfully',
      'profile_picture': user.profile_picture
    }), 200

  except Exception as e:
    return jsonify({'error': 'An error occurred while uploading the picture'}), 500


@app.route('/api/check_password', methods=['POST'])
def check_password():
  user_id = session.get('user_id')
  if not user_id:
    return jsonify({
      'error': 'User is not authorized'
    }), 400
  
  user_password = request.json['password']
  if not user_password:
    return jsonify({
      'error': 'No password provided'
    }), 400
  
  user = User.query.filter_by(id=user_id).first()
  
  if not bcrypt.check_password_hash(user.password, user_password):
    return jsonify({
      'error': 'Incorrect password'
    }), 400
  
  return jsonify({
    'message': 'Password is correct'
  }), 200


@app.route('/api/update_password', methods=['POST'])
def update_password():
  user_id = session.get('user_id')
  if not user_id:
    return jsonify({
      'error': 'User is not authorized'
    }), 400
  
  new_password = request.json['newPassword']
  
  if not new_password:
    return jsonify({
      'error': 'Current password or new password not provided'
    }), 400
  
  user = User.query.filter_by(id=user_id).first()
  
  if bcrypt.check_password_hash(user.password, new_password):
    return jsonify({
      'error': 'It\'s current password'
    }), 400
  
  if validate_password(password=new_password):
    validate_password_error = validate_password(password=new_password)
    return jsonify({
      'error': validate_password_error
    }), 400
  
  hashed_password = bcrypt.generate_password_hash(new_password)
  user.password = hashed_password
  
  db.session.commit()
  
  return jsonify({
    'message': 'Password updated successfully'
  }), 200


def generate_room_id(user1_id, user2_id):
  return f'{min(user1_id, user2_id)}_{max(user1_id, user2_id)}'


@socketio.on('join')
def on_join(data):
  user1_id = data['user1_id']
  user2_id = data['user2_id']

  room_id = generate_room_id(user1_id, user2_id)
  join_room(room_id)

  if room_id not in rooms:
      rooms[room_id]['members'] = []

  rooms[room_id]['members'].extend([user1_id, user2_id])
  socketio.emit('joined', { room_id: room_id, 'members': rooms[room_id]['members'] }, room=room_id)


@socketio.on('add_message')
def add_message(data):
  user1_id = data.get('user1_id')
  user2_id = data.get('user2_id')
  current_user_id = data.get('current_user_id')
  message = data.get('new_message')

  if current_user_id == user1_id:
    new_message = Messages(text=message, sender_id=user1_id, recipient_id=user2_id)
    db.session.add(new_message)
    db.session.commit()
  elif current_user_id == user2_id:
    new_message = Messages(text=message, sender_id=user2_id, recipient_id=user1_id)
    db.session.add(new_message)
    db.session.commit()

  data_to_send = {
        'room': generate_room_id(user1_id=user1_id, user2_id=user2_id),
        'message': {
            'id': new_message.id,
            'text': new_message.text,
            'date': new_message.date.strftime('%Y-%m-%d %H:%M:%S'),
            'sender_id': new_message.sender_id,
            'recipient_id': new_message.recipient_id
        }
    }


  socketio.emit('dataReceived', data_to_send)


@socketio.on('leave')
def on_leave(data):
    user1_id = data['user1_id']
    user2_id = data['user2_id']

    room_id = generate_room_id(user1_id, user2_id)
    leave_room(room_id)

    if room_id in rooms:
        del rooms[room_id]

    emit('left', {'room_id': room_id, 'members': []}, room=room_id)


@app.route('/api/fetch_messages', methods=['POST'])
def fetch_messages():
  if 'user_id' not in session:
    return jsonify({
      'error': 'user is not authorized'
    }), 400

  user1_id = request.json['user1_id']
  user2_id = request.json['user2_id']
  if not user1_id or not user2_id:
    return jsonify({
      'error': 'no receiver provided'
    }), 400

  user_id = session['user_id']

  if user1_id == user_id:
    sender_id = user1_id
    receiver_id = user2_id
  else:
    sender_id = user2_id
    receiver_id = user1_id

  sent_messages = Messages.query.filter_by(sender_id=sender_id, recipient_id=receiver_id).all()
  received_messages = Messages.query.filter_by(sender_id=receiver_id, recipient_id=sender_id).all()
  
  messages = sent_messages + received_messages
  messages.sort(key=lambda x: x.date)

  messages_data = [{
    'id': message.id,
    'text': message.text,
    'date': message.date,
    'sender_id': message.sender_id,
    'recipient_id': message.recipient_id
  } for message in messages]

  return jsonify(messages_data), 200


@app.route('/api/fetch_chats', methods=['GET'])
def fetch_chats():
  user_id = session.get('user_id')
  if not user_id:
    return jsonify({'error': 'User is not authorized'}), 400

  latest_messages_dict = {}

  all_messages = Messages.query.filter(
    or_(Messages.sender_id == user_id, Messages.recipient_id == user_id)
  ).order_by(Messages.date.desc()).all()

  for message in all_messages:
    if message.sender_id == user_id:
      other_user_id = message.recipient_id
    else:
      other_user_id = message.sender_id

    if other_user_id not in latest_messages_dict or message.date > latest_messages_dict[other_user_id].date:
      latest_messages_dict[other_user_id] = message

  chat_data = []
  for other_user_id, message in latest_messages_dict.items():
    sender = User.query.filter_by(id=message.sender_id).first()
    receiver = User.query.filter_by(id=message.recipient_id).first()

    chat_data.append({
      'sender_id': sender.id,
      'sender_name': sender.username,
      'sender_email': sender.email,
      'sender_picture': sender.profile_picture,
      'receiver_id': receiver.id,
      'receiver_name': receiver.username,
      'receiver_email': receiver.email,
      'receiver_picture': receiver.profile_picture,
      'text': message.text,
      'date': message.date.strftime('%Y-%m-%d %H:%M:%S')
    })

  return jsonify(chat_data), 200


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', allow_unsafe_werkzeug=True)
 
